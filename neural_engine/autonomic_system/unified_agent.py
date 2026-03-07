"""
NOOGH Unified Intelligent Agent
Combines ALL capabilities into one super-intelligent agent:
- Deep thinking (Thinking Claude)
- Hardware awareness
- Parallel neural processing
- Self-governing
- Full system access
- File analysis
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# from neural_engine.autonomic_system.full_access import get_unrestricted_learner -- REMOVED


# Import all components
from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness
from neural_engine.autonomic_system.parallel_neural_engine import get_parallel_engine
from neural_engine.autonomic_system.self_governor import get_self_governing_agent


@dataclass
class IntelligentInsight:
    """A single intelligent insight combining multiple sources"""

    source: str  # hardware/parallel/self/files
    insight: str
    confidence: float
    supporting_data: Dict[str, Any]
    timestamp: datetime


@dataclass
class UnifiedAnalysis:
    """Complete analysis from all systems"""

    query: str
    hardware_insights: List[IntelligentInsight]
    parallel_thoughts: List[IntelligentInsight]
    self_analysis: List[IntelligentInsight]
    file_insights: List[IntelligentInsight]
    unified_recommendation: str
    confidence_score: float
    execution_time: float


class UnifiedIntelligentAgent:
    """
    The ultimate NOOGH agent - combines everything:

    🧠 Deep Thinking +
    ⚡ Parallel Processing +
    💻 Hardware Awareness +
    📊 Self-Governing +
    📖 File Analysis +
    🌍 System Access

    = Super-intelligent recommendations
    """

    def __init__(self):
        """Initialize unified agent with all capabilities"""
        self.hardware = get_hardware_consciousness()
        self.parallel_engine = get_parallel_engine()
        self.self_governor = get_self_governing_agent()
        self.self_governor = get_self_governing_agent()
        # self.system_learner = get_unrestricted_learner() -- REMOVED for strict security

        print("🚀 Unified Intelligent Agent initialized")
        print("   ✅ Hardware awareness active")
        print("   ✅ Parallel neural engine active")
        print("   ✅ Self-governing active")
        print("   ✅ Self-governing active")
        # print("   ✅ Full system access active") -- DISABLED

    async def intelligent_analyze(self, query: str) -> UnifiedAnalysis:
        """
        Perform intelligent analysis using ALL systems in parallel.

        This is what makes NOOGH special:
        - Not just answering - UNDERSTANDING deeply
        - Not just thinking - thinking PARALLEL
        - Not just recommending - recommending with FULL context

        Args:
            query: User's question/task

        Returns:
            Complete unified analysis with smart recommendations
        """
        print(f"\n{'='*80}")
        print("🧠 UNIFIED INTELLIGENT ANALYSIS")
        print(f"Query: {query}")
        print(f"{'='*80}\n")

        start_time = time.time()

        # Run ALL analyses in parallel (the power of parallelism!)
        print("⚡ Running 4 parallel analysis streams...")

        tasks = [
            self._analyze_from_hardware(query),
            self._analyze_parallel_thinking(query),
            self._analyze_self_state(query),
            self._analyze_system_files(query),
        ]

        results = await asyncio.gather(*tasks)

        hardware_insights, parallel_insights, self_insights, file_insights = results

        # Synthesize all insights into unified recommendation
        print("\n🔄 Synthesizing insights from all sources...")
        recommendation = self._synthesize_unified_recommendation(
            query, hardware_insights, parallel_insights, self_insights, file_insights
        )

        elapsed = time.time() - start_time

        analysis = UnifiedAnalysis(
            query=query,
            hardware_insights=hardware_insights,
            parallel_thoughts=parallel_insights,
            self_analysis=self_insights,
            file_insights=file_insights,
            unified_recommendation=recommendation["recommendation"],
            confidence_score=recommendation["confidence"],
            execution_time=elapsed,
        )

        self._display_analysis(analysis)

        return analysis

    async def _analyze_from_hardware(self, query: str) -> List[IntelligentInsight]:
        """
        Analyze query from hardware perspective.

        Questions like:
        - Do I have enough resources?
        - Which cores are free?
        - Is GPU needed?
        - Memory sufficient?
        """
        print("   💻 Hardware analysis...")

        state = self.hardware.full_introspection()
        insights = []

        # CPU insights
        cpu_usage = sum(c["usage_percent"] for c in state["cpu"]["cores"]) / len(state["cpu"]["cores"])
        if cpu_usage > 80:
            insights.append(
                IntelligentInsight(
                    source="hardware",
                    insight="⚠️ CPU heavily loaded - recommend distributed processing",
                    confidence=0.95,
                    supporting_data={"cpu_usage": cpu_usage},
                    timestamp=datetime.utcnow(),
                )
            )
        else:
            insights.append(
                IntelligentInsight(
                    source="hardware",
                    insight=f"✅ CPU available ({100-cpu_usage:.0f}% free) - can handle task locally",
                    confidence=0.9,
                    supporting_data={"cpu_free": 100 - cpu_usage},
                    timestamp=datetime.utcnow(),
                )
            )

        # GPU insights
        if state["gpu"]["available"] and "train" in query.lower() or "ml" in query.lower():
            gpu = state["gpu"]["gpus"][0]
            insights.append(
                IntelligentInsight(
                    source="hardware",
                    insight=f"🎮 GPU ({gpu['name']}) perfect for this task - {gpu['cuda_cores']:,} CUDA cores available",
                    confidence=0.95,
                    supporting_data={"gpu": gpu},
                    timestamp=datetime.utcnow(),
                )
            )

        # Memory insights
        mem_available = state["memory"]["available_mb"] / 1024  # GB
        if "big data" in query.lower() or "large" in query.lower():
            if mem_available < 4:
                insights.append(
                    IntelligentInsight(
                        source="hardware",
                        insight=f"⚠️ Limited RAM ({mem_available:.1f} GB) - recommend data streaming",
                        confidence=0.9,
                        supporting_data={"ram_gb": mem_available},
                        timestamp=datetime.utcnow(),
                    )
                )
            else:
                insights.append(
                    IntelligentInsight(
                        source="hardware",
                        insight=f"✅ Sufficient RAM ({mem_available:.1f} GB) for large datasets",
                        confidence=0.85,
                        supporting_data={"ram_gb": mem_available},
                        timestamp=datetime.utcnow(),
                    )
                )

        return insights

    async def _analyze_parallel_thinking(self, query: str) -> List[IntelligentInsight]:
        """
        Use parallel thinking to analyze from multiple perspectives.
        """
        print("   ⚡ Parallel thinking analysis...")

        result = await self.parallel_engine.think_parallel(query)

        insights = []

        # Extract insights from parallel thoughts
        for thought_process in result["thought_processes"]:
            insights.append(
                IntelligentInsight(
                    source=f"parallel_core_{thought_process['core']}",
                    insight=thought_process["result"],
                    confidence=0.8,
                    supporting_data={"core_id": thought_process["core"], "thought_time": thought_process["time"]},
                    timestamp=datetime.utcnow(),
                )
            )

        # Add overall parallel insight
        insights.append(
            IntelligentInsight(
                source="parallel_summary",
                insight=f"Analyzed from {result['parallel_thoughts']} perspectives in {result['elapsed_time']:.2f}s",
                confidence=0.9,
                supporting_data={"speedup": f"{result['parallel_thoughts']}x parallel"},
                timestamp=datetime.utcnow(),
            )
        )

        return insights

    async def _analyze_self_state(self, query: str) -> List[IntelligentInsight]:
        """
        Analyze based on self-awareness and self-improvement data.
        """
        print("   📊 Self-analysis...")

        analysis = await self.self_governor.analyze_self()

        insights = []

        # Strengths relevant to query
        if "build" in query.lower() or "create" in query.lower():
            insights.append(
                IntelligentInsight(
                    source="self_strengths",
                    insight=f"✅ I excel at: {', '.join(analysis.strengths[:3])}",
                    confidence=1.0,
                    supporting_data={"all_strengths": analysis.strengths},
                    timestamp=datetime.utcnow(),
                )
            )

        # Weaknesses to consider
        if analysis.weaknesses:
            insights.append(
                IntelligentInsight(
                    source="self_weaknesses",
                    insight=f"⚠️ Current limitations: {', '.join(analysis.weaknesses[:2])}",
                    confidence=0.95,
                    supporting_data={"all_weaknesses": analysis.weaknesses},
                    timestamp=datetime.utcnow(),
                )
            )

        # Improvement suggestions
        if analysis.improvement_ideas:
            top_idea = analysis.improvement_ideas[0]
            insights.append(
                IntelligentInsight(
                    source="self_improvement",
                    insight=f"💡 Recommended enhancement: {top_idea['title']}",
                    confidence=0.85,
                    supporting_data=top_idea,
                    timestamp=datetime.utcnow(),
                )
            )

        # Confidence
        insights.append(
            IntelligentInsight(
                source="self_confidence",
                insight=f"📈 System confidence: {analysis.confidence_score:.0%}",
                confidence=analysis.confidence_score,
                supporting_data={"metrics": analysis.performance_metrics},
                timestamp=datetime.utcnow(),
            )
        )

        return insights

    async def _analyze_system_files(self, query: str) -> List[IntelligentInsight]:
        """
        Analyze relevant system files and codebase.
        NOTE: Full file system access has been disabled for security. 
        Only authorized paths should be accessed via specific tools.
        """
        print("   📖 File system analysis (Restricted Mode)...")
        # Returning empty insights as direct system exploration is disabled in production
        return []

    def _synthesize_unified_recommendation(
        self,
        query: str,
        hardware: List[IntelligentInsight],
        parallel: List[IntelligentInsight],
        self_analysis: List[IntelligentInsight],
        files: List[IntelligentInsight],
    ) -> Dict[str, Any]:
        """
        Synthesize all insights into unified intelligent recommendation.

        This is where the magic happens - combining:
        - Hardware state
        - Parallel thinking results
        - Self-awareness
        - File system knowledge

        Into ONE smart recommendation.
        """
        recommendation_parts = []

        # Header
        recommendation_parts.append(f"🎯 Unified Analysis for: '{query}'")
        recommendation_parts.append("")

        # Hardware perspective
        if hardware:
            recommendation_parts.append("💻 Hardware Perspective:")
            for insight in hardware[:2]:
                recommendation_parts.append(f"   {insight.insight}")
            recommendation_parts.append("")

        # Parallel thinking perspective
        if parallel:
            recommendation_parts.append("⚡ Parallel Analysis:")
            summary = parallel[-1]  # Last one is summary
            recommendation_parts.append(f"   {summary.insight}")
            recommendation_parts.append("")

        # Self-awareness perspective
        if self_analysis:
            recommendation_parts.append("📊 Self-Assessment:")
            for insight in self_analysis[:2]:
                recommendation_parts.append(f"   {insight.insight}")
            recommendation_parts.append("")

        # File system perspective
        if files:
            recommendation_parts.append("📖 System Knowledge:")
            for insight in files[:2]:
                recommendation_parts.append(f"   {insight.insight}")
            recommendation_parts.append("")

        # Unified recommendation
        recommendation_parts.append("✅ Unified Recommendation:")
        recommendation_parts.append("")

        # Intelligence synthesis
        all_insights = hardware + parallel + self_analysis + files
        avg_confidence = sum(i.confidence for i in all_insights) / len(all_insights) if all_insights else 0.5

        # Generate smart recommendation based on all data
        recommendation_parts.append(self._generate_smart_action_plan(query, all_insights))

        return {"recommendation": "\n".join(recommendation_parts), "confidence": avg_confidence}

    def _generate_smart_action_plan(self, query: str, insights: List[IntelligentInsight]) -> str:
        """Generate actionable plan based on all insights"""

        # Extract key information
        has_gpu = any("GPU" in i.insight for i in insights)
        any("heavily loaded" in i.insight for i in insights)
        sufficient_ram = any("Sufficient RAM" in i.insight for i in insights)

        plan = ""

        # Task-specific recommendations
        if "build" in query.lower() or "create" in query.lower():
            plan += "Recommended approach:\n"
            plan += "1. Use parallel processing across all 28 cores\n"
            if has_gpu:
                plan += "2. Leverage GPU acceleration for heavy computations\n"
            if sufficient_ram:
                plan += "3. Can load entire dataset in memory for faster processing\n"
            else:
                plan += "3. Use streaming approach due to RAM constraints\n"
            plan += "4. Monitor resource usage in real-time\n"
            plan += "5. Implement auto-scaling if load increases\n"

        elif "analyze" in query.lower():
            plan += "Analysis strategy:\n"
            plan += "1. Distribute analysis across multiple cores\n"
            plan += "2. Use parallel pattern recognition\n"
            plan += "3. Combine hardware metrics with code analysis\n"
            plan += "4. Generate comprehensive report\n"

        else:
            plan += "General approach:\n"
            plan += "1. Leverage all available cores for parallel execution\n"
            plan += "2. Monitor system resources during execution\n"
            plan += "3. Adapt strategy based on real-time performance\n"

        plan += f"\n📊 Confidence: {sum(i.confidence for i in insights)/len(insights):.0%}"
        plan += f"\n⚡ Expected speedup: {len(insights)}x (parallel processing)"

        return plan

    def _display_analysis(self, analysis: UnifiedAnalysis):
        """Display beautiful analysis results"""
        print(f"\n{'='*80}")
        print("✅ UNIFIED ANALYSIS COMPLETE")
        print(f"{'='*80}\n")

        print("📊 Analysis Summary:")
        print(f"   Hardware insights: {len(analysis.hardware_insights)}")
        print(f"   Parallel thoughts: {len(analysis.parallel_thoughts)}")
        print(f"   Self-analysis points: {len(analysis.self_analysis)}")
        print(f"   File insights: {len(analysis.file_insights)}")
        print(f"   Overall confidence: {analysis.confidence_score:.0%}")
        print(f"   Execution time: {analysis.execution_time:.2f}s")
        print()

        print("=" * 80)
        print(analysis.unified_recommendation)
        print("=" * 80)


# Singleton
_unified_agent: Optional[UnifiedIntelligentAgent] = None


def get_unified_agent() -> UnifiedIntelligentAgent:
    """Get or create unified intelligent agent"""
    global _unified_agent
    if _unified_agent is None:
        _unified_agent = UnifiedIntelligentAgent()
    return _unified_agent


# Demo
if __name__ == "__main__":

    async def demo():
        agent = get_unified_agent()

        # Test queries
        queries = [
            "Build a microservices architecture for high-traffic application",
            "Analyze the current system performance",
        ]

        for query in queries:
            await agent.intelligent_analyze(query)
            print("\n\n")
            await asyncio.sleep(1)

    asyncio.run(demo())
