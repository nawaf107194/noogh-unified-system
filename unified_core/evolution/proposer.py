"""
Patch Proposer - Structured Proposal Generator for Evolution
Version: 1.1.0
Part of: Self-Directed Layer (Phase 17.5)

Generates structured improvement proposals based on system analysis.
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path

from .ledger import EvolutionProposal, ProposalType, ProposalStatus, get_evolution_ledger
from .policy_gate import get_policy_gate

logger = logging.getLogger("unified_core.evolution.proposer")


class PatchProposer:
    """
    Generates structured evolution proposals.
    
    Features:
    - Config proposals: adjust thresholds, intervals
    - Policy proposals: modify aggression bounds, weights
    - Code proposals: helper function improvements (restricted)
    
    All proposals are structured - no free-form code generation.
    """
    
    def __init__(self):
        self.ledger = get_evolution_ledger()
        self.policy_gate = get_policy_gate()
        
        # Proposal templates
        self.config_templates = {
            "interval_adjustment": self._propose_interval_adjustment,
            "threshold_adjustment": self._propose_threshold_adjustment,
        }
        
        self.policy_templates = {
            "aggression_bounds": self._propose_aggression_bounds,
            "risk_threshold": self._propose_risk_threshold,
        }
        
        logger.info("PatchProposer initialized")
    
    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        return f"prop_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def _propose_interval_adjustment(
        self,
        current_value: float,
        suggested_value: float,
        target_path: str = "config/intervals.yaml",
        rationale: str = ""
    ) -> Optional[EvolutionProposal]:
        """Create an interval adjustment proposal."""
        diff = f"""
# Interval Adjustment
- current: {current_value}
+ suggested: {suggested_value}
"""
        
        return EvolutionProposal(
            proposal_id=self._generate_proposal_id(),
            proposal_type=ProposalType.CONFIG,
            description=f"Adjust interval from {current_value} to {suggested_value}",
            scope="config",
            targets=[target_path],
            diff=diff,
            risk_score=10,
            expected_benefit="Improved cycle timing",
            rollback_plan=f"Revert to {current_value}",
            rationale=rationale or "Optimizing based on observed performance"
        )
    
    def _propose_threshold_adjustment(
        self,
        threshold_name: str,
        current_value: float,
        suggested_value: float,
        target_path: str = "config/thresholds.yaml",
        rationale: str = ""
    ) -> Optional[EvolutionProposal]:
        """Create a threshold adjustment proposal."""
        diff = f"""
# Threshold Adjustment: {threshold_name}
- {threshold_name}: {current_value}
+ {threshold_name}: {suggested_value}
"""
        
        return EvolutionProposal(
            proposal_id=self._generate_proposal_id(),
            proposal_type=ProposalType.CONFIG,
            description=f"Adjust {threshold_name} from {current_value} to {suggested_value}",
            scope="config",
            targets=[target_path],
            diff=diff,
            risk_score=15,
            expected_benefit=f"Optimized {threshold_name} for current load",
            rollback_plan=f"Revert {threshold_name} to {current_value}",
            rationale=rationale
        )
    
    def _propose_aggression_bounds(
        self,
        current_min: float,
        current_max: float,
        suggested_min: float,
        suggested_max: float,
        rationale: str = ""
    ) -> Optional[EvolutionProposal]:
        """Create an aggression bounds proposal."""
        diff = f"""
# Aggression Bounds Adjustment
- min_aggression: {current_min}
- max_aggression: {current_max}
+ min_aggression: {suggested_min}
+ max_aggression: {suggested_max}
"""
        
        return EvolutionProposal(
            proposal_id=self._generate_proposal_id(),
            proposal_type=ProposalType.POLICY,
            description=f"Adjust aggression bounds: [{current_min}, {current_max}] → [{suggested_min}, {suggested_max}]",
            scope="policy",
            targets=["policy/governance.yaml"],
            diff=diff,
            risk_score=35,
            expected_benefit="More adaptive aggression policy",
            rollback_plan=f"Revert to [{current_min}, {current_max}]",
            rationale=rationale
        )
    
    def _propose_risk_threshold(
        self,
        current_threshold: int,
        suggested_threshold: int,
        rationale: str = ""
    ) -> Optional[EvolutionProposal]:
        """Create a risk threshold proposal."""
        diff = f"""
