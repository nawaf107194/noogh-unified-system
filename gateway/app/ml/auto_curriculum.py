"""
NOOGH Auto-Curriculum Learning System
Decides WHAT to train on based on:
- Self-analysis of capabilities
- User interaction patterns
- Task failure analysis
- Knowledge gaps detection
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from neural_engine.autonomic_system.self_governor import get_self_governing_agent
from neural_engine.autonomic_system.unified_agent import get_unified_agent
from gateway.app.ml.intelligent_training import TrainingConfig, get_training_engine


@dataclass
class LearningNeed:
    """A detected learning need"""

    need_id: str
    category: str  # code, language, math, reasoning, etc
    description: str
    evidence: List[str]  # Why we need this
    priority: float  # 0-1
    suggested_dataset: str
    suggested_model: str
    confidence: float


@dataclass
class TrainingDecision:
    """Decision to train on something"""

    decision_id: str
    learning_need: LearningNeed
    training_config: TrainingConfig
    rationale: str
    expected_improvement: str
    approved: bool
    timestamp: datetime


class AutoCurriculumLearner:
    """
    Autonomous curriculum learning - NOOGH decides what to learn.

    Process:
    1. Analyze current capabilities
    2. Detect knowledge gaps
    3. Analyze user interactions (what fails?)
    4. Prioritize learning needs
    5. Select optimal training data
    6. Decide when to train
    7. Execute training
    8. Evaluate improvement
    """

    def __init__(self):
        """Initialize auto-curriculum learner"""
        self.agent = get_unified_agent()
        self.self_governor = get_self_governing_agent()
        self.training_engine = get_training_engine()

        # Track interactions and failures
        self.interaction_history: List[Dict] = []
        self.failure_patterns: Dict[str, int] = defaultdict(int)
        self.knowledge_gaps: List[LearningNeed] = []
        self.training_decisions: List[TrainingDecision] = []

        print("🎓 Auto-Curriculum Learner initialized")
        print("   ✅ Can detect knowledge gaps")
        print("   ✅ Can prioritize learning needs")
        print("   ✅ Can decide what to train")

    async def analyze_learning_needs(self) -> List[LearningNeed]:
        """
        Analyze what NOOGH needs to learn.

        Sources:
        1. Self-analysis (what am I weak at?)
        2. Interaction history (what do users ask?)
        3. Failure patterns (what fails often?)
        4. Task analysis (what's coming?)
        """
        print(f"\n{'='*80}")
        print("🔍 ANALYZING LEARNING NEEDS")
        print(f"{'='*80}\n")

        needs = []

        # Source 1: Self-analysis
        print("1️⃣ Self-analysis for weaknesses...")
        self_needs = await self._analyze_self_weaknesses()
        needs.extend(self_needs)

        # Source 2: User interaction patterns
        print("\n2️⃣ Analyzing user interaction patterns...")
        interaction_needs = await self._analyze_interaction_patterns()
        needs.extend(interaction_needs)

        # Source 3: Failure analysis
        print("\n3️⃣ Analyzing failure patterns...")
        failure_needs = await self._analyze_failure_patterns()
        needs.extend(failure_needs)

        # Source 4: Future task analysis
        print("\n4️⃣ Analyzing future task requirements...")
        future_needs = await self._analyze_future_needs()
        needs.extend(future_needs)

        # Source 5: Weekly User-Defined Curriculum (Highest Priority)
        print("\n5️⃣ Applying Weekly Curriculum (Thinking, Agents, AI)...")
        schedule_needs = await self._analyze_weekly_schedule()
        needs.extend(schedule_needs)

        # Source 6: Synthetic Dream Data
        print("\n6️⃣ Checking for Synthetic Dreams...")
        dream_needs = await self._analyze_dream_data()
        needs.extend(dream_needs)

        # Prioritize
        print("\n7️⃣ Prioritizing learning needs...")
        needs = self._prioritize_needs(needs)

        self.knowledge_gaps = needs

        print(f"\n{'='*80}")
        print("✅ LEARNING NEEDS IDENTIFIED")
        print(f"   Total needs: {len(needs)}")
        print(f"   High priority: {len([n for n in needs if n.priority > 0.7])}")
        print(f"{'='*80}\n")

        return needs

    async def _analyze_self_weaknesses(self) -> List[LearningNeed]:
        """Analyze self to find weaknesses"""
        analysis = await self.self_governor.analyze_self()

        needs = []

        for i, weakness in enumerate(analysis.weaknesses[:5]):
            # Map weakness to training need
            if "tracing" in weakness.lower():
                need = LearningNeed(
                    need_id=f"self_weak_{i}",
                    category="infrastructure",
                    description="Learn distributed tracing patterns",
                    evidence=[weakness],
                    priority=0.6,
                    suggested_dataset="code_search_net",
                    suggested_model="Salesforce/codegen-350M-mono",
                    confidence=0.8,
                )
                needs.append(need)

            elif "caching" in weakness.lower():
                need = LearningNeed(
                    need_id=f"self_weak_{i}",
                    category="optimization",
                    description="Learn caching strategies",
                    evidence=[weakness],
                    priority=0.8,
                    suggested_dataset="stackoverflow",
                    suggested_model="gpt2",
                    confidence=0.85,
                )
                needs.append(need)

            elif "test" in weakness.lower():
                need = LearningNeed(
                    need_id=f"self_weak_{i}",
                    category="testing",
                    description="Learn testing patterns",
                    evidence=[weakness],
                    priority=0.7,
                    suggested_dataset="code_search_net",
                    suggested_model="codegen",
                    confidence=0.8,
                )
                needs.append(need)

        print(f"   Found {len(needs)} needs from self-analysis")
        for need in needs:
            print(f"   - {need.description} (priority: {need.priority:.0%})")

        return needs

    async def _analyze_interaction_patterns(self) -> List[LearningNeed]:
        """Analyze what users actually ask about (Real Data)"""
        from gateway.app.core.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()

        needs = []
        topic_counts = collector.topic_counts
        total = sum(topic_counts.values()) or 1

        print(f"   Analyzing {total} real interactions...")

        for topic, count in topic_counts.items():
            frequency = count / total
            if frequency > 0.1:  # Relevant if > 10% of queries
                if topic == "code_generation":
                    need = LearningNeed(
                        need_id=f"interact_{topic}",
                        category="coding",
                        description="Improve code generation (high user demand)",
                        evidence=[f"Users ask about {topic} {frequency:.0%} of the time"],
                        priority=min(0.9, frequency + 0.2),  # Boost priority slightly
                        suggested_dataset="code_search_net",
                        suggested_model="Salesforce/codegen-350M-mono",
                        confidence=0.9,
                    )
                    needs.append(need)

                elif topic == "arabic":
                    need = LearningNeed(
                        need_id=f"interact_{topic}",
                        category="language",
                        description="Improve Arabic language understanding",
                        evidence=[f"Users ask in Arabic {frequency:.0%} of the time"],
                        priority=min(0.85, frequency + 0.2),
                        suggested_dataset="arabic_billion_words",
                        suggested_model="aubmindlab/bert-base-arabertv2",
                        confidence=0.85,
                    )
                    needs.append(need)

                elif topic == "debugging":
                    need = LearningNeed(
                        need_id=f"interact_{topic}",
                        category="debugging",
                        description="Improve debugging capabilities",
                        evidence=[f"Users ask about debugging {frequency:.0%} of the time"],
                        priority=min(0.8, frequency + 0.2),
                        suggested_dataset="stackoverflow",
                        suggested_model="gpt2-medium",
                        confidence=0.8,
                    )
                    needs.append(need)

        if not needs:
            print("   ⚠️ No clear interaction patterns yet (need more data)")

        print(f"   Found {len(needs)} needs from user interactions")
        for need in needs:
            print(f"   - {need.description}")

        return needs

    async def _analyze_failure_patterns(self) -> List[LearningNeed]:
        """Analyze what actually fails (Real Data)"""
        from gateway.app.core.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()

        needs = []
        failures = collector.failure_counts

        print(f"   Analyzing {sum(failures.values())} failures...")

        for failure_type, count in failures.items():
            if count >= 1:  # Even 1 failure matters in early stages
                if failure_type == "math":
                    need = LearningNeed(
                        need_id=f"fail_{failure_type}",
                        category="math",
                        description="Learn advanced mathematics",
                        evidence=[f"Failed {count} times on math problems"],
                        priority=0.85,
                        suggested_dataset="math_dataset",
                        suggested_model="gpt2-medium",
                        confidence=0.8,
                    )
                    needs.append(need)

                elif failure_type == "complexity":
                    need = LearningNeed(
                        need_id=f"fail_{failure_type}",
                        category="coding",
                        description="Improve handling of complex queries",
                        evidence=[f"Failed {count} times on complex tasks"],
                        priority=0.8,
                        suggested_dataset="common_crawl",
                        suggested_model="gpt2-large",
                        confidence=0.75,
                    )
                    needs.append(need)

        if not needs:
            print("   ✅ No specific failure patterns detected yet")

        print(f"   Found {len(needs)} needs from failures")
        for need in needs:
            print(f"   - {need.description}")

        return needs

    async def _analyze_future_needs(self) -> List[LearningNeed]:
        """Predict future needs"""
        needs = []

        # Use unified agent to predict
        await self.agent.intelligent_analyze("What skills will I need in the future?")

        # Based on trends
        future_skills = [
            {
                "category": "multimodal",
                "description": "Learn vision + language",
                "dataset": "conceptual_captions",
                "model": "clip",
                "priority": 0.7,
            },
            {
                "category": "reasoning",
                "description": "Learn chain-of-thought reasoning",
                "dataset": "gsm8k",
                "model": "gpt2-medium",
                "priority": 0.75,
            },
        ]

        for skill in future_skills:
            need = LearningNeed(
                need_id=f"future_{skill['category']}",
                category=skill["category"],
                description=skill["description"],
                evidence=["Future capability requirement"],
                priority=skill["priority"],
                suggested_dataset=skill["dataset"],
                suggested_model=skill["model"],
                confidence=0.7,
            )
            needs.append(need)

        print(f"   Found {len(needs)} future needs")
        for need in needs:
            print(f"   - {need.description}")

        return needs

    async def _analyze_weekly_schedule(self) -> List[LearningNeed]:
        """
        Inject User-Defined Weekly Curriculum.
        Focus: Thinking, Agents, AI.
        """
        
        # User-Defined Schedule
        WEEKLY_SCHEDULE = [
            {
                "day": 1, 
                "category": "reasoning",
                "description": "Day 1: Advanced Chain-of-Thought Reasoning",
                "dataset": "gsm8k",
                "model": "gpt2-medium",
                "priority": 0.99
            },
            {
                "day": 2, 
                "category": "agents",
                "description": "Day 2: Tool Usage & API Integration",
                "dataset": "calculator_tools", # conceptual
                "model": "gpt2-medium",
                "priority": 0.98
            },
            {
                "day": 3, 
                "category": "ai_core",
                "description": "Day 3: AI Self-Improvement & Meta-Learning",
                "dataset": "alpaca_cleaned",
                "model": "gpt2-medium",
                "priority": 0.97
            },
            {
                "day": 4, 
                "category": "chat_ops",
                "description": "Day 4: Conversational Operations (Chat-to-Action)",
                "dataset": "dialogue_actions",
                "model": "gpt2-medium",
                "priority": 0.96
            },
            {
                "day": 5, 
                "category": "reflection",
                "description": "Day 5: Self-Reflection & Error Correction",
                "dataset": "self_instruct",
                "model": "gpt2-medium",
                "priority": 0.95
            },
            {
                "day": 6, 
                "category": "planning",
                "description": "Day 6: Long-term Planning & Decomposition",
                "dataset": "wikihow",
                "model": "gpt2-medium",
                "priority": 0.94
            },
            {
                "day": 7, 
                "category": "integration",
                "description": "Day 7: Unified System Integration (Noogh Protocol)",
                "dataset": "system_logs",
                "model": "gpt2-medium",
                "priority": 0.93 # Grand Finale
            }
        ]

        needs = []
        
        print(f"   📅 Loading {len(WEEKLY_SCHEDULE)} curriculum items...")
        
        for item in WEEKLY_SCHEDULE:
            need = LearningNeed(
                need_id=f"weekly_day_{item['day']}",
                category=item["category"],
                description=item["description"],
                evidence=["User-Defined Weekly Curriculum"],
                priority=item["priority"],
                suggested_dataset=item["dataset"],
                suggested_model=item["model"],
                confidence=1.0 
            )
            needs.append(need)
            
        return needs

    def _prioritize_needs(self, needs: List[LearningNeed]) -> List[LearningNeed]:
            """Prioritize learning needs"""

            if not needs:
                logger.warning("No learning needs provided.")
                return []

            # Sort by priority
            needs.sort(key=lambda n: n.priority, reverse=True)

            logger.info(f"Prioritized {len(needs)} needs:")
            for i, need in enumerate(needs[:5], 1):
                logger.info(f"{i}. {need.description} (priority: {need.priority:.0%})")

            return needs

    async def decide_training(self, top_n: int = 3) -> List[TrainingDecision]:
        """
        Decide what to train on.

        Considers:
        - Priority of need
        - Available resources
        - Training time
        - Expected improvement
        """
        print(f"\n{'='*80}")
        print("🎯 MAKING TRAINING DECISIONS")
        print(f"{'='*80}\n")

        # Get learning needs
        if not self.knowledge_gaps:
            await self.analyze_learning_needs()

        decisions = []

        # Select top N needs
        top_needs = self.knowledge_gaps[:top_n]

        for i, need in enumerate(top_needs, 1):
            print(f"\n{i}. Evaluating: {need.description}")

            # Create training config
            config = TrainingConfig(
                model_name=need.suggested_model,
                dataset_name=need.suggested_dataset,
                output_dir=f"./models/auto-learned-{need.category}",
                num_epochs=2,  # Start conservative
                batch_size=8,
                use_gpu=True,
                auto_optimize=True,
            )

            # Evaluate feasibility
            feasible, rationale = await self._evaluate_feasibility(need, config)

            decision = TrainingDecision(
                decision_id=f"decision_{i}",
                learning_need=need,
                training_config=config,
                rationale=rationale,
                expected_improvement=f"Close knowledge gap in {need.category}",
                approved=feasible and need.priority > 0.7,
                timestamp=datetime.now(),
            )

            decisions.append(decision)

            status = "✅ APPROVED" if decision.approved else "⏸️  DEFERRED"
            print(f"   {status}: {rationale}")

        self.training_decisions = decisions
        approved = [d for d in decisions if d.approved]

        print(f"\n{'='*80}")
        print("✅ TRAINING DECISIONS MADE")
        print(f"   Total evaluated: {len(decisions)}")
        print(f"   Approved: {len(approved)}")
        print(f"{'='*80}\n")

        return decisions

    async def _analyze_dream_data(self) -> List[LearningNeed]:
        """Check for synthetic dreams in data/dreams/"""
        import glob
        import os
        
        needs = []
        DREAMS_DIR = "/home/noogh/projects/noogh_unified_system/src/data/dreams"
        
        if not os.path.exists(DREAMS_DIR):
            return []
            
        dream_files = glob.glob(f"{DREAMS_DIR}/*.jsonl")
        if not dream_files:
            return []
            
        # Count total dreams
        total_dreams = len(dream_files)
        
        print(f"   💤 Found {total_dreams} synthetic dream files")
        
        if total_dreams > 0:
            need = LearningNeed(
                need_id="synthetic_dreams_reinforcement",
                category="synthetic_memory",
                description=f"Reinforce Synthetic Memories ({total_dreams} dreams)",
                evidence=[f"Found {total_dreams} generated dream scenarios"],
                priority=0.88, # High but below Day 1-6
                suggested_dataset="dreams", # Special flag for TrainingEngine
                suggested_model="gpt2-medium",
                confidence=0.9
            )
            needs.append(need)
            
        return needs

    async def _evaluate_feasibility(self, need: LearningNeed, config: TrainingConfig) -> tuple[bool, str]:
        """Evaluate if training is feasible"""

        # Check hardware
        from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness

        hw = get_hardware_consciousness()
        state = hw.full_introspection()

        # Need GPU for most training
        if not state["gpu"]["available"]:
            return False, "GPU not available - training would be too slow"

        # Check VRAM
        gpu = state["gpu"]["gpus"][0]
        vram_gb = gpu["memory_total_mb"] / 1024

        if vram_gb < 6:
            return False, f"Insufficient VRAM ({vram_gb:.1f}GB < 6GB required)"

        # Check priority
        if need.priority < 0.7:
            return False, f"Priority too low ({need.priority:.0%})"

        # Check confidence
        if need.confidence < 0.7:
            return False, f"Confidence too low ({need.confidence:.0%})"

        # Looks good!
        return True, f"Feasible: {vram_gb:.1f}GB VRAM, priority {need.priority:.0%}"

    async def execute_auto_training(self):
        """
        Execute autonomous training based on decisions.

        This is the full autonomous learning loop!
        """
        print(f"\n{'='*80}")
        print("🤖 AUTONOMOUS TRAINING EXECUTION")
        print(f"{'='*80}\n")

        # Make decisions
        decisions = await self.decide_training()

        # Execute approved trainings
        approved = [d for d in decisions if d.approved]

        if not approved:
            print("⚠️  No training approved at this time")
            return

        for i, decision in enumerate(approved, 1):
            print(f"\n{'='*60}")
            print(f"Training {i}/{len(approved)}: {decision.learning_need.description}")
            print(f"{'='*60}")

            try:
                result = await self.training_engine.train_model(decision.training_config)

                print("\n✅ Training complete!")
                print(f"   Model: {result.model_path}")
                print(f"   Loss: {result.metrics.get('eval_loss', 0):.4f}")
                print(f"   Time: {result.training_time:.1f}s")

                # Learn from this training
                await self._learn_from_training(decision, result)

            except Exception as e:
                print(f"\n❌ Training failed: {e}")
                # Learn from failure too!
                self.failure_patterns[decision.learning_need.category] += 1

    async def _learn_from_training(self, decision: TrainingDecision, result: Any):
        """Learn from training results"""

        # Update confidence
        if result.metrics.get("eval_loss", 999) < 3.0:
            print(f"   📚 Learned: Training on {decision.learning_need.suggested_dataset} works well")
            decision.learning_need.confidence = min(1.0, decision.learning_need.confidence + 0.1)
        else:
            print(f"   📚 Learned: Need better approach for {decision.learning_need.category}")
            decision.learning_need.confidence = max(0.5, decision.learning_need.confidence - 0.1)

    def record_interaction(self, query: str, success: bool):
        """Record user interaction for analysis (REAL)"""
        # Call persistent logger
        from gateway.app.core.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()
        collector.log_interaction(query, "Response not captured here", success)

        # Local cache update (legacy support)
        self.interaction_history.append({"query": query, "success": success, "timestamp": datetime.now()})


# Singleton
_curriculum_learner: Optional[AutoCurriculumLearner] = None


def get_curriculum_learner() -> AutoCurriculumLearner:
    """Get or create curriculum learner"""
    global _curriculum_learner
    if _curriculum_learner is not None:
        return _curriculum_learner
    _curriculum_learner = AutoCurriculumLearner()
    return _curriculum_learner


# Demo
if __name__ == "__main__":

    async def demo():
        learner = get_curriculum_learner()

        # Analyze what to learn
        needs = await learner.analyze_learning_needs()

        print("\n📊 Summary:")
        print(f"   Learning needs identified: {len(needs)}")

        # Make decisions
        decisions = await learner.decide_training(top_n=2)

        approved = [d for d in decisions if d.approved]
        print(f"\n   Trainings approved: {len(approved)}")

        if approved:
            print("\n✅ Will train on:")
            for d in approved:
                print(f"   - {d.learning_need.description}")
                print(f"     Dataset: {d.training_config.dataset_name}")
                print(f"     Model: {d.training_config.model_name}")

    asyncio.run(demo())
