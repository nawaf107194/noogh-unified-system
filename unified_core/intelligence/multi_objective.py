"""
Multi-Objective Optimization Module
Part of NOOGH Cognitive Enhancement (Phase 3 - Advanced #2 - FINAL)

This module implements decision-making when faced with conflicting objectives by:
1. Normalizing diverse criteria (e.g., speed vs. cost vs. security).
2. Calculating Pareto Dominance to eliminate strictly inferior options.
3. Returning the Pareto Frontier (the set of optimal trade-offs).
4. Applying a weighted sum model if the system has explicit priorities.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("unified_core.intelligence.multi_objective")

@dataclass
class Objective:
    """Defines an objective, whether we want to maximize or minimize it, and its weight."""
    name: str
    minimize: bool
    weight: float = 1.0  # Used only if a single best answer is required


@dataclass
class MultiObjectiveOption:
    """An option with specific values for various objectives."""
    name: str
    scores: Dict[str, float]  # e.g., {'cost': 1500, 'speed': 200, 'security': 90}
    normalized_scores: Dict[str, float] = field(default_factory=dict)
    
    def dominates(self, other: 'MultiObjectiveOption', objectives: List[Objective]) -> bool:
        """
        Returns True if this option is strictly better or equal to the other option in ALL objectives, 
        AND strictly better in at least ONE objective. (Pareto Dominance)
        """
        strictly_better_in_one = False
        
        for obj in objectives:
            val_self = self.scores.get(obj.name, 0.0)
            val_other = other.scores.get(obj.name, 0.0)
            
            # Check if self is worse
            is_worse = (val_self > val_other) if obj.minimize else (val_self < val_other)
            if is_worse:
                return False  # Cannot dominate if worse in anything
                
            # Check if self is strictly better
            is_better = (val_self < val_other) if obj.minimize else (val_self > val_other)
            if is_better:
                strictly_better_in_one = True
                
        return strictly_better_in_one


class MultiObjectiveOptimizer:
    """Analyze trade-offs and find Pareto optimal solutions."""

    def __init__(self, objectives: List[Objective]):
        self.objectives = objectives

    def find_pareto_frontier(self, options: List[MultiObjectiveOption]) -> List[MultiObjectiveOption]:
        """Returns the set of options that are not dominated by any other option."""
        logger.info(f"Calculating Pareto Frontier for {len(options)} options...")
        pareto_front = []
        
        for i, opt1 in enumerate(options):
            is_dominated = False
            for j, opt2 in enumerate(options):
                if i != j and opt2.dominates(opt1, self.objectives):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append(opt1)
                
        return pareto_front

    def normalize_scores(self, options: List[MultiObjectiveOption]):
        """Normalizes all objective scores between 0.0 and 1.0 based on min/max of the set."""
        for obj in self.objectives:
            vals = [opt.scores.get(obj.name, 0.0) for opt in options]
            min_val, max_val = min(vals), max(vals)
            range_val = max_val -min_val
            
            for opt in options:
                val = opt.scores.get(obj.name, 0.0)
                if range_val == 0:
                    opt.normalized_scores[obj.name] = 1.0  # Avoid division by zero
                else:
                    if obj.minimize:
                        # If minimizing, lower is better (max_val -> 0.0, min_val -> 1.0)
                        opt.normalized_scores[obj.name] = (max_val - val) / range_val
                    else:
                        # If maximizing, higher is better (max_val -> 1.0, min_val -> 0.0)
                        opt.normalized_scores[obj.name] = (val - min_val) / range_val

    def select_best_weighted(self, options: List[MultiObjectiveOption]) -> MultiObjectiveOption:
        """Applies weights to normalized scores to pick a single winner."""
        self.normalize_scores(options)
        
        best_option = None
        highest_score = -float('inf')
        
        for opt in options:
            total_score = 0.0
            for obj in self.objectives:
                total_score += opt.normalized_scores.get(obj.name, 0) * obj.weight
                
            # Store the computed overall score temporarily for tracking
            opt.normalized_scores['_weighted_total'] = total_score 
            
            if total_score > highest_score:
                highest_score = total_score
                best_option = opt
                
        return best_option

    def calculate_tradeoffs(self, opt_a: MultiObjectiveOption, opt_b: MultiObjectiveOption) -> Dict[str, Any]:
        """Provides a human-readable explanation of what you gain and lose by picking A instead of B."""
        gains = []
        losses = []
        
        for obj in self.objectives:
            val_a = opt_a.scores.get(obj.name, 0)
            val_b = opt_b.scores.get(obj.name, 0)
            diff = abs(val_a - val_b)
            
            if val_a == val_b:
                continue
                
            a_is_better = (val_a < val_b) if obj.minimize else (val_a > val_b)
            
            desc = f"{diff} units of {obj.name} (A: {val_a}, B: {val_b})"
            if a_is_better:
                gains.append(desc)
            else:
                losses.append(desc)
                
        return {
            "choosing_A_instead_of_B_gains": gains,
            "choosing_A_instead_of_B_loses": losses
        }