# Risk Threshold Adjustment
- risk_threshold: {current_threshold}
+ risk_threshold: {suggested_threshold}
"""
        
        return EvolutionProposal(
            proposal_id=self._generate_proposal_id(),
            proposal_type=ProposalType.POLICY,
            description=f"Adjust risk threshold from {current_threshold} to {suggested_threshold}",
            scope="policy",
            targets=["policy/evolution.yaml"],
            diff=diff,
            risk_score=40,
            expected_benefit="Adjusted risk tolerance",
            rollback_plan=f"Revert to {current_threshold}",
            rationale=rationale
        )
    
    def propose_from_analysis(
        self,
        analysis_type: str,
        analysis_data: Dict[str, Any]
    ) -> Optional[EvolutionProposal]:
        """
        Generate a proposal based on system analysis.
        
        Supported analysis types:
        - interval_optimization
        - threshold_optimization
        - aggression_tuning
        """
        proposal = None
        
        if analysis_type == "interval_optimization":
            current = analysis_data.get("current_interval", 3.0)
            avg_duration = analysis_data.get("avg_cycle_duration", 1.0)
            suggested = analysis_data.get("suggested_interval")
            
            # If suggested is provided directly, use it
            if suggested is not None and suggested != current:
                proposal = self._propose_interval_adjustment(
                    current, suggested,
                    rationale=analysis_data.get("rationale", f"Exploring interval optimization: {current} → {suggested}")
                )
            # Otherwise calculate from avg_duration
            elif current > avg_duration * 1.5:
                suggested = max(avg_duration * 1.2, 1.0)
                proposal = self._propose_interval_adjustment(
                    current, suggested,
                    rationale=f"Average cycle duration is {avg_duration:.1f}s, interval can be reduced"
                )
        
        elif analysis_type == "threshold_optimization":
            name = analysis_data.get("threshold_name", "unknown")
            current = analysis_data.get("current_value", 0)
            suggested = analysis_data.get("suggested_value", current)
            
            if current != suggested:
                proposal = self._propose_threshold_adjustment(
                    name, current, suggested,
                    rationale=analysis_data.get("rationale", "")
                )
        
        elif analysis_type == "aggression_tuning":
            current_min = analysis_data.get("current_min", 0.3)
            current_max = analysis_data.get("current_max", 1.0)
            suggested_min = analysis_data.get("suggested_min", current_min)
            suggested_max = analysis_data.get("suggested_max", current_max)
            
            if current_min != suggested_min or current_max != suggested_max:
                proposal = self._propose_aggression_bounds(
                    current_min, current_max,
                    suggested_min, suggested_max,
                    rationale=analysis_data.get("rationale", "")
                )
        
        # Validate and record if proposal was created
        if proposal:
            success, reason = self.ledger.record_proposal(proposal)
            if not success:
                logger.warning(f"Proposal rejected: {reason}")
                return None
            return proposal
        
        return None
    
    def get_pending_proposals(self) -> List[EvolutionProposal]:
        """Get all pending proposals."""
        return [
            p for p in self.ledger.proposals.values()
            if p.status == ProposalStatus.PENDING
        ]
    
    def get_approved_proposals(self) -> List[EvolutionProposal]:
        """Get all approved proposals awaiting execution."""
        return [
            p for p in self.ledger.proposals.values()
            if p.status == ProposalStatus.APPROVED
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proposer statistics."""
        return {
            "pending_count": len(self.get_pending_proposals()),
            "approved_count": len(self.get_approved_proposals()),
            "templates": {
                "config": list(self.config_templates.keys()),
                "policy": list(self.policy_templates.keys()),
            }
        }


# Singleton
_proposer_instance = None

def get_patch_proposer() -> PatchProposer:
    """Get the global PatchProposer instance."""
    global _proposer_instance
    if _proposer_instance is None:
        _proposer_instance = PatchProposer()
    return _proposer_instance
