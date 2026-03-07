"""
Autonomic Control API - HTTP endpoints for initiative loop control
Provides safe start/stop/status interface
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/autonomic", tags=["Autonomic System"])


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get current status of autonomic system
    
    Returns:
        Status including running state, stats, and configuration
    """
    try:
        from neural_engine.autonomic_system.initiative_loop import get_initiative_loop
        
        loop = get_initiative_loop()
        status = loop.get_status()
        
        logger.info("📊 Status requested")
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Status request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_loop(interval: int = 60) -> Dict[str, Any]:
    """
    Start the autonomic initiative loop
    
    Args:
        interval: Observation interval in seconds (default: 60)
        
    Returns:
        Start confirmation with configuration
    """
    try:
        from neural_engine.autonomic_system.initiative_loop import get_initiative_loop
        
        # Validate interval
        if interval < 10:
            raise HTTPException(
                status_code=400, 
                detail="Interval must be at least 10 seconds"
            )
        
        if interval > 3600:
            raise HTTPException(
                status_code=400,
                detail="Interval must not exceed 3600 seconds (1 hour)"
            )
        
        loop = get_initiative_loop(interval=interval)
        
        # Check if already running
        if loop.running:
            logger.warning("⚠️  Initiative loop already running")
            return {
                "success": False,
                "message": "Loop already running",
                "status": loop.get_status()
            }
        
        # Start the loop
        loop.start()
        
        logger.info(f"🚀 Initiative loop started (interval={interval}s)")
        
        return {
            "success": True,
            "message": f"Initiative loop started",
            "interval": interval,
            "status": loop.get_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_loop() -> Dict[str, Any]:
    """
    Stop the autonomic initiative loop
    
    Returns:
        Stop confirmation
    """
    try:
        from neural_engine.autonomic_system.initiative_loop import get_initiative_loop
        
        loop = get_initiative_loop()
        
        # Check if running
        if not loop.running:
            logger.warning("⚠️  Initiative loop not running")
            return {
                "success": False,
                "message": "Loop not running"
            }
        
        # Stop the loop
        loop.stop()
        
        logger.info("🛑 Initiative loop stopped")
        
        return {
            "success": True,
            "message": "Initiative loop stopped"
        }
        
    except Exception as e:
        logger.error(f"❌ Stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get detailed statistics
    
    Returns:
        Detailed stats including observations, executions, etc.
    """
    try:
        from neural_engine.autonomic_system.initiative_loop import get_initiative_loop
        
        loop = get_initiative_loop()
        status = loop.get_status()
        
        return {
            "success": True,
            "stats": status.get("stats", {}),
            "executor_stats": status.get("executor_stats", {}),
            "running": status.get("running", False)
        }
        
    except Exception as e:
        logger.error(f"❌ Stats request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple health check
    
    Returns:
        Health status
    """
    try:
        from neural_engine.autonomic_system.initiative_loop import get_initiative_loop
        
        loop = get_initiative_loop()
        
        return {
            "success": True,
            "healthy": True,
            "running": loop.running,
            "observations": loop.stats.get("observations", 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }
