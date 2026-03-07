"""
NOOGH Agent-to-Agent Learning
================================
Knowledge transfer between agents via the NeuronFabric.

When an agent succeeds at a task, it can:
1. Record the successful pattern as a neuron
2. Share it with other agents via the MessageBus
3. Other agents can query these patterns for similar tasks

This creates a collective intelligence where each agent
benefits from the experiences of all others.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("unified_core.agent_learning")


class AgentLearningHub:
    """
    Central hub for agent-to-agent knowledge transfer.
    
    Uses NeuronFabric as the shared memory and MessageBus for notifications.
    """
    
    def __init__(self):
        self._neuron_fabric = None
        self._message_bus = None
        self._knowledge_log: List[Dict] = []
        self._max_log = 200
        
        # Stats
        self.total_shared = 0
        self.total_consumed = 0
        
        logger.info("✅ AgentLearningHub initialized")
    
    def _get_fabric(self):
        if self._neuron_fabric is None:
            try:
                from unified_core.core.neuron_fabric import NeuronFabric
                self._neuron_fabric = NeuronFabric()
            except Exception as e:
                logger.debug(f"NeuronFabric unavailable: {e}")
        return self._neuron_fabric
    
    def _get_bus(self):
        if self._message_bus is None:
            try:
                from unified_core.orchestration.message_bus import get_message_bus
                self._message_bus = get_message_bus()
            except Exception as e:
                logger.debug(f"MessageBus unavailable: {e}")
        return self._message_bus
    
    def share_knowledge(
        self,
        agent_role: str,
        knowledge_type: str,
        content: str,
        context: Dict[str, Any] = None,
        confidence: float = 0.7,
    ) -> Optional[str]:
        """
        Share a piece of knowledge from one agent to the collective.
        
        Args:
            agent_role: Which agent is sharing (e.g., "health_monitor")
            knowledge_type: Type of knowledge (e.g., "pattern", "warning", "solution")
            content: The knowledge content
            context: Additional context
            confidence: How confident is this knowledge (0-1)
        
        Returns:
            neuron_id if stored, None if failed
        """
        fabric = self._get_fabric()
        if not fabric:
            logger.debug("Cannot share: NeuronFabric unavailable")
            return None
        
        # Create a neuron with tagged metadata
        neuron_data = {
            "source_agent": agent_role,
            "knowledge_type": knowledge_type,
            "content": content,
            "context": context or {},
            "confidence": confidence,
            "shared_at": time.time(),
            "tag": f"agent_knowledge:{agent_role}",
        }
        
        try:
            # Store in NeuronFabric
            neuron_id = fabric.learn_from_outcome(
                query=f"agent:{agent_role} {knowledge_type}: {content[:100]}",
                response=content,
                success=True,
                context=neuron_data,
            )
            
            self.total_shared += 1
            
            # Log
            self._knowledge_log.append({
                "action": "share",
                "agent": agent_role,
                "type": knowledge_type,
                "content_preview": content[:100],
                "timestamp": time.time(),
            })
            if len(self._knowledge_log) > self._max_log:
                self._knowledge_log.pop(0)
            
            logger.info(f"📤 {agent_role} shared knowledge: {knowledge_type} ({content[:50]}...)")
            
            # Notify other agents via MessageBus
            asyncio.ensure_future(self._notify_agents(agent_role, knowledge_type, content[:200]))
            
            return neuron_id
            
        except Exception as e:
            logger.debug(f"Knowledge sharing failed: {e}")
            return None
    
    def query_knowledge(
        self,
        query: str,
        requesting_agent: str = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Query the shared knowledge base.
        
        An agent can ask: "What do other agents know about X?"
        Returns relevant knowledge entries sorted by relevance.
        """
        fabric = self._get_fabric()
        if not fabric:
            return []
        
        try:
            # Query NeuronFabric
            results = fabric.activate_by_query(
                query=f"agent_knowledge {query}",
                top_k=max_results,
            )
            
            if results:
                self.total_consumed += 1
                logger.debug(f"📥 {requesting_agent or '?'} queried: '{query}' → {len(results)} results")
            
            return results or []
            
        except Exception as e:
            logger.debug(f"Knowledge query failed: {e}")
            return []
    
    async def _notify_agents(self, source: str, knowledge_type: str, preview: str):
        """Notify other agents about new shared knowledge."""
        bus = self._get_bus()
        if not bus:
            return
        
        try:
            from unified_core.orchestration.messages import MessageEnvelope, MessageType, RiskLevel
            
            msg = MessageEnvelope(
                sender=f"learning_hub",
                receiver="event:knowledge_shared",
                type=MessageType.EVENT,
                risk=RiskLevel.MINIMAL,
                payload={
                    "source_agent": source,
                    "knowledge_type": knowledge_type,
                    "preview": preview,
                    "timestamp": time.time(),
                },
            )
            await bus.publish(msg)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_shared": self.total_shared,
            "total_consumed": self.total_consumed,
            "log_size": len(self._knowledge_log),
            "recent_shares": [
                entry for entry in self._knowledge_log[-5:]
                if entry["action"] == "share"
            ],
        }


# Singleton
_hub_instance: Optional[AgentLearningHub] = None

def get_learning_hub() -> AgentLearningHub:
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = AgentLearningHub()
    return _hub_instance
