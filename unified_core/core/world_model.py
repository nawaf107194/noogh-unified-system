import hashlib
import json
import logging
import os
import time
import asyncio
import httpx
import re
from dataclasses import dataclass, field, fields as field_fields
from typing import Any, Dict, List, Optional, Set, AsyncIterator
from enum import Enum
from contextlib import asynccontextmanager

logger = logging.getLogger("unified_core.core.world_model")

class BeliefState(Enum):
    ACTIVE = "active"
    WEAKENED = "weakened"
    FALSIFIED = "falsified"

@dataclass
class Observation:
    source: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    observation_id: str = field(default_factory=lambda: hashlib.sha256(f"{time.time()}:{os.urandom(8).hex()}".encode()).hexdigest()[:16])

class Belief:
    def __init__(self, belief_id: str, proposition: str, confidence: float, state: Any = "active", **kwargs):
            if not belief_id.strip():
                raise ValueError("belief_id cannot be an empty string after stripping")
            if not proposition.strip():
                raise ValueError("proposition cannot be an empty string after stripping")
            if not 0 <= confidence <= 1:
                raise ValueError("confidence must be between 0 and 1 inclusive")

            self.belief_id = belief_id
            self.proposition = proposition
            self.confidence = confidence
            self.state = self._parse_state(state)
            self.created_at = kwargs.get("created_at", time.time())

            logging.debug(f"Belief initialized: {self.belief_id[:8]} | {self.proposition[:40]}")
    def _parse_state(self, val: Any) -> BeliefState:
        if isinstance(val, BeliefState): return val
        try: return BeliefState(str(val))
        except: return BeliefState.ACTIVE
    def is_usable(self) -> bool:
        return self.state != BeliefState.FALSIFIED

    def to_dict(self) -> Dict[str, Any]:
            state_value = self.state.value if hasattr(self.state, 'value') else str(self.state)
            return {
                "belief_id": self.belief_id,
                "proposition": self.proposition,
                "confidence": self.confidence,
                "state": state_value,
                "created_at": self.created_at
            }

@dataclass
class Prediction:
    prediction_id: str
    based_on_beliefs: List[str]
    predicted_outcome: Dict[str, Any]
    confidence: float
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    was_correct: Optional[bool] = None

@dataclass
class Falsification:
    falsification_id: str
    prediction_id: str
    beliefs_falsified: List[str]
    predicted: Dict[str, Any]
    actual: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"falsification_id": self.falsification_id, "prediction_id": self.prediction_id, "beliefs_falsified": self.beliefs_falsified, "predicted": self.predicted, "actual": self.actual, "timestamp": self.timestamp}

