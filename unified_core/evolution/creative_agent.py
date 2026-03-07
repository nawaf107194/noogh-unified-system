"""
Creative Evolution Agent — Multi-Strategy Unified Orchestrator
Version: 1.0.0
Part of: Cognitive Evolution System (v5.0)

Unlike single-source evolution, this agent draws from multiple data sources:
- Code analysis (existing BrainAssistedRefactoring)
- Performance metrics (WorldModel latency data)
- Error patterns (ScarTissue/FailureRecord analysis)
- LLM creativity (InnovationEngine)
- Curiosity/exploration (random function improvement)

The agent coordinates all strategies and prioritizes the best proposals.
"""

import logging
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ledger import EvolutionProposal, ProposalType, get_evolution_ledger
from .promoted_targets import get_promoted_targets
from . import evolution_config as config

logger = logging.getLogger("unified_core.evolution.creative_agent")


# ═══════════════════════════════════════════════════════════════
# Strategy Interface
# ═══════════════════════════════════════════════════════════════

@dataclass
class StrategyProposal:
    """A proposal from any strategy, before conversion to EvolutionProposal."""
    strategy_name: str
    target_file: str
    target_function: str
    description: str
    rationale: str
    priority: float = 0.0  # Higher = more important
    risk: float = 30.0     # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvolutionStrategy(ABC):
    """Base class for evolution strategies."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self._last_run = 0.0
        self._cooldown = 300.0  # Default 5 min cooldown
        self._run_count = 0
        self._success_count = 0
    
    def can_run(self) -> bool:
        return (time.time() - self._last_run) > self._cooldown
    
    def mark_run(self):
        self._last_run = time.time()
        self._run_count += 1
    
    @abstractmethod
    async def generate(self) -> List[StrategyProposal]:
        """Generate proposals from this strategy."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "runs": self._run_count,
            "successes": self._success_count,
            "success_rate": self._success_count / max(self._run_count, 1),
        }


# ═══════════════════════════════════════════════════════════════
# Strategy Implementations
# ═══════════════════════════════════════════════════════════════

class PerformanceStrategy(EvolutionStrategy):
    """Proposes improvements based on system performance data.
    
    Reads from WorldModel's belief system for latency and resource metrics.
    """
    
    def __init__(self, world_model=None):
        super().__init__("performance", weight=1.2)
        self._world_model = world_model
        self._cooldown = 600.0  # 10 min — perf data doesn't change fast
    
    def set_world_model(self, wm):
        self._world_model = wm
    
    async def generate(self) -> List[StrategyProposal]:
        if not self._world_model or not self.can_run():
            return []
        
        self.mark_run()
        proposals = []
        
        try:
            # Get performance beliefs from WorldModel
            beliefs = self._world_model.beliefs if hasattr(self._world_model, 'beliefs') else {}
            
            # Look for latency data
            latency = None
            for key, belief in beliefs.items():
                if 'latency' in str(key).lower() or 'response_time' in str(key).lower():
                    val = getattr(belief, 'value', belief) if hasattr(belief, 'value') else belief
                    if isinstance(val, (int, float)) and val > 2.0:  # > 2 seconds
                        latency = val
                        proposals.append(StrategyProposal(
                            strategy_name=self.name,
                            target_file="",  # Will be filled by Brain
                            target_function="",
                            description=f"High latency detected: {val:.1f}s (belief: {key})",
                            rationale=f"System belief '{key}' shows {val:.1f}s latency, above 2s threshold",
                            priority=min(val * 10, 50),
                            risk=25,
                            metadata={"belief_key": str(key), "latency_value": val}
                        ))
            
            # Look for CPU/memory warnings
            for key, belief in beliefs.items():
                key_str = str(key).lower()
                if 'cpu' in key_str or 'memory' in key_str or 'health' in key_str:
                    val = getattr(belief, 'value', belief) if hasattr(belief, 'value') else belief
                    if isinstance(val, dict):
                        cpu = val.get('cpu_percent', 0)
                        mem = val.get('memory_percent', 0)
                        if cpu > 80 or mem > 85:
                            proposals.append(StrategyProposal(
                                strategy_name=self.name,
                                target_file="",
                                target_function="",
                                description=f"Resource pressure: CPU={cpu}%, MEM={mem}%",
                                rationale=f"System under resource pressure, optimization needed",
                                priority=30,
                                risk=20,
                                metadata={"cpu": cpu, "memory": mem}
                            ))
            
            if proposals:
                logger.info(f"📊 PerformanceStrategy: {len(proposals)} proposals from WorldModel")
                
        except Exception as e:
            logger.debug(f"PerformanceStrategy failed: {e}")
        
        return proposals


