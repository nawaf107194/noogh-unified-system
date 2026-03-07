"""
NOOGH Autonomous Monitor
=========================
Self-triggered monitoring that runs independently.

The system watches itself and takes action when needed.
No user intervention required.

Runs as background task:
- Collects system metrics every N seconds
- Feeds observations to Decision Engine
- Executes decisions based on rules
"""

import asyncio
import logging
import subprocess
import psutil
import time
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Configuration for the autonomous monitor."""
    interval_seconds: int = 60          # Check every 60 seconds
    memory_threshold_warning: int = 80   # % memory usage
    memory_threshold_critical: int = 90
    disk_threshold_warning: int = 85     # % disk usage
    disk_threshold_critical: int = 95
    cpu_threshold_high: int = 90         # % CPU usage
    enabled: bool = True


class AutonomousMonitor:
    """
    🔄 Self-triggered monitoring system.
    
    Runs in background, observes system, makes decisions, takes actions.
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self.running = False
        self.last_check: Optional[datetime] = None
        self.check_count = 0
        self.alerts_sent: List[Dict] = []
        self._task: Optional[asyncio.Task] = None
        
        logger.info("🔄 Autonomous Monitor initialized")
    
    async def start(self):
        """Start the autonomous monitoring loop."""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"▶️ Autonomous Monitor started (interval: {self.config.interval_seconds}s)")
    
    async def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Autonomous Monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running and self.config.enabled:
            try:
                await self._check_system()
                self.check_count += 1
                self.last_check = datetime.now()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            await asyncio.sleep(self.config.interval_seconds)
    
    async def _check_system(self):
        """Perform system health check and make decisions."""
        from neural_engine.autonomy.decision_engine import get_decision_engine
        
        engine = get_decision_engine()
        
        # === Collect Metrics ===
        metrics = self._collect_metrics()
        
        # === Feed to Decision Engine ===
        for metric, value in metrics.items():
            obs = engine.observe(metric, value)
            decision = engine.evaluate(obs)
            
            if decision:
                # Execute the decision
                result = await engine.execute_decision(decision)
                
                # Record alert
                self.alerts_sent.append({
                    "timestamp": datetime.now().isoformat(),
                    "rule": decision.rule_id,
                    "message": decision.message,
                    "severity": decision.severity.value,
                    "result": result
                })
                
                # Keep only last 50 alerts
                if len(self.alerts_sent) > 50:
                    self.alerts_sent = self.alerts_sent[-50:]
                
                logger.info(f"🔔 Decision executed: {decision.message} → {result}")
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        metrics = {}
        
        try:
            # Memory
            mem = psutil.virtual_memory()
            metrics["memory_percent"] = mem.percent
            metrics["memory_available_gb"] = round(mem.available / (1024**3), 2)
            metrics["memory_used_gb"] = round(mem.used / (1024**3), 2)
            
            # Disk
            disk = psutil.disk_usage('/')
            metrics["disk_percent"] = disk.percent
            metrics["disk_free_gb"] = round(disk.free / (1024**3), 2)
            
            # CPU
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Load average (Linux)
            try:
                load = psutil.getloadavg()
                metrics["load_1m"] = load[0]
                metrics["load_5m"] = load[1]
            except:
                pass
            
            # Neural service status
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", "noogh-neural"],
                    capture_output=True, text=True, timeout=5
                )
                metrics["neural_service_active"] = result.stdout.strip() == "active"
            except:
                metrics["neural_service_active"] = False
            
            # GPU (if available)
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    metrics["gpu_temp"] = int(result.stdout.strip())
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
        
        return metrics
    
    def get_status(self) -> Dict:
        """Get monitor status."""
        return {
            "running": self.running,
            "enabled": self.config.enabled,
            "interval_seconds": self.config.interval_seconds,
            "check_count": self.check_count,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "alerts_count": len(self.alerts_sent),
            "recent_alerts": self.alerts_sent[-5:] if self.alerts_sent else []
        }
    
    def get_current_metrics(self) -> Dict:
        """Get current system metrics."""
        return self._collect_metrics()


# ========== Singleton ==========

_monitor: Optional[AutonomousMonitor] = None

def get_monitor() -> AutonomousMonitor:
    """Get or create global monitor."""
    global _monitor
    if _monitor is None:
        _monitor = AutonomousMonitor()
    return _monitor


async def start_autonomous_monitoring():
    """Start the autonomous monitoring system."""
    monitor = get_monitor()
    await monitor.start()
    return monitor


async def stop_autonomous_monitoring():
    """Stop the autonomous monitoring system."""
    monitor = get_monitor()
    await monitor.stop()


if __name__ == "__main__":
    # Test the monitor
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = AutonomousMonitor(MonitorConfig(interval_seconds=10))
        
        print(f"Current metrics: {monitor._collect_metrics()}")
        
        await monitor.start()
        await asyncio.sleep(25)  # Run for 25 seconds
        await monitor.stop()
        
        print(f"\nStatus: {monitor.get_status()}")
    
    asyncio.run(test())
