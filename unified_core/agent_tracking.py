"""
Noogh Agent Tracking System - نظام تتبع وكيل Noogh

Provides comprehensive monitoring and tracking capabilities for the autonomous agent.
يوفر قدرات مراقبة وتتبع شاملة للوكيل المستقل.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
import logging
import time
import psutil
import os
from datetime import datetime

logger = logging.getLogger("unified_core.agent_tracking")

router = APIRouter(prefix="/agent", tags=["Agent Tracking"])


class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    status: str
    pid: Optional[int] = None
    uptime_seconds: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    memory_percent: Optional[float] = None
    num_threads: Optional[int] = None
    last_cycle_id: Optional[str] = None
    last_activity: Optional[str] = None
    last_decision_time: Optional[float] = None
    total_decisions: Optional[int] = None
    arabic_status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DecisionMetrics(BaseModel):
    """Decision cycle metrics"""
    cycle_id: str
    started_at: float
    duration_ms: float
    observations_collected: int
    candidates_generated: int
    candidates_blocked: int
    decision_made: bool
    action_executed: bool


class AgentHealth(BaseModel):
    """Agent health status"""
    overall_health: str
    components: Dict[str, str]
    resource_usage: Dict[str, float]
    warnings: List[str] = []
    arabic_health: Optional[str] = None


# ========================================
# Helper Functions
# ========================================

async def _get_agent_status_data() -> AgentStatusResponse:
    """Internal function to get agent status data"""
    try:
        # First, try to find running agent daemon process
        agent_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'agent_daemon' in ' '.join(cmdline):
                    agent_pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if agent_pid:
            # Agent is running - get its info
            try:
                process = psutil.Process(agent_pid)
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = process.memory_percent()
                num_threads = process.num_threads()
                
                # Try to get additional info from daemon
                status_info = {}
                try:
                    from unified_core.agent_daemon import get_daemon
                    daemon = get_daemon()
                    status_info = daemon.get_status()
                except Exception:
                    # Daemon instance not accessible, use process info only
                    status_info = {
                        "state": "running",
                        "uptime_seconds": time.time() - process.create_time()
                    }
            
                # Translate status to Arabic
                status_translations = {
                    "initializing": "جاري التهيئة",
                    "running": "يعمل",
                    "paused": "متوقف مؤقتاً",
                    "shutting_down": "جاري الإيقاف",
                    "stopped": "متوقف",
                    "daemon_not_running": "الوكيل غير قيد التشغيل"
                }
                
                arabic_status = status_translations.get(status_info.get("state", "running"), "يعمل")
                
                return AgentStatusResponse(
                    status=status_info.get("state", "running"),
                    pid=agent_pid,
                    uptime_seconds=status_info.get("uptime_seconds"),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    num_threads=num_threads,
                    last_cycle_id=status_info.get("last_cycle_id"),
                    last_activity=status_info.get("last_activity"),
                    last_decision_time=status_info.get("last_decision_time"),
                    total_decisions=status_info.get("total_decisions"),
                    arabic_status=arabic_status,
                    details=status_info
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                return AgentStatusResponse(
                    status="error",
                    arabic_status="خطأ في الوصول",
                    details={"error": str(e)}
                )
        else:
            # No agent daemon process found
            return AgentStatusResponse(
                status="daemon_not_running",
                arabic_status="الوكيل غير قيد التشغيل",
                details={"message": "No agent_daemon process found"}
            )
            
    except Exception as e:
        logger.error(f"Agent status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_agent_health_data() -> AgentHealth:
    """Internal function to get agent health data"""
    try:
        health_status = {
            "overall_health": "healthy",
            "arabic_health": "صحي",
            "components": {},
            "resource_usage": {},
            "warnings": []
        }
        
        # Find running agent daemon process
        agent_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'agent_daemon' in ' '.join(cmdline):
                    agent_pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if agent_pid:
            # Agent is running
            health_status["components"]["daemon"] = "running"
            
            try:
                process = psutil.Process(agent_pid)
                health_status["resource_usage"]["cpu_percent"] = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                health_status["resource_usage"]["memory_mb"] = memory_info.rss / 1024 / 1024
                health_status["resource_usage"]["threads"] = process.num_threads()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                health_status["components"]["process"] = "not_accessible"
                health_status["warnings"].append("Cannot access process metrics")
            
        else:
            # Daemon not running
            health_status["overall_health"] = "stopped"
            health_status["arabic_health"] = "متوقف"
            health_status["components"]["daemon"] = "not_running"
        
        # Check system resources
        system_cpu = psutil.cpu_percent(interval=0.1)
        system_memory = psutil.virtual_memory()
        health_status["resource_usage"]["system_cpu"] = system_cpu
        health_status["resource_usage"]["system_memory_percent"] = system_memory.percent
        
        if system_cpu > 90 or system_memory.percent > 90:
            health_status["overall_health"] = "critical"
            health_status["arabic_health"] = "حرج"
            health_status["warnings"].append("System resources critical")
        
        return AgentHealth(**health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_agent_metrics_data() -> Dict[str, Any]:
    """Internal function to get agent metrics data"""
    try:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": time.time(),
            "arabic_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": vm.percent,
                "memory_used_gb": vm.used / (1024**3),
                "memory_total_gb": vm.total / (1024**3),
                "disk_percent": disk.percent
            },
            "agent": {},
            "performance": {}
        }
        
        # Find running agent daemon process
        agent_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'agent_daemon' in ' '.join(cmdline):
                    agent_pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if agent_pid:
            try:
                process = psutil.Process(agent_pid)
                metrics["agent"]["pid"] = agent_pid
                metrics["agent"]["cpu_percent"] = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                metrics["agent"]["memory_mb"] = memory_info.rss / 1024 / 1024
                metrics["agent"]["num_threads"] = process.num_threads()
                metrics["agent"]["status"] = "running"
                
                # Try to get performance metrics from daemon
                try:
                    from unified_core.agent_daemon import get_daemon
                    daemon = get_daemon()
                    status = daemon.get_status()
                    metrics["performance"]["uptime_seconds"] = status.get("uptime_seconds")
                    metrics["performance"]["total_decisions"] = status.get("total_decisions")
                    metrics["performance"]["last_decision_time"] = status.get("last_decision_time")
                    metrics["performance"]["cycle_interval"] = status.get("cycle_interval")
                except Exception:
                    # Use process info for uptime
                    metrics["performance"]["uptime_seconds"] = time.time() - process.create_time()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                metrics["agent"]["status"] = "not_accessible"
                metrics["agent"]["error"] = str(e)
        else:
            metrics["agent"]["status"] = "not_running"
            metrics["performance"]["status"] = "daemon_not_available"
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_recent_decisions_data(limit: int = 10) -> Dict[str, Any]:
    """Internal function to get recent decisions data"""
    try:
        decisions = []
        
        try:
            # Try to read from agent log
            log_path = "/tmp/noogh-agent.log"
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    lines = f.readlines()[-500:]  # Last 500 lines for better coverage
                
                # Look for CYCLE lines
                for line in lines:
                    if "=== CYCLE" in line:
                        try:
                            # Parse: 2026-02-05 17:46:03,172 | INFO | agent_daemon | === CYCLE 30 [65b3d121af61187b] ===
                            parts = line.split("|")
                            if len(parts) >= 4:
                                timestamp = parts[0].strip()
                                message = parts[3].strip()
                                
                                # Extract cycle info
                                if "CYCLE" in message:
                                    cycle_parts = message.split("CYCLE")[1].strip().split("[")
                                    if len(cycle_parts) >= 2:
                                        cycle_num = cycle_parts[0].strip()
                                        cycle_id = cycle_parts[1].replace("]", "").replace("=", "").strip()
                                        
                                        decisions.append({
                                            "timestamp": timestamp,
                                            "cycle_id": cycle_id,
                                            "cycle_number": int(cycle_num) if cycle_num.isdigit() else cycle_num,
                                            "arabic_type": "دورة قرار",
                                            "type": "decision_cycle",
                                            "observations_collected": 0,
                                            "action_executed": True
                                        })
                        except Exception as parse_error:
                            logger.debug(f"Could not parse cycle line: {parse_error}")
                            continue
                
        except Exception as e:
            logger.warning(f"Could not read decision log: {e}")
        
        # Sort by cycle number if available, otherwise keep order
        try:
            decisions.sort(key=lambda x: x.get('cycle_number', 0), reverse=True)
        except:
            pass
        
        return {
            "count": len(decisions),
            "decisions": decisions[:limit],
            "arabic_summary": f"تم العثور على {len(decisions)} دورة قرار"
        }
        
    except Exception as e:
        logger.error(f"Decision history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# AGENT STATUS ENDPOINTS
# ========================================

@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    Get current status of the autonomous agent daemon.
    الحصول على الحالة الحالية لبرنامج وكيل المستقل.
    
    READ-ONLY: Does not affect agent behavior.
    للقراءة فقط: لا يؤثر على سلوك الوكيل.
    """
    return await _get_agent_status_data()