class ErrorPatternStrategy(EvolutionStrategy):
    """Proposes improvements based on recurring error patterns.
    
    Reads from FailureRecord (ScarTissue) and EvolutionMemory to find
    functions that repeatedly cause errors.
    """
    
    def __init__(self, failure_record=None, evolution_memory=None):
        super().__init__("error_patterns", weight=1.5)
        self._failure_record = failure_record
        self._evolution_memory = evolution_memory
        self._cooldown = 600.0
    
    def set_failure_record(self, fr):
        self._failure_record = fr
    
    def set_evolution_memory(self, mem):
        self._evolution_memory = mem
    
    async def generate(self) -> List[StrategyProposal]:
        if not self.can_run():
            return []
        
        self.mark_run()
        proposals = []
        
        try:
            # Analyze scars for patterns
            if self._failure_record and hasattr(self._failure_record, 'scars'):
                # Group scars by action_type to find recurring patterns
                action_counts: Dict[str, int] = {}
                recent_errors: List[Dict] = []
                
                for scar in self._failure_record.scars:
                    action_type = scar.actions_blocked[0] if scar.actions_blocked else "unknown"
                    action_counts[action_type] = action_counts.get(action_type, 0) + 1
                    
                    # Track recent scars (last 24h)
                    if time.time() - scar.created_at < 86400:
                        recent_errors.append(scar.to_dict())
                
                # Find recurring failure patterns (3+ same type)
                for action, count in action_counts.items():
                    if count >= 3:
                        proposals.append(StrategyProposal(
                            strategy_name=self.name,
                            target_file="",
                            target_function="",
                            description=f"Recurring failure pattern: '{action}' ({count} scars)",
                            rationale=f"Action '{action}' has caused {count} permanent scars. Needs defensive redesign.",
                            priority=count * 15,
                            risk=35,
                            metadata={"action_type": action, "scar_count": count, "recent": recent_errors[:3]}
                        ))
            
            # Check EvolutionMemory for fragile files
            if self._evolution_memory:
                stats = self._evolution_memory.get_stats()
                fragile = stats.get("fragile_files", {})
                for filepath, expiry in fragile.items():
                    proposals.append(StrategyProposal(
                        strategy_name=self.name,
                        target_file=filepath,
                        target_function="",
                        description=f"Fragile file needs stabilization: {filepath.split('/')[-1]}",
                        rationale=f"File marked as fragile by EvolutionMemory due to repeated failures",
                        priority=25,
                        risk=40,
                        metadata={"fragile_until": expiry}
                    ))
            
            if proposals:
                logger.info(f"🩹 ErrorPatternStrategy: {len(proposals)} proposals from failure analysis")
                
        except Exception as e:
            logger.debug(f"ErrorPatternStrategy failed: {e}")
        
        return proposals


class CuriosityStrategy(EvolutionStrategy):
    """Proposes exploratory improvements to functions that haven't been touched.
    
    Uses InnovationEngine's random function picker to find unexplored areas.
    """
    
    def __init__(self):
        super().__init__("curiosity", weight=0.5)
        self._cooldown = 1800.0  # 30 min — curiosity is rare
    
    async def generate(self) -> List[StrategyProposal]:
        if not self.can_run() or random.random() > 0.3:  # Only 30% chance
            return []
        
        self.mark_run()
        proposals = []
        
        try:
            from .innovation_engine import get_innovation_engine
            engine = get_innovation_engine()
            
            # Pick a random function for architecture review
            # _pick_random_function returns keys: file_path, function_name, code, start_line, end_line
            func_info = engine._pick_random_function()
            if func_info:
                target_file = func_info.get("file_path", "")
                target_func = func_info.get("function_name", "")
                proposals.append(StrategyProposal(
                    strategy_name=self.name,
                    target_file=target_file,
                    target_function=target_func,
                    description=f"Curiosity exploration: {target_func} in {target_file.split('/')[-1]}",
                    rationale="Random exploration to discover improvement opportunities in untouched code",
                    priority=10,
                    risk=20,
                    metadata={"exploration": True, "func_info": func_info}
                ))
                logger.info(f"🔍 CuriosityStrategy: exploring {target_func}")
        except Exception as e:
            logger.debug(f"CuriosityStrategy failed: {e}")
        
        return proposals


# ═══════════════════════════════════════════════════════════════
# Creative Evolution Agent (Orchestrator)
# ═══════════════════════════════════════════════════════════════

