from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math

@dataclass
class Situation:
    """Represents a situation or problem domain for analogy matching."""
    domain: str
    description: str
    structure: Dict[str, Any]
    solution: Optional[str] = None
    outcome: Optional[str] = None

@dataclass
class AnalogyMatch:
    """Represents a found analogy and its mapping to the current situation."""
    source_domain: str
    source_situation: Situation
    similarity_score: float
    structural_mapping: Dict[str, str]
    transferable_knowledge: str
    adapted_solution: Optional[str] = None

class AnalogicalReasoner:
    """Core module for reasoning by analogy from similar structural situations in different domains."""
    
    def __init__(self):
        # A mock knowledge base of abstract structures across different domains
        self.knowledge_base = [
            Situation(
                domain="Traffic Engineering",
                description="Traffic slow due to too many intersections in downtown",
                structure={"flow_type": "physical", "bottleneck": "intersection", "metric": "latency"},
                solution="Build bypass highways avoiding downtown center",
                outcome="Throughput increased by 300%"
            ),
            Situation(
                domain="Biology",
                description="Virus invading cell by binding to specific receptors",
                structure={"actor": "malicious_entity", "target": "system_core", "vector": "receptor_binding"},
                solution="Introduce decoy receptors to intercept the virus",
                outcome="Infection rate dropped by 90%"
            ),
            Situation(
                domain="Economics",
                description="Inflation rising due to excessive money supply competing for limited goods",
                structure={"demand": "high", "supply": "limited", "result": "resource_devaluation"},
                solution="Increase interest rates to reduce money velocity",
                outcome="Prices stabilized over 3 quarters"
            ),
            Situation(
                domain="Logistics",
                description="Warehouse workers spending too much time traveling between aisles",
                structure={"operation": "fetch", "bottleneck": "travel_distance", "metric": "efficiency"},
                solution="Group frequently bought items together near the packing station",
                outcome="Order picking speed doubled"
            )
        ]
        
        # NeuronFabric integration: source knowledge from learned neurons
        self._neuron_fabric = None
        self._event_bus = None
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            self._neuron_fabric = get_neuron_fabric()
            self._enrich_kb_from_neurons()
        except Exception:
            pass
        try:
            from unified_core.integration.event_bus import get_event_bus
            self._event_bus = get_event_bus()
        except Exception:
            pass

    def _enrich_kb_from_neurons(self):
        """Add learned situations from NeuronFabric's cognitive neurons."""
        if not self._neuron_fabric:
            return
        try:
            from unified_core.core.neuron_fabric import NeuronType
            cognitive_neurons = [
                n for n in self._neuron_fabric._neurons.values()
                if n.neuron_type == NeuronType.COGNITIVE and n.confidence > 0.6
            ]
            for neuron in cognitive_neurons[:20]:  # Top 20 by recency
                if any(kb.description == neuron.proposition for kb in self.knowledge_base):
                    continue
                self.knowledge_base.append(Situation(
                    domain=neuron.domain or "general",
                    description=neuron.proposition,
                    structure=self._extract_structure(neuron.proposition),
                    solution=None,
                    outcome=None
                ))
        except Exception:
            pass

    def _extract_structure(self, situation_description: str) -> Dict[str, Any]:
        """In a real AI system, use NLP to extract structural ontology. Here we use heuristics."""
        desc = situation_description.lower()
        struct = {}
        
        if "slow" in desc or "latency" in desc or "waiting" in desc:
            struct["metric"] = "latency"
        if "bottleneck" in desc or "block" in desc or "lock" in desc:
            struct["bottleneck"] = "contention_point"
        if "fetch" in desc or "retrieve" in desc or "read" in desc:
            struct["operation"] = "fetch"
        if "attack" in desc or "breach" in desc or "exploit" in desc:
            struct["actor"] = "malicious_entity"
        
        return struct

    def _structural_similarity(self, struct_a: Dict[str, Any], struct_b: Dict[str, Any]) -> float:
        """Calculate Jaccard-like similarity between two abstract structures."""
        keys_a = set(struct_a.keys())
        keys_b = set(struct_b.keys())
        
        if not keys_a or not keys_b:
            return 0.0
            
        common_keys = keys_a.intersection(keys_b)
        if not common_keys:
            return 0.0
            
        score = 0.0
        for k in common_keys:
            if struct_a[k] == struct_b[k]:
                score += 1.0 # Exact match
            else:
                score += 0.5 # Related concept
                
        return min(1.0, score / max(len(keys_a), len(keys_b)))

    def _create_mapping(self, source_struct: Dict[str, Any], target_struct: Dict[str, Any]) -> Dict[str, str]:
        """Map concepts from source domain to target domain."""
        mapping = {}
        # Simple heuristic mapping for demo
        for k_s, v_s in source_struct.items():
            for k_t, v_t in target_struct.items():
                if k_s == k_t:
                    mapping[v_s] = v_t
        return mapping

    def _adapt_solution(self, analogical_solution: str, mapping: Dict[str, str], target_domain: str) -> str:
        """Translate the solution into the target domain's terminology."""
        # VERY basic translation for demo purposes
        adapted = analogical_solution
        if target_domain == "Software Engineering":
            if "highway" in adapted.lower():
                adapted = adapted.replace("Build bypass highways", "Create fast-path/denormalized views")
            if "decoy" in adapted.lower():
                adapted = adapted.replace("Introduce decoy receptors", "Deploy honeypots")
            if "group frequently" in adapted.lower() or "items together" in adapted.lower():
                adapted = "Implement memory caching (Redis/Memcached) for hot data"
        return adapted

    def find_analogies(self, current_situation_desc: str, target_domain: str = "Software Engineering") -> List[AnalogyMatch]:
        """Find analogous situations in completely different domains to inspire lateral solutions."""
        
        current_structure = self._extract_structure(current_situation_desc)
        analogies = []

        for kb_sit in self.knowledge_base:
            similarity = self._structural_similarity(current_structure, kb_sit.structure)
            
            if similarity > 0.1: # Must have some structural overlap
                mapping = self._create_mapping(kb_sit.structure, current_structure)
                adapted = self._adapt_solution(kb_sit.solution, mapping, target_domain) if kb_sit.solution else None
                
                match = AnalogyMatch(
                    source_domain=kb_sit.domain,
                    source_situation=kb_sit,
                    similarity_score=similarity,
                    structural_mapping=mapping,
                    transferable_knowledge=f"Concept from {kb_sit.domain}: {kb_sit.solution or kb_sit.description}",
                    adapted_solution=adapted
                )
                analogies.append(match)

        result = sorted(analogies, key=lambda x: x.similarity_score, reverse=True)
        
        # Publish analogy event and store successful analogies as neurons
        if result and self._event_bus:
            try:
                from unified_core.integration.event_bus import EventPriority
                self._event_bus.publish_sync(
                    "analogy_found",
                    {
                        "query": current_situation_desc[:100],
                        "matches_count": len(result),
                        "top_domain": result[0].source_domain,
                        "top_score": result[0].similarity_score,
                    },
                    "AnalogicalReasoner",
                    EventPriority.LOW
                )
            except Exception:
                pass
        
        if result and self._neuron_fabric:
            try:
                from unified_core.core.neuron_fabric import NeuronType
                best = result[0]
                if best.similarity_score > 0.5 and best.adapted_solution:
                    self._neuron_fabric.create_neuron(
                        proposition=f"Analogy: {best.adapted_solution[:100]}",
                        neuron_type=NeuronType.COGNITIVE,
                        confidence=best.similarity_score,
                        domain="intelligence",
                        tags=["analogy", best.source_domain.lower().replace(" ", "_")],
                        metadata={"source_domain": best.source_domain, "query": current_situation_desc[:80]}
                    )
            except Exception:
                pass
        
        return result
