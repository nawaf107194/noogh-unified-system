"""
Linux Intelligence Module — System Understanding & Interaction
Version: 1.0.0
Part of: Unified Core

Gives the Agent real understanding of the Linux environment:
1. READ   — services, logs, processes, disk, network
2. THINK  — analyze output, detect problems, understand patterns
3. ACT    — fix issues, restart services, optimize configs
4. LEARN  — record every diagnosis + fix for distillation

Unlike ProcessActuator (raw command execution), this module
UNDERSTANDS what the commands mean and acts strategically.
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("unified_core.core.linux_intelligence")


# ============================================================
#  Data Models
# ============================================================

@dataclass
class ServiceStatus:
    """Status of a systemd service."""
    name: str
    active: str          # active, inactive, failed, activating
    sub_state: str       # running, dead, exited, etc.
    pid: int = 0
    memory_mb: float = 0.0
    uptime: str = ""
    description: str = ""
    
    @property
    def is_healthy(self) -> bool:
        return self.active == "active" and self.sub_state == "running"
    
    @property
    def is_failed(self) -> bool:
        return self.active == "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "active": self.active,
            "sub_state": self.sub_state,
            "pid": self.pid,
            "memory_mb": self.memory_mb,
            "uptime": self.uptime,
            "healthy": self.is_healthy,
        }


@dataclass
class SystemDiagnosis:
    """Result of diagnosing a problem."""
    problem: str
    severity: str        # critical, warning, info
    root_cause: str
    suggested_fix: str
    auto_fixable: bool
    fix_commands: List[List[str]] = field(default_factory=list)
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "auto_fixable": self.auto_fixable,
            "confidence": self.confidence,
        }


@dataclass
class LinuxAction:
    """Record of an action taken on the system."""
    action_id: str
    action_type: str     # diagnose, fix, restart, query
    description: str
    commands_run: List[str]
    output: str
    success: bool
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "type": self.action_type,
            "description": self.description,
            "success": self.success,
            "timestamp": self.timestamp,
        }


# ============================================================
#  Safe Command Execution
# ============================================================

# Commands the agent can run freely (read-only)
SAFE_READ_COMMANDS = {
    "systemctl": ["status", "is-active", "is-enabled", "list-units", "show"],
    "journalctl": ["--no-pager", "-n", "--since", "--unit", "-u", "--output"],
    "ps": ["aux", "-ef", "--sort", "-eo"],
    "df": ["-h", "--output"],
    "free": ["-h", "-m", "-g"],
    "uptime": [],
    "who": [],
    "uname": ["-a", "-r"],
    "ip": ["addr", "route", "link"],
    "ss": ["-tlnp", "-ulnp"],
    "lsof": ["-i", "-P"],
    "cat": [],  # Will be path-restricted
    "head": [],
    "tail": ["-n", "-f"],
    "grep": [],
    "find": [],
    "wc": ["-l"],
    "du": ["-sh", "-h"],
    "nvidia-smi": ["--query-gpu", "--format"],
    "top": ["-bn1"],
    "lscpu": [],
    "lsblk": [],
    "mount": [],
}

# Commands that modify the system (need approval or auto-fix mode)
WRITE_COMMANDS = {
    "systemctl": ["restart", "start", "stop", "enable", "disable", "reload"],
    "apt": ["update", "install", "upgrade"],
    "pip3": ["install", "upgrade"],
}

# Paths safe to read logs from
SAFE_LOG_PATHS = [
    "/var/log/syslog",
    "/var/log/auth.log",
    "/var/log/kern.log",
    "/var/log/dmesg",
    "/home/noogh/projects/noogh_unified_system/src/data/",
    "/home/noogh/projects/noogh_unified_system/src/logs/",
]

# Our services to monitor
NOOGH_SERVICES = [
    "noogh-agent",
    "noogh-gateway", 
    "noogh-neural",
    "noogh-console",
    "noogh-autonomic",
]


class LinuxIntelligence:
    """
    Intelligent Linux system interaction layer.
    
    READ  → Understand system state
    THINK → Diagnose problems  
    ACT   → Fix issues
    LEARN → Record for distillation
    """
    
    def __init__(self, auto_fix: bool = False):
        self.auto_fix = auto_fix  # If True, apply fixes automatically
        self._actions: List[LinuxAction] = []
        self._diagnoses: List[SystemDiagnosis] = []
        self._action_count = 0
        self._fix_count = 0
        self._diagnosis_count = 0
        
        logger.info(f"🐧 LinuxIntelligence initialized (auto_fix={auto_fix})")
    
    # ========================================
    #  READ — System State
    # ========================================
    
    async def _run_cmd(self, cmd: List[str], timeout: float = 10.0) -> Tuple[str, str, int]:
        """Run a command safely. Returns (stdout, stderr, exit_code)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return (
                stdout.decode('utf-8', errors='replace').strip(),
                stderr.decode('utf-8', errors='replace').strip(),
                proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Command timed out: {' '.join(cmd)}")
            return "", "TIMEOUT", -1
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)}: {e}")
            return "", str(e), -1
    
    async def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get detailed status of a systemd service."""
        stdout, _, _ = await self._run_cmd([
            "systemctl", "show", service_name,
            "--property=ActiveState,SubState,MainPID,MemoryCurrent,Description"
        ])
        
        props = {}
        for line in stdout.split('\n'):
            if '=' in line:
                key, val = line.split('=', 1)
                props[key.strip()] = val.strip()
        
        memory_bytes = int(props.get("MemoryCurrent", "0") or "0")
        
        return ServiceStatus(
            name=service_name,
            active=props.get("ActiveState", "unknown"),
            sub_state=props.get("SubState", "unknown"),
            pid=int(props.get("MainPID", "0") or "0"),
            memory_mb=round(memory_bytes / (1024 * 1024), 1) if memory_bytes > 0 else 0,
            description=props.get("Description", ""),
        )
    
    async def get_all_services_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all NOOGH services."""
        results = {}
        for svc in NOOGH_SERVICES:
            results[svc] = await self.get_service_status(svc)
        return results
    
    async def get_service_logs(self, service_name: str, lines: int = 30, 
                                since: str = None) -> str:
        """Get recent logs for a service."""
        cmd = ["journalctl", "-u", service_name, "--no-pager", 
               "-n", str(min(lines, 100)), "--output=short-iso"]
        if since:
            cmd.extend(["--since", since])
        
        stdout, _, _ = await self._run_cmd(cmd, timeout=5.0)
        return stdout
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        health = {}
        
        # CPU & Memory
        stdout, _, _ = await self._run_cmd(["free", "-m"])
        if stdout:
            lines = stdout.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 7:
                    health["ram_total_mb"] = int(parts[1])
                    health["ram_used_mb"] = int(parts[2])
                    health["ram_available_mb"] = int(parts[6])
                    health["ram_percent"] = round(int(parts[2]) / int(parts[1]) * 100, 1)
        
        # Disk
        stdout, _, _ = await self._run_cmd(["df", "-h", "/"])
        if stdout:
            lines = stdout.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    health["disk_total"] = parts[1]
                    health["disk_used"] = parts[2]
                    health["disk_available"] = parts[3]
                    health["disk_percent"] = parts[4]
        
        # Uptime & Load
        stdout, _, _ = await self._run_cmd(["uptime"])
        if stdout:
            health["uptime"] = stdout.strip()
            load_match = re.search(r'load average:\s*([\d.]+)', stdout)
            if load_match:
                health["load_1min"] = float(load_match.group(1))
        
        # GPU
        stdout, _, rc = await self._run_cmd([
            "nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits"
        ])
        if rc == 0 and stdout:
            parts = stdout.strip().split(', ')
            if len(parts) >= 4:
                health["gpu_temp_c"] = int(parts[0])
                health["gpu_util_percent"] = int(parts[1])
                health["gpu_mem_used_mb"] = int(parts[2])
                health["gpu_mem_total_mb"] = int(parts[3])
        
        # Network: listening ports
        stdout, _, _ = await self._run_cmd(["ss", "-tlnp"])
        if stdout:
            listening_ports = []
            for line in stdout.split('\n')[1:]:
                port_match = re.search(r':(\d+)\s', line)
                if port_match:
                    listening_ports.append(int(port_match.group(1)))
            health["listening_ports"] = sorted(set(listening_ports))
        
        # Services
        services = await self.get_all_services_status()
        health["services"] = {
            name: svc.to_dict() for name, svc in services.items()
        }
        health["services_healthy"] = sum(1 for s in services.values() if s.is_healthy)
        health["services_failed"] = sum(1 for s in services.values() if s.is_failed)
        
        return health
    
    async def get_top_processes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get top processes by CPU/memory usage."""
        stdout, _, _ = await self._run_cmd([
            "ps", "-eo", "pid,user,%cpu,%mem,rss,comm", "--sort=-%cpu"
        ])
        
        processes = []
        if stdout:
            lines = stdout.split('\n')[1:]  # Skip header
            for line in lines[:count]:
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    processes.append({
                        "pid": int(parts[0]),
                        "user": parts[1],
                        "cpu_percent": float(parts[2]),
                        "mem_percent": float(parts[3]),
                        "rss_kb": int(parts[4]),
                        "command": parts[5],
                    })
        
        return processes
    
    async def search_logs(self, pattern: str, service: str = None, 
                           lines: int = 20) -> str:
        """Search system logs for a pattern."""
        if service:
            cmd = ["journalctl", "-u", service, "--no-pager", 
                   "-n", "500", "--output=short-iso"]
        else:
            cmd = ["journalctl", "--no-pager", "-n", "500", "--output=short-iso"]
        
        stdout, _, _ = await self._run_cmd(cmd, timeout=5.0)
        
        if stdout and pattern:
            # Filter lines matching pattern
            matched = [l for l in stdout.split('\n') if pattern.lower() in l.lower()]
            return '\n'.join(matched[-lines:])
        
        return stdout
    
    # ========================================
    #  THINK — Diagnosis
    # ========================================
    
    async def diagnose_service(self, service_name: str) -> Optional[SystemDiagnosis]:
        """Diagnose why a service is failing."""
        status = await self.get_service_status(service_name)
        
        if status.is_healthy:
            return None  # No problem to diagnose
        
        # Get recent logs for clues
        logs = await self.get_service_logs(service_name, lines=50)
        
        diagnosis = SystemDiagnosis(
            problem=f"Service {service_name} is {status.active}/{status.sub_state}",
            severity="critical" if status.is_failed else "warning",
            root_cause="",
            suggested_fix="",
            auto_fixable=False,
        )
        
        # Pattern matching on logs
        if "ModuleNotFoundError" in logs or "ImportError" in logs:
            module_match = re.search(r"(?:ModuleNotFoundError|ImportError).*?'(\S+)'", logs)
            module_name = module_match.group(1) if module_match else "unknown"
            diagnosis.root_cause = f"Missing Python module: {module_name}"
            diagnosis.suggested_fix = f"pip3 install {module_name}"
            diagnosis.fix_commands = [["pip3", "install", module_name]]
            diagnosis.auto_fixable = True
            diagnosis.confidence = 0.9
        
        elif "PermissionError" in logs or "Permission denied" in logs:
            diagnosis.root_cause = "Permission denied — service lacks file access"
            diagnosis.suggested_fix = "Check file ownership and systemd user"
            diagnosis.confidence = 0.7
        
        elif "Address already in use" in logs:
            port_match = re.search(r"port\s+(\d+)|:(\d+)", logs)
            port = port_match.group(1) or port_match.group(2) if port_match else "?"
            diagnosis.root_cause = f"Port {port} already in use by another process"
            diagnosis.suggested_fix = f"Kill process using port {port} or change port"
            diagnosis.confidence = 0.85
        
        elif "ConnectionRefusedError" in logs or "Connection refused" in logs:
            diagnosis.root_cause = "Cannot connect to a dependency (Redis, DB, Neural Engine)"
            diagnosis.suggested_fix = "Check if dependent services are running"
            diagnosis.confidence = 0.7
        
        elif "OOM" in logs or "Killed" in logs or "MemoryError" in logs:
            diagnosis.root_cause = "Out of memory — process was killed by OOM killer"
            diagnosis.suggested_fix = "Reduce memory usage or add swap"
            diagnosis.confidence = 0.85
        
        elif "CUDA" in logs or "GPU" in logs:
            diagnosis.root_cause = "GPU/CUDA error — driver or memory issue"
            diagnosis.suggested_fix = "Check nvidia-smi, restart GPU processes"
            diagnosis.confidence = 0.6
        
        elif "SyntaxError" in logs or "NameError" in logs:
            error_match = re.search(r"(?:SyntaxError|NameError).*", logs)
            diagnosis.root_cause = f"Code error: {error_match.group(0)[:100] if error_match else 'Python error'}"
            diagnosis.suggested_fix = "Fix the code error and restart service"
            diagnosis.confidence = 0.9
        
        elif status.active == "activating":
            diagnosis.root_cause = "Service stuck in activating state — slow startup or dependency issue"
            diagnosis.suggested_fix = f"Restart service: systemctl restart {service_name}"
            diagnosis.fix_commands = [["systemctl", "restart", service_name]]
            diagnosis.auto_fixable = True
            diagnosis.confidence = 0.7
        
        else:
            # Unknown — ask the Brain
            diagnosis.root_cause = "Unknown failure — needs deeper analysis"
            diagnosis.suggested_fix = "Check logs manually or ask Brain for analysis"
            diagnosis.confidence = 0.3
        
        self._diagnoses.append(diagnosis)
        self._diagnosis_count += 1
        
        logger.info(
            f"🔍 Diagnosis: {diagnosis.problem} → {diagnosis.root_cause} "
            f"(confidence={diagnosis.confidence:.0%})"
        )
        
        return diagnosis
    
    async def diagnose_all_services(self) -> List[SystemDiagnosis]:
        """Diagnose all NOOGH services."""
        diagnoses = []
        for svc in NOOGH_SERVICES:
            diagnosis = await self.diagnose_service(svc)
            if diagnosis:
                diagnoses.append(diagnosis)
        return diagnoses
    
    async def ask_brain_diagnosis(self, problem: str, logs: str) -> Optional[SystemDiagnosis]:
        """Ask the Brain (32B) to diagnose a complex problem."""
        try:
            from unified_core.neural_bridge import NeuralEngineClient
            client = NeuralEngineClient()
            
            prompt = f"""Analyze this Linux system problem and provide a diagnosis.

