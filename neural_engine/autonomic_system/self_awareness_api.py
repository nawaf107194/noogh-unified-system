"""
Self-Awareness API - Behavioral analysis endpoints
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/self-awareness", tags=["Self-Awareness"])


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get self-awareness adapter status
    
    Returns:
        Adapter status
    """
    try:
        from neural_engine.specialized_systems.self_awareness_adapter import get_self_awareness_adapter
        
        adapter = get_self_awareness_adapter()
        status = adapter.get_status()
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Status request failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/summary")
async def get_summary(
    window: int = Query(300, ge=60, le=3600, description="Analysis window in seconds")
) -> Dict[str, Any]:
    """
    Get behavioral summary
    
    Args:
        window: Time window to analyze (60-3600 seconds, default: 300)
        
    Returns:
        Complete behavioral analysis
    """
    try:
        from neural_engine.specialized_systems.self_awareness_adapter import get_self_awareness_adapter
        
        adapter = get_self_awareness_adapter()
        summary = adapter.get_summary(window_seconds=window)
        
        logger.info(f"📊 Summary generated for {window}s window")
        
        return {
            "success": True,
            **summary
        }
        
    except Exception as e:
        logger.error(f"❌ Summary request failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/proposals")
async def get_proposals(
    window: int = Query(300, ge=60, le=3600, description="Analysis window in seconds")
) -> Dict[str, Any]:
    """
    Get self-improvement proposals
    
    Args:
        window: Time window to analyze
        
    Returns:
        Proposed improvements
    """
    try:
        from neural_engine.specialized_systems.self_awareness_adapter import get_self_awareness_adapter
        
        adapter = get_self_awareness_adapter()
        observation = adapter.observe(window_seconds=window)
        assessment = adapter.assess(observation)
        proposals = adapter.propose_actions(assessment)
        
        return {
            "success": True,
            "window_seconds": window,
            "proposals": proposals,
            "assessment_summary": {
                "total_decisions": assessment["decision_analysis"]["total_decisions"],
                "approval_rate": assessment["decision_analysis"]["approval_rate"],
                "execution_success_rate": assessment["execution_analysis"]["success_rate"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Proposals request failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics(
    window: int = Query(300, ge=60, le=3600, description="Analysis window in seconds")
) -> Dict[str, Any]:
    """
    Get behavioral metrics only
    
    Args:
        window: Time window to analyze
        
    Returns:
        Key metrics
    """
    try:
        from neural_engine.specialized_systems.self_awareness_adapter import get_self_awareness_adapter
        
        adapter = get_self_awareness_adapter()
        observation = adapter.observe(window_seconds=window)
        assessment = adapter.assess(observation)
        
        return {
            "success": True,
            "window_seconds": window,
            "metrics": {
                "total_events": assessment["total_events"],
                "events_by_type": assessment["events_by_type"],
                "decision_metrics": {
                    "total": assessment["decision_analysis"]["total_decisions"],
                    "approved": assessment["decision_analysis"]["approved"],
                    "blocked": assessment["decision_analysis"]["blocked"],
                    "approval_rate": assessment["decision_analysis"]["approval_rate"],
                    "avg_confidence": assessment["decision_analysis"]["confidence_avg"]
                },
                "execution_metrics": {
                    "total": assessment["execution_analysis"]["total_executions"],
                    "successful": assessment["execution_analysis"]["successful"],
                    "failed": assessment["execution_analysis"]["failed"],
                    "success_rate": assessment["execution_analysis"]["success_rate"]
                },
                "health_metrics": {
                    "avg_cpu": assessment["health_analysis"]["avg_cpu"],
                    "avg_memory": assessment["health_analysis"]["avg_memory"],
                    "health_statuses": assessment["health_analysis"]["health_statuses"]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Metrics request failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
