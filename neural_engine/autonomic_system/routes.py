"""
Self-Governing Agent API Endpoints
Exposes self-improvement capabilities via REST API
"""

from fastapi import APIRouter, BackgroundTasks, Depends

from neural_engine.autonomic_system.self_governor import get_self_governing_agent
from unified_core.auth import AuthContext, require_admin, require_bearer

router = APIRouter(prefix="/self", tags=["Self-Governing"])


@router.get("/analyze")
async def analyze_system(auth: AuthContext = Depends(require_admin)):
    """
    UC3 analyzes itself and returns findings.

    Requires admin auth.
    """
    agent = get_self_governing_agent()
    analysis = await agent.analyze_self()

    from dataclasses import asdict

    return {"ok": True, "analysis": asdict(analysis)}


@router.get("/report")
async def get_self_report(auth: AuthContext = Depends(require_admin)):
    """
    Generate comprehensive self-analysis report.

    Returns markdown report.
    """
    agent = get_self_governing_agent()
    report = await agent.generate_self_report()

    return {"ok": True, "report": report, "format": "markdown"}


@router.get("/proposals")
async def get_improvement_proposals(limit: int = 5, auth: AuthContext = Depends(require_admin)):
    """Get improvement proposals from UC3."""
    agent = get_self_governing_agent()
    proposals = await agent.propose_improvements(limit=limit)

    from dataclasses import asdict

    return {"ok": True, "proposals": [asdict(p) for p in proposals]}


@router.post("/learn")
async def learn_from_interaction(
    query: str, response: str, feedback_score: float = 0.5, auth: AuthContext = Depends(require_bearer)
):
    """
    UC3 learns from a user interaction.

    Args:
        query: User's query
        response: System's response
        feedback_score: Quality score (0-1)
    """
    agent = get_self_governing_agent()

    await agent.learn_from_interaction({"query": query, "response": response, "feedback_score": feedback_score})

    return {"ok": True, "message": "Learning recorded"}


@router.post("/auto-improve")
async def trigger_auto_improvement(background_tasks: BackgroundTasks, auth: AuthContext = Depends(require_admin)):
    """
    Trigger autonomous improvement cycle in background.

    UC3 will:
    1. Analyze itself
    2. Generate proposals
    3. Learn patterns
    4. Generate report
    """

    async def improvement_cycle():
        agent = get_self_governing_agent()

        # Full cycle
        await agent.analyze_self()
        await agent.propose_improvements()
        report = await agent.generate_self_report()

        # Log
        print("✅ Auto-improvement cycle complete")
        print(report[:500] + "...")

    # Run in background
    background_tasks.add_task(improvement_cycle)

    return {
        "ok": True,
        "status": "improvement_cycle_started",
        "message": "UC3 is analyzing and improving itself in background",
    }


@router.get("/learned-patterns")
async def get_learned_patterns(auth: AuthContext = Depends(require_admin)):
    """Get patterns UC3 has learned from interactions."""
    agent = get_self_governing_agent()

    return {"ok": True, "patterns": agent.learned_patterns}


@router.get("/health")
async def self_health_check(auth: AuthContext = Depends(require_bearer)):
    """UC3's self-assessed health status."""
    agent = get_self_governing_agent()
    analysis = await agent.analyze_self()

    return {
        "ok": True,
        "confidence": analysis.confidence_score,
        "status": "healthy" if analysis.confidence_score > 0.8 else "degraded",
        "metrics": analysis.performance_metrics,
    }