PROBLEM: {problem}

RECENT LOGS:
```
{logs[-2000:]}
```

Provide your diagnosis in this JSON format:
```json
{{
    "root_cause": "What caused the problem",
    "severity": "critical/warning/info",
    "fix": "How to fix it",
    "commands": ["command1", "command2"],
    "confidence": 0.8
}}
```"""
            
            messages = [
                {"role": "system", "content": "You are a Linux systems expert. Diagnose problems precisely and suggest concrete fixes."},
                {"role": "user", "content": prompt}
            ]
            
            result = await client.complete(messages, max_tokens=1024)
            
            if result.get("success") and result.get("content"):
                response = result["content"]
                
                # Record for distillation
                try:
                    from unified_core.evolution.distillation_collector import get_distillation_collector
                    collector = get_distillation_collector()
                    collector.record(
                        category="linux_diagnosis",
                        system_prompt="You are a Linux systems expert.",
                        user_prompt=prompt,
                        teacher_response=response,
                        quality_score=0.7,
                        metadata={"problem": problem}
                    )
                except Exception:
                    pass
                
                # Parse JSON from response
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    if json_end > json_start:
                        try:
                            data = json.loads(response[json_start:json_end])
                            return SystemDiagnosis(
                                problem=problem,
                                severity=data.get("severity", "warning"),
                                root_cause=data.get("root_cause", "Unknown"),
                                suggested_fix=data.get("fix", ""),
                                auto_fixable=bool(data.get("commands")),
                                fix_commands=[[c] if isinstance(c, str) else c for c in data.get("commands", [])],
                                confidence=float(data.get("confidence", 0.5)),
                            )
                        except json.JSONDecodeError:
                            pass
                
                # Fallback: use raw response
                return SystemDiagnosis(
                    problem=problem,
                    severity="warning",
                    root_cause=response[:200],
                    suggested_fix=response[200:400] if len(response) > 200 else "",
                    auto_fixable=False,
                    confidence=0.4,
                )
        
        except Exception as e:
            logger.error(f"Brain diagnosis failed: {e}")
            return None
    
    # ========================================
    #  ACT — Fix Problems
    # ========================================
    
    async def restart_service(self, service_name: str) -> LinuxAction:
        """Restart a systemd service."""
        action = LinuxAction(
            action_id=f"linux_{int(time.time())}",
            action_type="restart",
            description=f"Restart {service_name}",
            commands_run=[f"systemctl restart {service_name}"],
            output="",
            success=False,
        )
        
        stdout, stderr, rc = await self._run_cmd(
            ["systemctl", "restart", service_name], timeout=15.0
        )
        
        # Check if it actually started
        await asyncio.sleep(2)
        status = await self.get_service_status(service_name)
        
        action.output = stdout or stderr
        action.success = status.is_healthy
        
        self._actions.append(action)
        self._action_count += 1
        if action.success:
            self._fix_count += 1
        
        logger.info(
            f"{'✅' if action.success else '❌'} "
            f"Restart {service_name}: {status.active}/{status.sub_state}"
        )
        
        return action
    
    async def apply_fix(self, diagnosis: SystemDiagnosis) -> LinuxAction:
        """Apply a fix from a diagnosis."""
        action = LinuxAction(
            action_id=f"fix_{int(time.time())}",
            action_type="fix",
            description=f"Fix: {diagnosis.suggested_fix}",
            commands_run=[],
            output="",
            success=False,
        )
        
        if not diagnosis.auto_fixable or not diagnosis.fix_commands:
            action.output = "Not auto-fixable"
            self._actions.append(action)
            return action
        
        outputs = []
        all_success = True
        
        for cmd in diagnosis.fix_commands:
            action.commands_run.append(' '.join(cmd))
            stdout, stderr, rc = await self._run_cmd(cmd, timeout=30.0)
            outputs.append(f"$ {' '.join(cmd)}\n{stdout}\n{stderr}".strip())
            if rc != 0:
                all_success = False
                break
        
        action.output = '\n---\n'.join(outputs)
        action.success = all_success
        
        self._actions.append(action)
        self._action_count += 1
        if action.success:
            self._fix_count += 1
        
        logger.info(
            f"{'✅' if action.success else '❌'} "
            f"Fix applied: {diagnosis.suggested_fix}"
        )
        
        return action
    
    # ========================================
    #  INTEGRATED — Full diagnostic cycle
    # ========================================
    
    async def run_health_check(self) -> Dict[str, Any]:
        """
        Full health check cycle:
        1. Check all services
        2. Diagnose any failures
        3. Optionally auto-fix
        
        Called by Agent Daemon periodically.
        """
        result = {
            "timestamp": time.time(),
            "healthy": True,
            "services": {},
            "diagnoses": [],
            "actions_taken": [],
        }
        
        # 1. Check services
        services = await self.get_all_services_status()
        for name, status in services.items():
            result["services"][name] = status.to_dict()
            
            if not status.is_healthy:
                result["healthy"] = False
                
                # 2. Diagnose
                diagnosis = await self.diagnose_service(name)
                if diagnosis:
                    result["diagnoses"].append(diagnosis.to_dict())
                    
                    # 3. Auto-fix if enabled
                    if self.auto_fix and diagnosis.auto_fixable and diagnosis.confidence >= 0.7:
                        logger.info(f"🔧 Auto-fixing: {diagnosis.suggested_fix}")
                        action = await self.apply_fix(diagnosis)
                        result["actions_taken"].append(action.to_dict())
        
        # Summary
        healthy_count = sum(1 for s in services.values() if s.is_healthy)
        total = len(services)
        
        if result["healthy"]:
            logger.info(f"🐧 Health check: {healthy_count}/{total} services healthy ✅")
        else:
            logger.warning(
                f"🐧 Health check: {healthy_count}/{total} services healthy, "
                f"{len(result['diagnoses'])} issues found"
            )
        
        return result
    
    async def investigate(self, question: str) -> Dict[str, Any]:
        """
        Answer a question about the system using commands.
        
        Examples:
        - "What's using port 8001?"
        - "Why is noogh-agent failing?"
        - "How much disk space is left?"
        - "Show GPU usage"
        """
        investigation = {
            "question": question,
            "findings": [],
            "answer": "",
        }
        
        q = question.lower()
        
        if "port" in q:
            port_match = re.search(r'(\d{4,5})', question)
            if port_match:
                port = port_match.group(1)
                stdout, _, _ = await self._run_cmd(["ss", "-tlnp"])
                lines = [l for l in stdout.split('\n') if port in l]
                investigation["findings"] = lines
                investigation["answer"] = f"Port {port}: {lines[0] if lines else 'not in use'}"
        
        elif "disk" in q or "space" in q:
            stdout, _, _ = await self._run_cmd(["df", "-h"])
            investigation["findings"] = stdout.split('\n')
            investigation["answer"] = stdout
        
        elif "gpu" in q or "nvidia" in q:
            stdout, _, _ = await self._run_cmd(["nvidia-smi"])
            investigation["findings"] = [stdout]
            investigation["answer"] = stdout
        
        elif "memory" in q or "ram" in q:
            stdout, _, _ = await self._run_cmd(["free", "-h"])
            investigation["findings"] = [stdout]
            investigation["answer"] = stdout
        
        elif "fail" in q or "error" in q or "why" in q:
            # Try to find the service name
            for svc in NOOGH_SERVICES:
                if svc.replace("noogh-", "") in q:
                    diagnosis = await self.diagnose_service(svc)
                    if diagnosis:
                        investigation["findings"] = [diagnosis.to_dict()]
                        investigation["answer"] = f"{diagnosis.root_cause} → {diagnosis.suggested_fix}"
                    break
        
        elif "process" in q or "top" in q:
            processes = await self.get_top_processes(5)
            investigation["findings"] = processes
            investigation["answer"] = '\n'.join(
                f"{p['command']}: CPU={p['cpu_percent']}% MEM={p['mem_percent']}%"
                for p in processes
            )
        
        elif "service" in q:
            services = await self.get_all_services_status()
            investigation["findings"] = [s.to_dict() for s in services.values()]
            investigation["answer"] = '\n'.join(
                f"{s.name}: {'✅' if s.is_healthy else '❌'} {s.active}/{s.sub_state}"
                for s in services.values()
            )
        
        else:
            # General query — try Brain
            health = await self.get_system_health()
            investigation["findings"] = [health]
            investigation["answer"] = json.dumps(health, indent=2, default=str)
        
        return investigation
    
    # ========================================
    #  Stats
    # ========================================
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_actions": self._action_count,
            "total_fixes": self._fix_count,
            "total_diagnoses": self._diagnosis_count,
            "auto_fix_enabled": self.auto_fix,
            "recent_actions": [a.to_dict() for a in self._actions[-5:]],
            "recent_diagnoses": [d.to_dict() for d in self._diagnoses[-5:]],
        }


# Singleton
_linux_intel: Optional[LinuxIntelligence] = None

def get_linux_intelligence(auto_fix: bool = False) -> LinuxIntelligence:
    """Get or create global LinuxIntelligence instance."""
    global _linux_intel
    if _linux_intel is None:
        _linux_intel = LinuxIntelligence(auto_fix=auto_fix)
    return _linux_intel