@router.get("/health", response_model=AgentHealth)
async def get_agent_health():
    """
    Get comprehensive health status of the agent.
    الحصول على حالة الصحة الشاملة للوكيل.
    """
    return await _get_agent_health_data()


@router.get("/metrics")
async def get_agent_metrics():
    """
    Get detailed performance metrics for the agent.
    الحصول على مقاييس الأداء التفصيلية للوكيل.
    """
    return await _get_agent_metrics_data()


@router.get("/decisions/recent")
async def get_recent_decisions(limit: int = 10):
    """
    Get recent decision history.
    الحصول على سجل القرارات الحديثة.
    """
    return await _get_recent_decisions_data(limit)


@router.get("/tracking/start")
async def start_tracking():
    """
    Start agent tracking session.
    بدء جلسة تتبع الوكيل.
    """
    return {
        "status": "tracking_started",
        "arabic_status": "بدأ التتبع",
        "session_id": f"track_{int(time.time())}",
        "timestamp": time.time()
    }


@router.get("/tracking/stop")
async def stop_tracking():
    """
    Stop agent tracking session.
    إيقاف جلسة تتبع الوكيل.
    """
    return {
        "status": "tracking_stopped",
        "arabic_status": "توقف التتبع",
        "timestamp": time.time()
    }
