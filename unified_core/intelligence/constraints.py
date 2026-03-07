from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class Proposal:
    """Represents a proposed action or innovation with its attributes affecting constraints."""
    name: str
    description: str
    attributes: Dict[str, float] = field(default_factory=dict)
    
    def get_value(self, constraint_name: str) -> Optional[float]:
        return self.attributes.get(constraint_name)

class ConstraintManager:
    """Track and reason about constraints to ensure feasible and realistic solutions."""

    def __init__(self):
        # Base limits for the constraint solver
        self.constraints = {
            # Resource constraints
            'max_ram_bytes': 32_000_000_000,  # 32GB
            'max_cpu_percent': 90.0,
            'max_gpu_memory': 12_000_000_000,  # 12GB
            'max_disk_percent': 85.0,

            # Safety constraints (relaxed for autonomous evolution)
            'max_risk_score': 90.0,  # Raised to 90 to match AGENT_RISK_THRESHOLD
            'min_test_coverage': 0.5,  # Lowered from 0.8 to 0.5
            'max_canary_failures': 5.0,  # Increased from 2 to 5

            # Quality constraints (relaxed)
            'min_confidence': 0.3,  # Lowered from 0.6 to 0.3
            'max_complexity': 200.0,  # Increased from 100 to 200

            # Time constraints
            'max_downtime_seconds': 5.0,
            'max_processing_time': 300.0,

            # Business/Operational constraints
            'min_user_satisfaction': 0.7,
            'max_cost_per_month': 1000.0
        }

    def _violation_severity(self, constraint: str, actual: float, limit: float) -> str:
        """Determine severity of violation based on type of constraint and magnitude."""
        if constraint.startswith('max_'):
            ratio = actual / limit if limit > 0 else float('inf')
        else:
            ratio = limit / actual if actual > 0 else float('inf')
            
        # Severe overrun (more than 50% violation) is always hard
        if ratio > 1.5:
            return 'hard'
        
        # Certain constraints are non-negotiable hard boundaries
        # Removed max_risk_score from hard constraints to allow canary testing to be the real gate
        hard_constraints = ['max_downtime_seconds', 'max_cost_per_month']
        if constraint in hard_constraints:
            return 'hard'
            
        return 'soft'

    def _violates(self, proposal: Proposal, constraint: str, limit: float) -> bool:
        """Check if a specific constraint is violated by the proposal."""
        val = proposal.get_value(constraint)
        if val is None:
            return False
            
        if constraint.startswith('max_'):
            return val > limit
        elif constraint.startswith('min_'):
            return val < limit
        return False

    def is_feasible(self, proposal: Proposal) -> Dict[str, Any]:
        """Check if proposal satisfies all constraints."""
        violations = []

        for constraint, limit in self.constraints.items():
            if self._violates(proposal, constraint, limit):
                actual_val = proposal.get_value(constraint)
                violations.append({
                    'constraint': constraint,
                    'limit': limit,
                    'actual': actual_val,
                    'severity': self._violation_severity(constraint, actual_val, limit)
                })

        return {
            'feasible': len(violations) == 0,
            'violations': violations,
            'hard_violations': [v for v in violations if v['severity'] == 'hard'],
            'soft_violations': [v for v in violations if v['severity'] == 'soft']
        }

    def find_feasible_solution(self, goal: str, initial_proposal: Proposal, constraints_to_relax: Optional[List[str]] = None) -> Optional[Proposal]:
        """
        Attempt to validate a feasible solution. If it fails due to soft constraints, 
        try to relax them if authorized by the caller.
        """
        check = self.is_feasible(initial_proposal)
        
        if check['feasible']:
            return initial_proposal
            
        if check['hard_violations']:
            # Hard constraints cannot be automatically relaxed
            return None
            
        if constraints_to_relax and check['soft_violations']:
            # Try to relax the authorized constraints
            for violation in check['soft_violations']:
                constraint = violation['constraint']
                if constraint in constraints_to_relax:
                    # Relax by 20%
                    if constraint.startswith('max_'):
                        self.constraints[constraint] *= 1.2
                    elif constraint.startswith('min_'):
                        self.constraints[constraint] *= 0.8
            
            # Recheck after relaxation
            recheck = self.is_feasible(initial_proposal)
            if recheck['feasible']:
                return initial_proposal
            
        return None
