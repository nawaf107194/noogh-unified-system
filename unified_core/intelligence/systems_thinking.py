from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class SystemNode:
    """A component in the system (e.g., 'Database Cache', 'User Load', 'Memory')."""
    name: str
    description: str
    value: float  # Current state/level (e.g., 85.0 for 85% full)

@dataclass
class CausalLink:
    """A connection showing how one node influences another."""
    source: str
    target: str
    polarity: int  # +1 (same direction), -1 (opposite direction)
    strength: float # 0.0 to 1.0 multiplier of influence
    delay: bool = False # Does the effect happen immediately or over time?

@dataclass
class FeedbackLoop:
    """A full cycle of connections creating a feedback structure."""
    nodes: List[str]
    loop_type: str  # 'Reinforcing' (Positive/Exponential) or 'Balancing' (Negative/Stabilizing)
    significance: float # How strongly this loop dominates the system behavior

class SystemsThinker:
    """Advanced module for holistic system reasoning, feedback loops, and emergence detection."""
    
    def __init__(self):
        self.nodes: Dict[str, SystemNode] = {}
        self.links: List[CausalLink] = []

    def load_system_model(self, nodes: List[SystemNode], links: List[CausalLink]):
        """Load the components and connections for a specific domain model."""
        self.nodes = {n.name: n for n in nodes}
        self.links = links

    def _find_paths(self, start: str, current: str, visited: set, path: List[str], loops: List[List[str]]):
        """Depth-First Search (DFS) to find closed loops in the causal graph."""
        visited.add(current)
        path.append(current)
        
        # Get all outgoing links from the current node
        outgoing_links = [link for link in self.links if link.source == current]
        
        for link in outgoing_links:
            next_node = link.target
            if next_node == start and len(path) > 1:
                # We found a loop back to the start
                loops.append(list(path))
            elif next_node not in visited:
                self._find_paths(start, next_node, visited.copy(), list(path), loops)

    def detect_feedback_loops(self) -> List[FeedbackLoop]:
        """Discover all cyclical feedback loops in the system."""
        all_loops = []
        recorded_loop_sets = set() # To prevent duplicate A->B->A and B->A->B
        
        for node_name in self.nodes:
            loops_from_node = []
            self._find_paths(node_name, node_name, set(), [], loops_from_node)
            
            for loop_path in loops_from_node:
                # Create a canonical representation of the loop to check for duplicates
                canon = frozenset(loop_path)
                if canon not in recorded_loop_sets:
                    recorded_loop_sets.add(canon)
                    
                    # Calculate loop polarity
                    # Multiply the polarities of all links in the loop: 
                    # Even number of negative links = Reinforcing (+)
                    # Odd number of negative links = Balancing (-)
                    net_polarity = 1
                    strength_prod = 1.0
                    for i in range(len(loop_path)):
                        source = loop_path[i]
                        target = loop_path[(i + 1) % len(loop_path)]
                        # Find the specific link
                        for link in self.links:
                            if link.source == source and link.target == target:
                                net_polarity *= link.polarity
                                strength_prod *= link.strength
                                break
                    
                    loop_type = 'Reinforcing (❄️ Snowball/Exponential)' if net_polarity > 0 else 'Balancing (⚖️ Stabilizing)'
                    all_loops.append(FeedbackLoop(
                        nodes=loop_path,
                        loop_type=loop_type,
                        significance=strength_prod * len(loop_path) # Heuristic significance
                    ))
        return sorted(all_loops, key=lambda x: x.significance, reverse=True)

    def identify_leverage_points(self) -> List[Dict[str, Any]]:
        """
        Identify nodes with disproportionate influence over the system.
        A high leverage point is a node that:
        1. Sits on a highly significant Reinforcing loop (can break a vicious cycle or start a virtuous one)
        2. Has high out-degree (influences many things) relative to its in-degree
        """
        loops = self.detect_feedback_loops()
        leverage_scores = {name: 0.0 for name in self.nodes}
        
        # 1. Loop involvement scores
        for loop in loops:
            multiplier = 2.0 if 'Reinforcing' in loop.loop_type else 1.0
            for node in loop.nodes:
                leverage_scores[node] += loop.significance * multiplier
                
        # 2. Influence ratio (Out vs In)
        for name in self.nodes:
            out_strength = sum(l.strength for l in self.links if l.source == name)
            in_strength = sum(l.strength for l in self.links if l.target == name)
            
            # Nodes that push heavily on the system but aren't pushed as much
            # are excellent levers of control
            if in_strength > 0:
                ratio = out_strength / in_strength
                leverage_scores[name] *= max(1.0, ratio) # Boost score significantly
            elif out_strength > 0:
                leverage_scores[name] *= 3.0 # Pure origin nodes are strong levers
                
        # Format results
        results = [
            {'node': name, 'leverage_score': score, 'reasoning': "Highly central to vicious/virtuous cycles" if score > 5.0 else "Minor systemic influence"}
            for name, score in leverage_scores.items()
        ]
        
        return sorted(results, key=lambda x: x['leverage_score'], reverse=True)
