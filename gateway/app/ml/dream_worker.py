import asyncio
import logging
from typing import Any, Dict, Optional

from gateway.app.core.config import get_settings
try:
    from gateway.app.core.memory import memory
except ImportError:
    memory = None

logger = logging.getLogger("dream_worker")


class PriorityDreamScheduler:
    """
    Schedules dream tasks based on importance and failures.
    Priority: High (Critical Failures) > Medium (Low Confidence) > Low (General Patterns)
    """

    def __init__(self):
        self.high_priority = []
        self.medium_priority = []
        self.low_priority = []
        self.settings = get_settings()

    async def analyze_and_schedule(self):
        """Analyze memory and populate priority queues."""
        logger.info("DreamScheduler: Analyzing memory for learning opportunities...")

        # 1. Find Critical Failures (High Priority)
        # Search for records where verified=False or outcome contains 'error' or 'failed'
        failures = memory.find_similar(query_text="failed error exception", top_k=10)
        self.high_priority = [f for f in failures if f.get("verified") == False]

        # 2. Find Low Performance / Patterns (Medium/Low Priority)
        # Random sampling of recent tasks for general refinement
        recent = memory.find_similar(query_text="task accomplishment", top_k=20)
        self.medium_priority = recent[:5]
        self.low_priority = recent[5:]

        logger.info(
            f"Scheduled: {len(self.high_priority)} High, {len(self.medium_priority)} Medium, {len(self.low_priority)} Low tasks."
        )

    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the highest priority task available."""
        if self.high_priority:
            return self.high_priority.pop(0)
        if self.medium_priority:
            return self.medium_priority.pop(0)
        if self.low_priority:
            return self.low_priority.pop(0)
        return None


class DreamWorker:
    """
    Main background worker for the Dream Cycle.
    Uses a Teacher model (Cloud/DeepSeek) to refine Student trajectories.
    """

    def __init__(self, scheduler: PriorityDreamScheduler):
        self.scheduler = scheduler
        self.teacher = None  # Lazy load
        self.is_active = False

    async def start_cycle(self):
        """Run a full dream cycle."""
        self.is_active = True
        logger.info("💭 DreamWorker: Entering REM cycle (Deep Learning)...")

        if self.teacher is None:
            # For dreams, we always prefer the strongest available model (Teacher)
            from gateway.app.llm.brain_factory import create_brain

            self.teacher = create_brain()  # Usually CloudClient/DeepSeek if configured

        await self.scheduler.analyze_and_schedule()

        while self.is_active:
            task_data = await self.scheduler.get_next_task()
            if not task_data:
                logger.info("DreamWorker: No more tasks in queue. Cycle complete.")
                break

            await self._process_dream(task_data)
            await asyncio.sleep(2)  # Breathing room

        self.is_active = False
        logger.info("💭 DreamWorker: Waking up. Models refined.")

    async def _process_dream(self, task_data: Dict[str, Any]):
        """
        'Dream' about a task: Re-imagine the trajectory using the teacher.
        """
        goal = task_data.get("content", "Unknown Goal")
        logger.info(f"Dreaming about: {goal[:50]}...")

        prompt = (
            f"RE-IMAGINE TASK: {goal}\n\n"
            "This task previously failed or was inefficient. "
            "As a Teacher Model, provide the perfect step-by-step reasoning (Chain of Thought) "
            "and final answer to solve this correctly."
        )

        try:
            # 1. Generate perfect trajectory via Teacher
            improved_trajectory = self.teacher.generate(prompt, max_new_tokens=512)

            # 2. Store the improved version as 'verified' memory
            memory.add_experience(
                goal=goal,
                plan_id="dream_refined_" + task_data.get("plan_id", "unknown"),
                outcome=improved_trajectory,
                source="dream_mode",
                verified=True,
            )

            logger.info(f"✅ Dream Refined: {goal[:30]}... stored in semantic memory.")

        except Exception as e:
            logger.error(f"Dream process failed: {e}")


# Service functions
async def run_dream_cycle():
    scheduler = PriorityDreamScheduler()
    worker = DreamWorker(scheduler)
    await worker.start_cycle()


if __name__ == "__main__":
    # Allow manual triggering for testing
    pass

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_dream_cycle())
