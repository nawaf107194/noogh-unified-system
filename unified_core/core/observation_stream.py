"""
Observation Stream - Real-Time Environment Signal Collection

Collects live signals from the environment and feeds them to WorldModel.
This enables the AI to observe reality, not just respond to requests.

Signals Collected:
- System metrics (CPU, memory, disk, network)
- Process health
- Error rates
- Queue depths
- Timing metrics
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("unified_core.core.observation_stream")

# Try to import psutil for system metrics
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available - system metrics limited")


@dataclass
class Signal:
    """A single signal from the environment."""
    name: str
    value: Any
    source: str
    timestamp: float = field(default_factory=time.time)
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "unit": self.unit
        }


class SignalCollector:
    """Base class for signal collectors."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def collect(self) -> List[Signal]:
        """Collect signals. Override in subclass."""
        raise NotImplementedError


class SystemMetricsCollector(SignalCollector):
    """Collects system-level metrics."""
    
    def __init__(self):
        super().__init__("system_metrics")
        self._last_cpu = 0.0
        self._last_net_io = None
    
    async def collect(self) -> List[Signal]:
        signals = []
        
        if not HAS_PSUTIL:
            return signals
        
        try:
            signals.extend(self._get_cpu_signals())
            signals.extend(self._get_mem_signals())
            signals.extend(self._get_disk_signals())
            signals.extend(self._get_load_signals())
            signals.extend(self._get_net_signals())
            signals.extend(self._get_proc_signals())
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            signals.append(Signal(
                name="collection_error",
                value=str(e),
                source="system_metrics_collector"
            ))
        
        return signals

    def _get_cpu_signals(self) -> List[Signal]:
        return [Signal(
            name="cpu_usage",
            value=psutil.cpu_percent(interval=0.1),
            source="psutil",
            unit="percent"
        )]

    def _get_mem_signals(self) -> List[Signal]:
        mem = psutil.virtual_memory()
        return [
            Signal(
                name="memory_usage",
                value=mem.percent,
                source="psutil",
                unit="percent"
            ),
            Signal(
                name="memory_available_mb",
                value=mem.available / (1024 * 1024),
                source="psutil",
                unit="MB"
            )
        ]

    def _get_disk_signals(self) -> List[Signal]:
        disk = psutil.disk_usage('/')
        return [Signal(
            name="disk_usage",
            value=disk.percent,
            source="psutil",
            unit="percent"
        )]

    def _get_load_signals(self) -> List[Signal]:
        try:
            load1, load5, load15 = os.getloadavg()
            return [Signal(
                name="load_average_1m",
                value=load1,
                source="os",
                unit="load"
            )]
        except (AttributeError, OSError):
            return []

    def _get_net_signals(self) -> List[Signal]:
        signals = []
        net_io = psutil.net_io_counters()
        if self._last_net_io:
            signals.append(Signal(
                name="network_bytes_sent_rate",
                value=net_io.bytes_sent - self._last_net_io.bytes_sent,
                source="psutil",
                unit="bytes/s"
            ))
            signals.append(Signal(
                name="network_bytes_recv_rate",
                value=net_io.bytes_recv - self._last_net_io.bytes_recv,
                source="psutil",
                unit="bytes/s"
            ))
        self._last_net_io = net_io
        return signals

    def _get_proc_signals(self) -> List[Signal]:
        return [Signal(
            name="process_count",
            value=len(psutil.pids()),
            source="psutil",
            unit="count"
        )]


class AgentHealthCollector(SignalCollector):
    """Collects agent-specific health metrics."""
    
    def __init__(self, gravity_well=None, scar_tissue=None, world_model=None):
        super().__init__("agent_health")
        self._gravity_well = gravity_well
        self._scar_tissue = scar_tissue
        self._world_model = world_model
    
    def set_components(self, gravity_well=None, scar_tissue=None, world_model=None):
        """Set component references."""
        if gravity_well:
            self._gravity_well = gravity_well
        if scar_tissue:
            self._scar_tissue = scar_tissue
        if world_model:
            self._world_model = world_model
    
    async def collect(self) -> List[Signal]:
        signals = []
        
        try:
            signals.extend(self._get_decision_signals())
            signals.extend(self._get_scar_signals())
            signals.extend(await self._get_belief_signals())
        
        except Exception as e:
            logger.error(f"Error collecting agent health: {e}")
            signals.append(Signal(
                name="collection_error",
                value=str(e),
                source="agent_health_collector"
            ))
        
        return signals

    def _get_decision_signals(self) -> List[Signal]:
        if self._gravity_well:
            return [Signal(
                name="decision_count",
                value=self._gravity_well.get_decision_count(),
                source="gravity_well",
                unit="count"
            )]
        return []

    def _get_scar_signals(self) -> List[Signal]:
        signals = []
        if self._scar_tissue:
            signals.append(Signal(
                name="scar_depth",
                value=self._scar_tissue.get_scar_depth(),
                source="scar_tissue",
                unit="depth"
            ))
            signals.append(Signal(
                name="scar_count",
                value=self._scar_tissue.get_scar_count(),
                source="scar_tissue",
                unit="count"
            ))
        return signals

    async def _get_belief_signals(self) -> List[Signal]:
        signals = []
        if self._world_model:
            state = await self._world_model.get_belief_state()
            signals.append(Signal(
                name="belief_count_active",
                value=state.get("active", 0),
                source="world_model",
                unit="count"
            ))
            signals.append(Signal(
                name="belief_count_falsified",
                value=state.get("falsified", 0),
                source="world_model",
                unit="count"
            ))
            signals.append(Signal(
                name="falsification_count",
                value=state.get("total_falsifications", 0),
                source="world_model",
                unit="count"
            ))
        return signals


