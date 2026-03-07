"""
SystemAdmin Adapter - Connects SYSTEM_ADMIN specialized system to Core
Follows strict Policy + ConfidenceGate pattern
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemAdminAdapter:
    """
    Adapter for SystemAdmin specialized system
    Provides OBSERVE → ASSESS → PROPOSE pattern
    """
    
    def __init__(self):
        """Initialize adapter with SystemMonitor"""
        from neural_engine.specialized_systems.system_monitor import SystemMonitor
        
        self.monitor = SystemMonitor()
        self.observation_history = []
        self.max_history = 100
        
        logger.info("✅ SystemAdminAdapter initialized")
    
    # ========== OBSERVE LAYER ==========
    
    def observe(self) -> Dict[str, Any]:
        """
        Observe current system state (read-only, safe)
        
        Returns:
            Complete system snapshot
        """
        try:
            observation = {
                "timestamp": datetime.now().isoformat(),
                "health": self.monitor.get_health_status(),
                "cpu": self.monitor.get_cpu_info(),
                "memory": self.monitor.get_memory_info(),
                "disk": self.monitor.get_disk_info(),
                "gpu": self.monitor.get_gpu_info(),
                "network": self.monitor.get_network_info(),
            }
            
            # Store in history
            self.observation_history.append(observation)
            if len(self.observation_history) > self.max_history:
                self.observation_history.pop(0)
            
            logger.debug(f"📊 System observed: health={observation['health']['status']}")
            return observation
            
        except Exception as e:
            logger.error(f"❌ Observation failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get formatted data for dashboard"""
        return self.monitor.get_dashboard_data()
    
    # ========== ASSESS LAYER ==========
    
    def assess(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess system state and identify risks/issues
        
        Args:
            state: System observation from observe()
            
        Returns:
            Assessment with risks and priorities
        """
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "risks": [],
            "warnings": [],
            "info": [],
            "priority": "normal"
        }
        
        # Check for errors
        if "error" in state:
            assessment["risks"].append({
                "type": "observation_failure",
                "severity": "high",
                "message": state["error"]
            })
            assessment["priority"] = "high"
            return assessment
        
        # CPU assessment
        cpu_usage = state.get("cpu", {}).get("cpu_usage_percent", 0)
        if cpu_usage > 90:
            assessment["risks"].append({
                "type": "cpu_critical",
                "severity": "critical",
                "value": cpu_usage,
                "message": f"CPU usage critical: {cpu_usage}%"
            })
            assessment["priority"] = "critical"
        elif cpu_usage > 75:
            assessment["warnings"].append({
                "type": "cpu_high",
                "value": cpu_usage,
                "message": f"CPU usage high: {cpu_usage}%"
            })
            if assessment["priority"] == "normal":
                assessment["priority"] = "medium"
        
        # Memory assessment
        mem_percent = state.get("memory", {}).get("percent", 0)
        if mem_percent > 90:
            assessment["risks"].append({
                "type": "memory_critical",
                "severity": "critical",
                "value": mem_percent,
                "message": f"Memory usage critical: {mem_percent}%"
            })
            assessment["priority"] = "critical"
        elif mem_percent > 80:
            assessment["warnings"].append({
                "type": "memory_high",
                "value": mem_percent,
                "message": f"Memory usage high: {mem_percent}%"
            })
        
        # Disk assessment
        for partition in state.get("disk", {}).get("partitions", []):
            percent = partition.get("percent", 0)
            mountpoint = partition.get("mountpoint", "unknown")
            
            if percent > 95:
                assessment["risks"].append({
                    "type": "disk_critical",
                    "severity": "critical",
                    "mountpoint": mountpoint,
                    "value": percent,
                    "message": f"Disk {mountpoint} critical: {percent}%"
                })
                assessment["priority"] = "critical"
            elif percent > 85:
                assessment["warnings"].append({
                    "type": "disk_high",
                    "mountpoint": mountpoint,
                    "value": percent,
                    "message": f"Disk {mountpoint} high: {percent}%"
                })
        
        # GPU assessment (if available)
        gpu = state.get("gpu", {})
        if gpu.get("available"):
            mem_total = gpu.get("memory_total", 1)
            mem_allocated = gpu.get("memory_allocated", 0)
            gpu_percent = (mem_allocated / mem_total * 100) if mem_total > 0 else 0
            
            if gpu_percent > 95:
                assessment["warnings"].append({
                    "type": "gpu_memory_high",
                    "value": gpu_percent,
                    "message": f"GPU memory high: {gpu_percent:.1f}%"
                })
        
        # Health status
        health_status = state.get("health", {}).get("status", "unknown")
        if health_status == "critical":
            assessment["priority"] = "critical"
        elif health_status == "warning" and assessment["priority"] == "normal":
            assessment["priority"] = "medium"
        
        logger.info(f"🔍 Assessment: priority={assessment['priority']}, risks={len(assessment['risks'])}, warnings={len(assessment['warnings'])}")
        return assessment
    
    # ========== PROPOSE LAYER ==========
    
    def propose_actions(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Propose remediation actions based on assessment
        
        Args:
            assessment: Assessment from assess()
            
        Returns:
            List of proposed actions with confidence scores
        """
        proposals = []
        
        # Handle critical risks
        for risk in assessment.get("risks", []):
            risk_type = risk.get("type")
            
            if risk_type == "cpu_critical":
                proposals.append({
                    "action": "log_warning",
                    "target": "system_health",
                    "params": {
                        "message": risk["message"],
                        "severity": "critical"
                    },
                    "confidence": 1.0,
                    "auto_execute": True  # Safe action
                })
            
            elif risk_type == "memory_critical":
                proposals.append({
                    "action": "log_warning",
                    "target": "system_health",
                    "params": {
                        "message": risk["message"],
                        "severity": "critical"
                    },
                    "confidence": 1.0,
                    "auto_execute": True
                })
                # Could propose memory cleanup, but requires policy approval
                proposals.append({
                    "action": "suggest_restart",
                    "target": "neural_service",
                    "params": {
                        "reason": "Memory pressure",
                        "estimated_impact": "2-3 minutes downtime"
                    },
                    "confidence": 0.7,
                    "auto_execute": False  # Requires approval
                })
            
            elif risk_type == "disk_critical":
                proposals.append({
                    "action": "log_warning",
                    "target": "system_health",
                    "params": {
                        "message": risk["message"],
                        "severity": "critical"
                    },
                    "confidence": 1.0,
                    "auto_execute": True
                })
                proposals.append({
                    "action": "suggest_cleanup",
                    "target": "disk",
                    "params": {
                        "mountpoint": risk.get("mountpoint"),
                        "targets": ["logs", "temp_files", "cache"]
                    },
                    "confidence": 0.8,
                    "auto_execute": False  # Requires approval
                })
        
        # Handle warnings
        for warning in assessment.get("warnings", []):
            warning_type = warning.get("type")
            
            if warning_type in ["cpu_high", "memory_high", "disk_high", "gpu_memory_high"]:
                proposals.append({
                    "action": "log_info",
                    "target": "system_health",
                    "params": {
                        "message": warning["message"],
                        "severity": "warning"
                    },
                    "confidence": 1.0,
                    "auto_execute": True
                })
        
        logger.info(f"💡 Proposed {len(proposals)} actions (auto_execute={sum(1 for p in proposals if p['auto_execute'])})")
        return proposals
    
    # ========== TREND ANALYSIS ==========
    
    def analyze_trends(self, window_minutes: int = 10) -> Dict[str, Any]:
        """
        Analyze trends from observation history
        
        Args:
            window_minutes: Time window to analyze
            
        Returns:
            Trend analysis
        """
        if len(self.observation_history) < 2:
            return {"status": "insufficient_data"}
        
        # Get recent observations
        recent = self.observation_history[-min(len(self.observation_history), window_minutes):]
        
        # Analyze CPU trend
        cpu_values = [obs.get("cpu", {}).get("cpu_usage_percent", 0) for obs in recent]
        cpu_trend = "stable"
        if len(cpu_values) >= 3:
            if cpu_values[-1] > cpu_values[-2] > cpu_values[-3]:
                cpu_trend = "increasing"
            elif cpu_values[-1] < cpu_values[-2] < cpu_values[-3]:
                cpu_trend = "decreasing"
        
        # Analyze memory trend
        mem_values = [obs.get("memory", {}).get("percent", 0) for obs in recent]
        mem_trend = "stable"
        if len(mem_values) >= 3:
            if mem_values[-1] > mem_values[-2] > mem_values[-3]:
                mem_trend = "increasing"
            elif mem_values[-1] < mem_values[-2] < mem_values[-3]:
                mem_trend = "decreasing"
        
        return {
            "window_size": len(recent),
            "cpu_trend": cpu_trend,
            "cpu_current": cpu_values[-1] if cpu_values else 0,
            "memory_trend": mem_trend,
            "memory_current": mem_values[-1] if mem_values else 0,
        }
    
    # ========== UTILITY ==========
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "adapter": "SystemAdmin",
            "status": "operational",
            "observations_stored": len(self.observation_history),
            "max_history": self.max_history
        }


# Singleton instance
_adapter_instance: Optional[SystemAdminAdapter] = None


def get_system_admin_adapter() -> SystemAdminAdapter:
    """Get singleton adapter instance"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = SystemAdminAdapter()
    return _adapter_instance
