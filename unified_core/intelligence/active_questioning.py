"""
Active Questioning Module - Deep Understanding Through Iterative Why/How
Part of NOOGH Cognitive Enhancement (Phase 1 - Quick Win #1)

This module implements active questioning to deepen understanding by:
1. Asking 'why' repeatedly (5 Whys technique)
2. Asking 'how' for implementation details
3. Asking 'what if' for edge cases
4. Building question chains that expose deeper insights
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger("unified_core.intelligence.active_questioning")


@dataclass
class Question:
    """Represents a single question in a questioning chain."""
    level: int
    question_type: str  # 'why', 'how', 'what_if', 'what_else'
    question_text: str
    answer: Optional[str] = None
    timestamp: str = None
    insights: List[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.insights is None:
            self.insights = []


class ActiveQuestioner:
    """
    Deep questioning system that asks 'why', 'how', and 'what if' repeatedly
    to deepen understanding and uncover hidden assumptions.

    Based on:
    - 5 Whys technique (Toyota Production System)
    - Socratic questioning
    - Root cause analysis
    """

    def __init__(self, max_depth: int = 5):
        """
        Initialize the Active Questioner.

        Args:
            max_depth: Maximum depth of questioning (default: 5 for "5 Whys")
        """
        self.max_depth = max_depth
        self.question_chains = []
        self.insights = []
        
        # Caching: avoid redundant LLM calls for the same subject
        self._inquiry_cache: Dict[str, Dict] = {}
        self._cache_ttl = 600  # 10 minutes
        self._cache_timestamps: Dict[str, float] = {}
        
        # NeuronFabric + EventBus
        self._neuron_fabric = None
        self._event_bus = None
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            self._neuron_fabric = get_neuron_fabric()
        except Exception:
            pass
        try:
            from unified_core.integration.event_bus import get_event_bus
            self._event_bus = get_event_bus()
        except Exception:
            pass

    def ask_why_chain(self, observation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ask 'why' repeatedly to deepen understanding.

        Args:
            observation: The initial observation or statement to question
            context: Optional context for more informed questioning

        Returns:
            Dictionary containing the question chain, insights, and depth analysis
        """
        questions = []
        current = observation

        for level in range(self.max_depth):
            # Generate why question
            why_question = self._generate_why_question(current, level, context)

            # Generate answer (in real system, this would query knowledge base)
            answer = self._answer_why(current, why_question, context)

            question = Question(
                level=level + 1,
                question_type='why',
                question_text=why_question,
                answer=answer,
                insights=self._extract_insights_from_answer(answer)
            )

            questions.append(question)
            current = answer

            # Stop if we've reached root cause
            if self._is_root_cause(answer):
                logger.info(f"Reached root cause at depth {level + 1}")
                break

        result = {
            'original_observation': observation,
            'question_chain': questions,
            'depth_reached': len(questions),
            'root_cause': questions[-1].answer if questions else None,
            'all_insights': [ins for q in questions for ins in q.insights],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        self.question_chains.append(result)
        return result

    def ask_how_chain(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ask 'how' repeatedly to understand implementation details.

        Args:
            goal: The goal or outcome to understand how to achieve
            context: Optional context for more informed questioning

        Returns:
            Dictionary containing the how-chain and implementation steps
        """
        questions = []
        current = goal

        for level in range(self.max_depth):
            how_question = self._generate_how_question(current, level, context)
            answer = self._answer_how(current, how_question, context)

            question = Question(
                level=level + 1,
                question_type='how',
                question_text=how_question,
                answer=answer,
                insights=self._extract_insights_from_answer(answer)
            )

            questions.append(question)
            current = answer

            # Stop if we've reached concrete implementation
            if self._is_concrete_enough(answer):
                logger.info(f"Reached concrete implementation at depth {level + 1}")
                break

        return {
            'goal': goal,
            'question_chain': questions,
            'depth_reached': len(questions),
            'implementation_steps': [q.answer for q in questions],
            'all_insights': [ins for q in questions for ins in q.insights],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def ask_what_if_scenarios(self, situation: str, count: int = 3) -> Dict[str, Any]:
        """
        Ask 'what if' questions to explore edge cases and alternatives.

        Args:
            situation: The situation to explore alternatives for
            count: Number of what-if scenarios to generate

        Returns:
            Dictionary containing what-if scenarios and their implications
        """
        scenarios = []

        for i in range(count):
            what_if = self._generate_what_if_question(situation, i)
            implications = self._analyze_what_if(what_if, situation)

            question = Question(
                level=i + 1,
                question_type='what_if',
                question_text=what_if,
                answer=implications,
                insights=self._extract_insights_from_answer(implications)
            )

            scenarios.append(question)

        return {
            'situation': situation,
            'scenarios': scenarios,
            'scenario_count': len(scenarios),
            'all_insights': [ins for s in scenarios for ins in s.insights],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def comprehensive_inquiry(self, subject: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive inquiry using all questioning techniques.
        Includes caching, NeuronFabric insight storage, and EventBus publishing.
        """
        import hashlib, time
        
        # Cache check
        cache_key = hashlib.sha256(subject.encode()).hexdigest()[:16]
        cached_ts = self._cache_timestamps.get(cache_key, 0)
        if time.time() - cached_ts < self._cache_ttl and cache_key in self._inquiry_cache:
            logger.info(f"⚡ CACHED INQUIRY: {subject[:40]}...")
            return self._inquiry_cache[cache_key]
        
        logger.info(f"Starting comprehensive inquiry on: {subject}")

        why_chain = self.ask_why_chain(subject, context)
        how_chain = self.ask_how_chain(subject, context)
        what_if_scenarios = self.ask_what_if_scenarios(subject, count=3)

        # Synthesize insights
        all_insights = (
            why_chain['all_insights'] +
            how_chain['all_insights'] +
            what_if_scenarios['all_insights']
        )
        synthesized = self._synthesize_insights(all_insights)

        result = {
            'subject': subject,
            'why_analysis': why_chain,
            'how_analysis': how_chain,
            'what_if_analysis': what_if_scenarios,
            'total_questions_asked': (
                len(why_chain['question_chain']) +
                len(how_chain['question_chain']) +
                len(what_if_scenarios['scenarios'])
            ),
            'synthesized_insights': synthesized,
            'depth_score': self._calculate_depth_score(why_chain, how_chain),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Cache result
        self._inquiry_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        # Store insights as NeuronFabric neurons
        if self._neuron_fabric and synthesized:
            try:
                from unified_core.core.neuron_fabric import NeuronType
                for insight in synthesized[:5]:
                    self._neuron_fabric.create_neuron(
                        proposition=insight[:120],
                        neuron_type=NeuronType.COGNITIVE,
                        confidence=0.5,
                        domain="intelligence",
                        tags=["inquiry_insight", "active_questioning"],
                        metadata={"subject": subject[:80], "source": "ActiveQuestioner"}
                    )
            except Exception:
                pass
        
        # Publish inquiry event
        if self._event_bus:
            try:
                from unified_core.integration.event_bus import EventPriority
                self._event_bus.publish_sync(
                    "inquiry_completed",
                    {
                        "subject": subject[:100],
                        "total_questions": result['total_questions_asked'],
                        "depth_score": result['depth_score'],
                        "insights_count": len(synthesized),
                    },
                    "ActiveQuestioner",
                    EventPriority.LOW
                )
            except Exception:
                pass
        
        return result

    # Internal helper methods

    def _generate_why_question(self, current: str, level: int, context: Optional[Dict] = None) -> str:
        """Generate a why question based on current statement."""
        if level == 0:
            return f"Why does this happen: '{current}'?"
        else:
            return f"Why is that the case (level {level + 1})?"

    def _generate_how_question(self, current: str, level: int, context: Optional[Dict] = None) -> str:
        """Generate a how question based on current goal."""
        if level == 0:
            return f"How can we achieve: '{current}'?"
        else:
            return f"How do we implement that (level {level + 1})?"

    def _generate_what_if_question(self, situation: str, index: int) -> str:
        """Generate a what-if question for alternative scenarios."""
        templates = [
            f"What if the assumption in '{situation}' is wrong?",
            f"What if we reversed the approach in '{situation}'?",
            f"What if external conditions change for '{situation}'?"
        ]
        return templates[index % len(templates)]

    def _call_neural_engine(self, prompt: str) -> str:
        """Helper to call Neural Engine synchronously."""
        import asyncio
        from dotenv import load_dotenv
        import pathlib
        
        # Load env vars safely if not loaded
        env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            
        from unified_core.neural_bridge import NeuralEngineClient
        
        async def _run():
            client = NeuralEngineClient()
            try:
                messages = [
                    {"role": "system", "content": "أنت NOOGH، العقل الاستراتيجي والتحليلي. أجب بعمق ووضوح، واذكر السبب الجذري والتفاصيل المهمة باختصار باللغة العربية."},
                    {"role": "user", "content": prompt}
                ]
                resp = await client.complete(messages, max_tokens=300)
                if resp.get('success'):
                    return resp.get('content', '').strip()
                return f"عذراً، لم أتمكن من استنتاج السبب (خطأ في النظام): {resp.get('error', 'Unknown Error')}"
            except Exception as e:
                return f"[خطأ غير متوقع: {str(e)}]"
            finally:
                await client.close()
                
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(_run()))
                return future.result()
        else:
            return asyncio.run(_run())

    def _answer_why(self, current: str, question: str, context: Optional[Dict] = None) -> str:
        """
        Generate answer to why question using NeuralEngineClient.
        """
        prompt = f"السياق/الحدث: '{current}'\n\nالسؤال المطروح: {question}\n\nيرجى الإجابة عن السبب المباشر والجذري باختصار (في حدود سطرين أو ثلاثة)."
        logger.info(f"Asking NeuralEngine (Why): {question}")
        return self._call_neural_engine(prompt)

    def _answer_how(self, current: str, question: str, context: Optional[Dict] = None) -> str:
        """
        Generate answer to how question using NeuralEngineClient.
        """
        prompt = f"الهدف: '{current}'\n\nالسؤال المطروح: {question}\n\nيرجى توضيح الخطوات العملية للتنفيذ باختصار وفي نقاط واضحة."
        logger.info(f"Asking NeuralEngine (How): {question}")
        return self._call_neural_engine(prompt)

    def _analyze_what_if(self, what_if: str, situation: str) -> str:
        """Analyze implications of what-if scenario using NeuralEngineClient."""
        prompt = f"الموقف الأساسي: '{situation}'\n\nالسيناريو الافتراضي المطروح (ماذا لو): {what_if}\n\nما هي النتيجة أو التأثير المحتمل بشكل موجز ومباشر؟"
        logger.info(f"Asking NeuralEngine (What-If): {what_if}")
        return self._call_neural_engine(prompt)

    def _extract_insights_from_answer(self, answer: str) -> List[str]:
        """Extract key insights from an answer."""
        # Simplified - in real system, would use NLP/semantic analysis
        return [f"Insight: {answer[:100]}..."]

    def _is_root_cause(self, answer: str) -> bool:
        """Check if we've reached a root cause."""
        # Simplified heuristic
        root_indicators = ['fundamental', 'core', 'basic', 'intrinsic', 'inherent']
        return any(indicator in answer.lower() for indicator in root_indicators)

    def _is_concrete_enough(self, answer: str) -> bool:
        """Check if implementation detail is concrete enough."""
        concrete_indicators = ['specific', 'execute', 'implement', 'code', 'steps']
        return any(indicator in answer.lower() for indicator in concrete_indicators)

    def _synthesize_insights(self, insights: List[str]) -> List[str]:
        """Synthesize and deduplicate insights."""
        # Remove duplicates and group similar insights
        unique_insights = list(set(insights))
        return unique_insights[:10]  # Top 10 most relevant

    def _calculate_depth_score(self, why_chain: Dict, how_chain: Dict) -> float:
        """Calculate depth score based on questioning thoroughness."""
        why_depth = why_chain['depth_reached']
        how_depth = how_chain['depth_reached']

        # Score: (actual_depth / max_possible_depth) * 100
        avg_depth = (why_depth + how_depth) / 2
        depth_score = (avg_depth / self.max_depth) * 100

        return round(depth_score, 2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about questioning activity."""
        return {
            'total_question_chains': len(self.question_chains),
            'average_depth': sum(c['depth_reached'] for c in self.question_chains) / len(self.question_chains) if self.question_chains else 0,
            'total_insights_generated': sum(len(c['all_insights']) for c in self.question_chains),
            'question_types_distribution': {
                'why': sum(1 for c in self.question_chains if any(q.question_type == 'why' for q in c.get('question_chain', []))),
                'how': sum(1 for c in self.question_chains if any(q.question_type == 'how' for q in c.get('question_chain', []))),
                'what_if': sum(1 for c in self.question_chains if any(q.question_type == 'what_if' for q in c.get('question_chain', [])))
            }
        }


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    questioner = ActiveQuestioner(max_depth=5)

    # Example 1: Why chain
    print("=" * 70)
    print("EXAMPLE 1: Why Chain")
    print("=" * 70)
    result = questioner.ask_why_chain(
        "The evolution pipeline was blocked with 98 innovations stuck in queue"
    )
    print(f"Depth reached: {result['depth_reached']}")
    print(f"Root cause: {result['root_cause']}")
    print(f"Insights: {len(result['all_insights'])}")
    print()

    # Example 2: How chain
    print("=" * 70)
    print("EXAMPLE 2: How Chain")
    print("=" * 70)
    result = questioner.ask_how_chain(
        "Implement Active Questioning capability in NOOGH"
    )
    print(f"Depth reached: {result['depth_reached']}")
    print(f"Implementation steps: {len(result['implementation_steps'])}")
    print()

    # Example 3: What-if scenarios
    print("=" * 70)
    print("EXAMPLE 3: What-If Scenarios")
    print("=" * 70)
    result = questioner.ask_what_if_scenarios(
        "Agent daemon checks triggers every 10 cycles"
    )
    print(f"Scenarios explored: {result['scenario_count']}")
    print()

    # Example 4: Comprehensive inquiry
    print("=" * 70)
    print("EXAMPLE 4: Comprehensive Inquiry")
    print("=" * 70)
    result = questioner.comprehensive_inquiry(
        "NOOGH needs better cognitive depth"
    )
    print(f"Total questions asked: {result['total_questions_asked']}")
    print(f"Depth score: {result['depth_score']}")
    print(f"Synthesized insights: {len(result['synthesized_insights'])}")
    print()

    # Statistics
    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    stats = questioner.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