class SpatialCollector(SignalCollector):
    """Tracks physical environment changes and structural pulse."""
    
    def __init__(self, spatial_specialist=None):
        super().__init__("spatial_pulse")
        self._spatial_specialist = spatial_specialist
    
    async def collect(self) -> List[Signal]:
        if not self._spatial_specialist:
            return []
            
        try:
            spatial_map = self._spatial_specialist.spatial_map
            return [Signal(
                name="spatial_node_count",
                value=len(spatial_map.get("nodes", [])),
                source="spatial_specialist",
                unit="nodes"
            ), Signal(
                name="project_root",
                value=spatial_map.get("root", "unknown"),
                source="spatial_specialist"
            )]
        except Exception as e:
            logger.error(f"Spatial collection failed: {e}")
            return []


class ErrorRateCollector(SignalCollector):
    """Tracks error rates from logs or metrics."""
    
    def __init__(self, window_seconds: float = 60.0):
        super().__init__("error_rate")
        self._window = window_seconds
        self._errors: List[float] = []
        self._successes: List[float] = []
    
    def record_error(self):
        """Record an error occurrence."""
        self._errors.append(time.time())
    
    def record_success(self):
        """Record a success occurrence."""
        self._successes.append(time.time())
    
    def _prune_old(self):
        """Remove entries older than window."""
        cutoff = time.time() - self._window
        self._errors = [t for t in self._errors if t > cutoff]
        self._successes = [t for t in self._successes if t > cutoff]
    
    async def collect(self) -> List[Signal]:
        self._prune_old()
        
        total = len(self._errors) + len(self._successes)
        error_rate = len(self._errors) / total if total > 0 else 0.0
        
        return [
            Signal(
                name="error_count",
                value=len(self._errors),
                source="error_rate_collector",
                unit="count"
            ),
            Signal(
                name="success_count",
                value=len(self._successes),
                source="error_rate_collector",
                unit="count"
            ),
            Signal(
                name="error_rate",
                value=error_rate,
                source="error_rate_collector",
                unit="ratio"
            )
        ]


class ObservationStream:
    """
    Aggregates signals from all collectors and feeds WorldModel.
    
    This is the interface between the environment and the AI's beliefs.
    """
    
    def __init__(self, world_model=None):
        self._world_model = world_model
        
        # Initialize collectors
        self._system_collector = SystemMetricsCollector()
        self._agent_collector = AgentHealthCollector()
        self._error_collector = ErrorRateCollector()
        self._spatial_collector = SpatialCollector()
        
        self._collectors: List[SignalCollector] = [
            self._system_collector,
            self._agent_collector,
            self._error_collector,
            self._spatial_collector
        ]
        
        self._observation_count = 0
        
        logger.info("ObservationStream initialized with collectors: "
                   f"{[c.name for c in self._collectors]}")
    
    def set_components(self, gravity_well=None, scar_tissue=None, world_model=None, spatial_specialist=None):
        """Wire up component references."""
        if world_model:
            self._world_model = world_model
        if spatial_specialist:
            self._spatial_collector._spatial_specialist = spatial_specialist
        self._agent_collector.set_components(
            gravity_well=gravity_well,
            scar_tissue=scar_tissue,
            world_model=world_model
        )
    
    def record_error(self):
        """Record an error for error rate tracking."""
        self._error_collector.record_error()
    
    def record_success(self):
        """Record a success for error rate tracking."""
        self._error_collector.record_success()
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect all signals from all collectors.
        
        Returns list of observation dicts ready for WorldModel.
        """
        all_signals = await self._run_collectors()
        self._observation_count += 1
        return [s.to_dict() for s in all_signals]

    async def _run_collectors(self) -> List[Signal]:
        """Execute all signal collectors and aggregate results."""
        all_signals = []
        for collector in self._collectors:
            try:
                signals = await collector.collect()
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Collector {collector.name} failed: {e}")
                all_signals.append(Signal(
                    name="collector_failure",
                    value=str(e),
                    source=collector.name
                ))
        return all_signals
    
    def add_collector(self, collector: SignalCollector):
        """Add a custom signal collector."""
        self._collectors.append(collector)
        logger.info(f"Added collector: {collector.name}")
    
    def get_observation_count(self) -> int:
        """Return total observations collected."""
        return self._observation_count
