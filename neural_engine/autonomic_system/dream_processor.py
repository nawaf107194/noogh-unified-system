"""
Dream Mode - Autonomous learning during idle periods.
Mimics biological sleep processing to consolidate memories and discover patterns.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DreamProcessor:
    """
    Processes memories during idle time to:
    - Consolidate important memories
    - Discover new patterns
    - Strengthen neural connections
    - Optimize knowledge models
    """

    def __init__(self, memory_manager, recall_engine, reasoning_engine):
        self.memory = memory_manager  # Now uses MemoryManager instead of MemoryConsolidator
        self.recall = recall_engine
        self.reasoning = reasoning_engine
        self.is_dreaming = False
        self.dream_cycles = 0
        self.insights_discovered = []

        logger.info("DreamProcessor initialized with triple-store memory")

    async def start_dreaming(self, duration_minutes: int = 5):
        """
        Start a dream cycle.

        Args:
            duration_minutes: How long to dream
        """
        if self.is_dreaming:
            logger.warning("Already dreaming")
            return

        self.is_dreaming = True
        logger.info(f"💭 Entering dream mode for {duration_minutes} minutes...")

        try:
            end_time = datetime.now() + timedelta(minutes=duration_minutes)

            while datetime.now() < end_time and self.is_dreaming:
                await self._dream_cycle()
                await asyncio.sleep(10)  # Short pause between cycles

        finally:
            self.is_dreaming = False
            logger.info(f"💭 Dream mode ended. Cycles: {self.dream_cycles}, Insights: {len(self.insights_discovered)}")

    async def _dream_cycle(self):
        """Execute one dream cycle."""
        self.dream_cycles += 1
        logger.debug(f"Dream cycle {self.dream_cycles} starting...")

        # 1. Smart Recall (Prioritize Errors & Tasks)
        memories = await self._recall_smart_memories(n=15)

        if not memories:
            logger.debug("No memories to process")
            return

        # 2. Find patterns
        patterns = await self._find_patterns(memories)

        # 3. Generate structured insights
        insights = await self._generate_insights(patterns)

        # 4. Store new knowledge
        if insights:
            await self._store_insights(insights)
            self.insights_discovered.extend(insights)

    async def _recall_smart_memories(self, n: int = 15) -> List[Dict[str, Any]]:
        """Recall memories prioritizing errors and tasks."""
        memories = []
        try:
            # 1. Fetch recent errors (Priority 1)
            # MemoryManager is sync, so we thread it to avoid blocking loop
            import asyncio
            errors = await asyncio.to_thread(self.memory.recall_by_type, "system_error", n=5)
            
            # 2. Fetch incomplete/active tasks (Priority 2)
            tasks = await asyncio.to_thread(self.memory.recall_by_type, "task_item", n=5)
            
            # 3. Fetch recent general memories (Context)
            recent = await asyncio.to_thread(self.memory.recall_recent, n=10)

            # Combine and deduplicate by ID
            seen_ids = set()
            for mem in errors + tasks + recent:
                if mem["id"] not in seen_ids:
                    memories.append(mem)
                    seen_ids.add(mem["id"])

            # Limit to n
            return memories[:n]

        except Exception as e:
            logger.error(f"Error in smart recall: {e}")
            return []

    async def _find_patterns(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze memories to find patterns.

        Returns:
            List of discovered patterns
        """
        patterns = []

        # Extract content from memories
        contents = [m.get("content", "") for m in memories]

        # Find common themes
        themes = await self._extract_themes(contents)

        # Find temporal patterns
        temporal = await self._find_temporal_patterns(memories)

        # Find semantic connections
        connections = await self._find_semantic_connections(contents)

        if themes:
            patterns.append({"type": "thematic", "data": themes, "confidence": 0.4})  # Lowered from 0.7

        if temporal:
            patterns.append({"type": "temporal", "data": temporal, "confidence": 0.3})  # Lowered from 0.6

        if connections:
            patterns.append({"type": "semantic", "data": connections, "confidence": 0.4})  # Lowered from 0.8

        return patterns

    async def _extract_themes(self, contents: List[str]) -> Dict[str, Any]:
        """Extract common themes from content."""
        # Simple keyword extraction
        all_words = []
        for content in contents:
            words = content.lower().split()
            all_words.extend(words)

        # Count frequencies
        from collections import Counter

        word_freq = Counter(all_words)

        # Get top themes
        common_words = word_freq.most_common(5)

        if common_words:
            return {"keywords": [word for word, _ in common_words], "frequencies": dict(common_words)}

        return {}

    async def _find_temporal_patterns(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find temporal patterns in memories."""
        # Analyze timestamps
        timestamps = []
        for m in memories:
            ts = m.get("metadata", {}).get("timestamp")
            if ts:
                timestamps.append(ts)

        if len(timestamps) > 1:
            return {"count": len(timestamps), "span": "recent"}

        return {}

    async def _find_semantic_connections(self, contents: List[str]) -> List[Dict[str, Any]]:
        """Find semantic connections between memories."""
        connections = []

        # Compare each pair
        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                similarity = self._calculate_similarity(contents[i], contents[j])

                if similarity > 0.3:  # Lowered from 0.5
                    connections.append({"memory_1": i, "memory_2": j, "similarity": similarity})

        return connections

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity calculation."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Use Sorensen-Dice coefficient for better sensitivity on short strings
        intersection = words1.intersection(words2)
        inter = len(intersection)
        return (2.0 * inter) / (len(words1) + len(words2)) if (words1 or words2) else 0.0

    async def _generate_insights(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate structured insights from discovered patterns.

        Returns:
            List of insight dictionaries
        """
        insights = []

        for pattern in patterns:
            # Calculate pattern strength
            confidence = pattern.get("confidence", 0.5)

            if pattern["type"] == "thematic":
                keywords = pattern["data"].get("keywords", [])
                if keywords:
                    insights.append(
                        {
                            "pattern_type": "Thematic",
                            "content": f"Recurring theme detected: {', '.join(keywords[:3])}",
                            "confidence": confidence,
                        }
                    )

            elif pattern["type"] == "semantic":
                connections = pattern["data"]
                if len(connections) > 2:
                    insights.append(
                        {
                            "pattern_type": "Semantic",
                            "content": f"Found {len(connections)} semantic connections between memories",
                            "confidence": confidence,
                        }
                    )

            elif pattern["type"] == "temporal":
                insights.append(
                    {
                        "pattern_type": "Temporal",
                        "content": "Temporal clustering detected in recent memories",
                        "confidence": confidence,
                    }
                )

        return insights

    async def _store_insights(self, insights: List[Dict[str, Any]]):
        """Store discovered structured insights (as dreams, not facts)."""
        for insight in insights:
            try:
                # Store in DREAMS collection, not facts
                self.memory.store_dream(
                    content=f"[DREAM INSIGHT] [{insight['pattern_type']}] {insight['content']}",
                    confidence=insight["confidence"],
                    metadata={
                        "dream_cycle": self.dream_cycles,
                        "timestamp": datetime.now().isoformat(),
                        "pattern_type": insight["pattern_type"],
                    },
                )
                logger.info(f"💡 Dream Insight ({insight['pattern_type']}): {insight['content']}")
            except Exception as e:
                logger.error(f"Error storing insight: {e}")

    def stop_dreaming(self):
        """Stop the dream cycle."""
        self.is_dreaming = False
        logger.info("Dream mode stopping...")

    def get_stats(self) -> Dict[str, Any]:
        """Get dream statistics."""
        return {
            "is_dreaming": self.is_dreaming,
            "total_cycles": self.dream_cycles,
            "insights_discovered": len(self.insights_discovered),
            "recent_insights": self.insights_discovered[-5:] if self.insights_discovered else [],
        }


class DreamScheduler:
    """
    Schedules dream cycles during idle periods.
    """

    def __init__(self, dream_processor, idle_threshold_minutes: int = 30):
        self.dream_processor = dream_processor
        self.idle_threshold = idle_threshold_minutes
        self.last_activity = datetime.now()
        self.auto_dream_enabled = True

        logger.info(f"DreamScheduler initialized (idle threshold: {idle_threshold_minutes}m)")

    def record_activity(self):
        """Record user activity."""
        self.last_activity = datetime.now()

    async def check_and_dream(self):
        """Check if idle and start dreaming if needed."""
        if not self.auto_dream_enabled:
            return

        idle_time = datetime.now() - self.last_activity

        if idle_time > timedelta(minutes=self.idle_threshold):
            if not self.dream_processor.is_dreaming:
                logger.info(f"System idle for {idle_time.seconds // 60}m, starting dream mode...")
                await self.dream_processor.start_dreaming(duration_minutes=5)

    async def run_scheduler(self):
        """Run the scheduler loop."""
        while True:
            await self.check_and_dream()
            await asyncio.sleep(60)  # Check every minute