class WorldModel:
    MAX_CONFIDENCE_CAP = 0.95

    def __init__(self, config: Optional[Dict] = None):
        from unified_core.core.memory_store import UnifiedMemoryStore
        self._memory = UnifiedMemoryStore()
        
        try:
            from unified_core.integration.event_bus import get_event_bus, StandardEvents
            self._event_bus = get_event_bus()
            self._events = StandardEvents
        except ImportError as e:
            logger.warning(f"Could not load EventBus into WorldModel: {e}")
            self._event_bus = None
            self._events = None
            
        from unified_core.config import settings
        self.STORAGE_LOCATIONS = settings.WORLD_STORAGE_LOCATIONS
        self._loaded = False
        self._background_tasks: Set[asyncio.Task] = set()
        self._synthesis_lock = asyncio.Lock()
        self._neural_failures = 0
        self._last_synthesis = 0
        logger.info("WorldModel Master Restored.")

    async def setup(self):
        if self._loaded: return
        await self._load_state()
        self._loaded = True
        logger.info("Setup complete.")

    def _belief_from_dict(self, data: Dict[str, Any]) -> Belief:
            d = data.copy()
            bid = d.pop("belief_id", d.pop("key", "unknown"))
            prop = d.pop("proposition", d.pop("value", str(d)))
            conf = d.pop("confidence", 0.5)
            if not prop:
                logger.warning("Proposition is empty, setting to 'unknown'")
                prop = "unknown"
            return Belief(belief_id=bid, proposition=prop, confidence=conf, **d)

    def _prediction_from_dict(self, data: Dict[str, Any]) -> Prediction:
            if not data:
                logger.warning("Received empty data dictionary, returning default Prediction instance")
                return Prediction()

            valid_keys = {"prediction_id", "based_on_beliefs", "predicted_outcome", "confidence", "created_at", "resolved", "was_correct"}
            filtered = {k: v for k, v in data.items() if k in valid_keys}

            if len(filtered) < len(data):
                removed_keys = set(data.keys()) - set(filtered.keys())
                logger.debug(f"Filtered out invalid keys: {removed_keys}")

            return Prediction(**filtered)

    async def _load_state(self):
        all_f = await self._memory.get_all_falsifications()
        cf = {f["falsification_id"]: f for f in all_f}
        for loc in self.STORAGE_LOCATIONS:
            path = os.path.join(loc, "falsifications.jsonl")
            if not os.path.exists(path): continue
            try:
                with open(path, "r") as f:
                    for line in f:
                        d = json.loads(line.strip()).get("data", json.loads(line.strip()))
                        if d.get("falsification_id") not in cf:
                            await self._memory.append_falsification(Falsification(**d))
            except Exception as e: logger.error(f"Load error: {e}")

    async def add_belief(self, proposition: str, initial_confidence: float = 0.5) -> Belief:
        # Input sanitization
        try:
            from unified_core.integration.security_hardening import get_sanitizer
            proposition, _ = get_sanitizer().sanitize(proposition, "add_belief")
        except Exception:
            pass
        
        # Deterministic ID based on proposition content (prevents duplicates across restarts)
        bid = hashlib.sha256(proposition.encode()).hexdigest()[:16]
        
        # Check if belief already exists — skip if so
        existing = await self._memory.get_belief(bid)
        if existing is not None:
            return self._belief_from_dict(existing) if isinstance(existing, dict) else existing
        
        belief = Belief(bid, proposition, min(initial_confidence, self.MAX_CONFIDENCE_CAP))
        await self._memory.set_belief(bid, belief)
        logger.debug(f"✅ New belief added: {bid[:8]}... '{proposition[:50]}'")
        
        if getattr(self, '_event_bus', None) and getattr(self, '_events', None):
            try:
                await self._event_bus.publish(
                    event_type=self._events.BELIEF_ADDED,
                    data={
                        "belief_id": bid,
                        "proposition": proposition,
                        "confidence": belief.confidence,
                        "state": belief.state.value if hasattr(belief.state, "value") else str(belief.state)
                    },
                    source="WorldModel"
                )
            except Exception as e:
                logger.error(f"Failed to publish belief_added event: {e}")
        
        # NeuronFabric integration: auto-create neuron from belief
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
            fabric = get_neuron_fabric()
            neuron = fabric.create_neuron(
                proposition=proposition,
                neuron_type=NeuronType.COGNITIVE,
                confidence=belief.confidence,
                domain=self._infer_domain(proposition),
                tags=["belief", f"bid:{bid[:8]}"],
                metadata={"belief_id": bid, "source": "WorldModel.add_belief"}
            )
            fabric.auto_connect(neuron.neuron_id, max_connections=5)
            logger.debug(f"🧬 Neuron {neuron.neuron_id[:8]} created for belief {bid[:8]}")
        except Exception as e:
            logger.debug(f"NeuronFabric integration skipped: {e}")
                
        return belief

    async def observe(self, observation: Observation) -> List[Any]:
        await self._memory.append_observation(observation)
        now = time.time()
        if now - self._last_synthesis > 30 and not self._synthesis_lock.locked():
            self._last_synthesis = now
            task = asyncio.create_task(self.synthesize_semantic_beliefs())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        return []

    async def get_recent_observations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Public API to access recent observations (Async).
        Required by agent_daemon and task_dispatcher.
        """
        try:
            if hasattr(self._memory, 'get_recent_observations'):
                return await self._memory.get_recent_observations(limit=limit)
            else:
                logger.warning("Memory store missing get_recent_observations, returning empty list")
                return []
        except Exception as e:
            logger.error(f"Failed to get recent observations: {e}")
            return []

    async def predict(self, query: str, based_on: Optional[List[str]] = None) -> Prediction:
        mem = await self._memory.get_all_beliefs()
        eligible = [self._belief_from_dict(v) for v in mem.values() if self._belief_from_dict(v).is_usable()]
        p_id = hashlib.sha256(f"p:{query}:{time.time()}".encode()).hexdigest()[:16]
        prediction = Prediction(p_id, [b.belief_id for b in eligible], {"likely": True}, 0.5)
        await self._memory.save_prediction(prediction)
        return prediction

    async def falsify(self, prediction_id: str, actual_outcome: Dict[str, Any]) -> Optional[Falsification]:
        p_data = await self._memory.get_prediction(prediction_id)
        if not p_data: return None
        prediction = self._prediction_from_dict(p_data)
        if prediction.resolved: return None
        
        prediction.resolved = True
        prediction.was_correct = actual_outcome.get("success", False)
        await self._memory.save_prediction(prediction)
        
        if not prediction.was_correct:
            f_id = hashlib.sha256(f"f:{prediction_id}:{time.time()}".encode()).hexdigest()[:16]
            falsification = Falsification(
                falsification_id=f_id,
                prediction_id=prediction_id,
                beliefs_falsified=prediction.based_on_beliefs,
                predicted=prediction.predicted_outcome,
                actual=actual_outcome
            )
            await self._memory.append_falsification(falsification)
            
            if getattr(self, '_event_bus', None) and getattr(self, '_events', None):
                try:
                    await self._event_bus.publish(
                        event_type=self._events.BELIEF_FALSIFIED,
                        data={
                            "falsification_id": f_id,
                            "prediction_id": prediction_id,
                            "beliefs_falsified": prediction.based_on_beliefs
                        },
                        source="WorldModel"
                    )
                except Exception as e:
                    logger.error(f"Failed to publish belief_falsified event: {e}")
                    
            return falsification
            
        return None

    async def get_usable_beliefs(self) -> List[Belief]:
        mem = await self._memory.get_all_beliefs()
        return [self._belief_from_dict(b) for b in mem.values() if self._belief_from_dict(b).is_usable()]

    async def get_belief_state(self) -> Dict[str, Any]:
        """Return comprehensive belief statistics with all required keys for MetaGovernor."""
        try:
            mem = await self._memory.get_all_beliefs()
            active = weakened = falsified = 0
            total_confidence = 0.0
            
            for data in mem.values():
                belief = self._belief_from_dict(data)
                if belief.state == BeliefState.ACTIVE:
                    active += 1
                elif belief.state == BeliefState.WEAKENED:
                    weakened += 1
                elif belief.state == BeliefState.FALSIFIED:
                    falsified += 1
                total_confidence += belief.confidence
            
            avg_confidence = total_confidence / len(mem) if mem else 0.0
            all_fals = await self._memory.get_all_falsifications()
            
            return {
                "total_beliefs": len(mem),
                "active": active,
                "weakened": weakened,
                "falsified": falsified,
                "average_confidence": round(avg_confidence, 3),
                "total_falsifications": len(all_fals),
                "background_tasks": len(self._background_tasks),
                "loaded": self._loaded
            }
        except Exception as e:
            logger.error(f"Failed to get belief state: {e}")
            return {
                "total_beliefs": 0, "active": 0, "weakened": 0, "falsified": 0,
                "average_confidence": 0.0, "total_falsifications": 0,
                "background_tasks": len(self._background_tasks), "loaded": self._loaded
            }

    async def synthesize_semantic_beliefs(self):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client: pass # Placeholder
        except Exception: pass

    async def shutdown(self):
        for task in list(self._background_tasks): task.cancel()
        if self._background_tasks: await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def consolidate_memory(self):
        """
        Cognitive Entropy Consolidation v2.4 (Emergency Scaling).
        Simplified version to avoid dependency issues.
        """
        logger.info("🧠 Starting memory consolidation...")
        try:
            all_beliefs = await self._memory.get_all_beliefs()
            total_beliefs = len(all_beliefs)
            target_capacity = 50000 * 0.8
            if total_beliefs > target_capacity:
                prune_count = int((total_beliefs - target_capacity) * 0.1)
                logger.info(f"Population {total_beliefs} exceeds target {target_capacity}, pruning {prune_count} beliefs")
                beliefs_list = []
                for bid, data in all_beliefs.items():
                    belief = self._belief_from_dict(data)
                    beliefs_list.append((belief.confidence, bid, belief))
                beliefs_list.sort(key=lambda x: x[0])
                pruned = 0
                for _, bid, belief in beliefs_list[:prune_count]:
                    if belief.state != BeliefState.FALSIFIED and belief.confidence < 0.4:
                        await self._memory.delete_belief(bid)
                        pruned += 1
                logger.info(f"Pruned {pruned} low-confidence beliefs")
            logger.info(f"Consolidation complete. Total beliefs: {total_beliefs}")
        except Exception as e:
            logger.error(f"Consolidation failed: {e}")

    def get_query_latency(self) -> float:
            """Public API to access query latency metric (Sync for AgentDaemon)."""
            latency = getattr(self._memory, '_query_latency_ewma', None)
            if latency is None:
                logger.warning("Query latency metric not found, returning 0.0")
                return 0.0
            return latency

    async def record_evolution_step(self, evolution_id: str, path: str, eye: str, rationale: str, context: Dict[str, Any] = None, outcome: str = "", success: bool = True):
        """Public API to record a strategic evolution event (Async)."""
        try:
            if hasattr(self._memory, 'record_evolution_step'):
                return await self._memory.record_evolution_step(evolution_id, path, eye, rationale, context, outcome, success)
            else:
                logger.warning("Memory store missing record_evolution_step")
                return None
        except Exception as e:
            logger.error(f"Failed to record evolution step: {e}")
            return None

    async def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Public API to retrieve recent strategic evolution steps (Async)."""
        try:
            if hasattr(self._memory, 'get_evolution_history'):
                return await self._memory.get_evolution_history(limit)
            else:
                logger.warning("Memory store missing get_evolution_history")
                return []
        except Exception as e:
            logger.error(f"Failed to get evolution history: {e}")
            return []

    def _infer_domain(self, proposition: str) -> str:
        """Infer domain from belief proposition text."""
        p = proposition.lower()
        domain_keywords = {
            "trading": ["trade", "market", "price", "btc", "eth", "binance", "futures", "pnl", "leverage"],
            "security": ["security", "audit", "vulnerability", "attack", "injection", "tamper"],
            "system": ["cpu", "memory", "gpu", "disk", "process", "service", "daemon"],
            "intelligence": ["neuron", "belief", "decision", "prediction", "reasoning", "cognitive"],
            "evolution": ["evolve", "refactor", "improve", "optimize", "learn"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in p for kw in keywords):
                return domain
        return "general"