class CreativeEvolutionAgent:
    """Multi-strategy evolution orchestrator.
    
    Coordinates all data sources and strategies to generate
    diverse, high-quality evolution proposals.
    
    Integration:
        Called by EvolutionController during handle_trigger() to
        supplement the existing brain_refactor and innovation pipelines.
    """
    
    _instance: Optional["CreativeEvolutionAgent"] = None
    
    def __init__(self):
        self._promoted_targets = get_promoted_targets()
        
        # Initialize strategies
        self._performance = PerformanceStrategy()
        self._error_patterns = ErrorPatternStrategy()
        self._curiosity = CuriosityStrategy()
        
        self.strategies: List[EvolutionStrategy] = [
            self._performance,
            self._error_patterns,
            self._curiosity,
        ]
        
        # Stats
        self._total_proposals = 0
        self._total_filtered = 0
        self._cycle_count = 0
        
        logger.info(f"🧠 CreativeEvolutionAgent initialized with {len(self.strategies)} strategies")
    
    @classmethod
    def get_instance(cls) -> "CreativeEvolutionAgent":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def wire_components(self, world_model=None, failure_record=None, 
                        evolution_memory=None):
        """Wire cognitive components into strategies."""
        if world_model:
            self._performance.set_world_model(world_model)
        if failure_record:
            self._error_patterns.set_failure_record(failure_record)
        if evolution_memory:
            self._error_patterns.set_evolution_memory(evolution_memory)
        logger.info("🔌 CreativeEvolutionAgent: components wired")
    
    async def generate_proposals(self, max_total: int = 3) -> List[StrategyProposal]:
        """Run all strategies and return prioritized proposals.
        
        Args:
            max_total: Maximum proposals to return (across all strategies)
        
        Returns:
            Filtered, prioritized list of StrategyProposals
        """
        self._cycle_count += 1
        all_proposals: List[StrategyProposal] = []
        
        for strategy in self.strategies:
            try:
                proposals = await strategy.generate()
                all_proposals.extend(proposals)
            except Exception as e:
                logger.debug(f"Strategy {strategy.name} failed: {e}")
        
        if not all_proposals:
            return []
        
        # Filter out already-promoted targets
        filtered = []
        for p in all_proposals:
            if p.target_file and p.target_function:
                if self._promoted_targets.contains(p.target_file, p.target_function):
                    self._total_filtered += 1
                    continue
            filtered.append(p)
        
        # Sort by priority (highest first), then by risk (lowest first)
        filtered.sort(key=lambda p: (p.priority, -p.risk), reverse=True)
        
        result = filtered[:max_total]
        self._total_proposals += len(result)
        
        if result:
            logger.info(
                f"🧠 CreativeAgent: {len(result)} proposals from "
                f"{len(set(p.strategy_name for p in result))} strategies "
                f"(filtered {len(all_proposals) - len(filtered)} promoted)"
            )
        
        return result
    
    def convert_to_evolution_proposal(self, sp: StrategyProposal) -> Optional[EvolutionProposal]:
        """Convert a StrategyProposal to an EvolutionProposal for the ledger."""
        try:
            # v13: Skip proposals with no actual code changes or missing targets
            has_code = (sp.metadata.get("generated_code") or 
                       sp.metadata.get("refactored_code") or
                       sp.metadata.get("original_code"))
            if not has_code:
                logger.info(f"⏭️ Skipping {sp.strategy_name} proposal — no generated code yet")
                return None
                
            if not sp.target_file:
                logger.info(f"⏭️ Skipping {sp.strategy_name} proposal — no target file")
                return None
            
            proposal = EvolutionProposal(
                proposal_id=f"creative_{int(time.time())}_{sp.strategy_name}",
                proposal_type=ProposalType.CODE,
                description=f"[{sp.strategy_name.upper()}] {sp.description}",
                scope="code",
                targets=[sp.target_file] if sp.target_file else [],
                diff=f"# Strategy: {sp.strategy_name}\n# {sp.rationale}\n",
                risk_score=int(sp.risk),
                expected_benefit=sp.rationale,
                rollback_plan="Revert to backup",
                rationale=f"CreativeEvolutionAgent/{sp.strategy_name}: {sp.rationale}"
            )
            proposal.metadata = {
                "strategy": sp.strategy_name,
                "function": sp.target_function,
                "priority": sp.priority,
                **sp.metadata
            }
            return proposal
        except Exception as e:
            logger.error(f"Failed to convert proposal: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "cycles": self._cycle_count,
            "total_proposals": self._total_proposals,
            "total_filtered": self._total_filtered,
            "strategies": [s.get_stats() for s in self.strategies]
        }


def get_creative_agent() -> CreativeEvolutionAgent:
    """Get singleton CreativeEvolutionAgent instance."""
    return CreativeEvolutionAgent.get_instance()
