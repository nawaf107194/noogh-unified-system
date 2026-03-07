"""
WorldModel Initialization - Foundational Beliefs

This module seeds the WorldModel with foundational beliefs about:
- System capabilities
- Architectural constraints
- Operational boundaries

These beliefs form the basis for genuine decision-making.
Once falsified, they remain falsified forever.
"""

import logging
from typing import Dict, List

logger = logging.getLogger("unified_core.core.world_init")


# Foundational beliefs about the system
FOUNDATIONAL_BELIEFS = [
    # Architectural beliefs
    ("System operates with centralized decision authority", 0.95),
    ("State transitions are irreversible", 0.99),
    ("Memory constraints are coercive, not advisory", 0.95),
    ("Failures produce permanent scars", 0.99),
    
    # Capability beliefs
    ("System can process natural language queries", 0.85),
    ("System can store and retrieve data", 0.90),
    ("System can audit code for security vulnerabilities", 0.85),
    ("System can monitor resource utilization", 0.80),
    
    # Operational beliefs
    ("Database connections may fail under load", 0.6),
    ("GPU resources are limited and shared", 0.7),
    ("External services may be unavailable", 0.5),
    ("User inputs may contain malicious content", 0.4),
    
    # Self-knowledge beliefs
    ("I am not fully autonomous", 0.95),
    ("My predictions may be wrong", 0.8),
    ("I cannot access resources outside allowed roots", 0.99),
    ("My decisions have consequences I cannot undo", 0.99),
    
    # Spatial/Project beliefs (Phase 15 Addition)
    ("I am part of a larger project hierarchy beyond /src", 0.90),
    ("The project root directory contains critical backups and data partitions", 0.85),
    ("My spatial awareness determines my operational context", 0.95),
]


async def seed_world_model(world_model) -> List[Dict]:
    """
    Seed the WorldModel with foundational beliefs (Async).
    
    Returns list of created beliefs.
    """
    created_beliefs = []
    
    for proposition, confidence in FOUNDATIONAL_BELIEFS:
        try:
            belief = await world_model.add_belief(proposition, initial_confidence=confidence)
            created_beliefs.append({
                "belief_id": belief.belief_id,
                "proposition": proposition,
                "confidence": confidence
            })
            logger.info(f"Seeded belief: {proposition[:40]}... (conf={confidence})")
        except Exception as e:
            logger.error(f"Failed to seed belief '{proposition}': {e}")
    
    logger.info(f"WorldModel seeded with {len(created_beliefs)} foundational beliefs")
    return created_beliefs


async def initialize_ai_core_knowledge(bridge) -> Dict:
    """
    Initialize the AI core with foundational knowledge (Async).
    
    This should be called after bridge initialization to
    populate the WorldModel with initial beliefs.
    """
    if not hasattr(bridge, '_world_model') or not bridge._world_model:
        return {"success": False, "error": "WorldModel not available"}
    
    beliefs = await seed_world_model(bridge._world_model)
    
    # Generate initial goals based on beliefs (Async)
    if hasattr(bridge, '_gravity_well') and bridge._gravity_well:
        initial_goals = await bridge._gravity_well.generate_goals()
        return {
            "success": True,
            "beliefs_seeded": len(beliefs),
            "goals_generated": len(initial_goals)
        }
    
    return {
        "success": True,
        "beliefs_seeded": len(beliefs),
        "goals_generated": 0
    }
