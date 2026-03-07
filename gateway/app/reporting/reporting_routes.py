"""
Reporting API Routes
Expose comprehensive reporting via REST API and WebSockets
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect

from gateway.app.core.auth import AuthContext, require_admin
from gateway.app.core.metrics_collector import get_metrics_collector
from gateway.app.reporting.comprehensive_reporter import get_reporter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.websocket("/stream")
async def websocket_report_stream(websocket: WebSocket):
    """
    Stream real-time system pulse.
    """
    await websocket.accept()
    # Send immediate handshake to confirm connection
    await websocket.send_json({"type": "handshake", "status": "connected"})

    reporter = get_reporter()
    collector = get_metrics_collector()

    try:
        while True:
            # 1. Get Hardware Stats (Fast)
            # We use internal method to avoid async overhead if possible,
            # or just call the async method
            hw_report = await reporter._generate_hardware_report()

            # 2. Get Performance Metrics (Real)
            perf_report = collector.get_performance_snapshot()

            # 3. Construct Pulse Package
            pulse = {
                "timestamp": datetime.now().isoformat(),
                "hardware": {
                    "cpu_usage": hw_report["cpu"]["avg_usage_percent"],
                    "ram_usage": hw_report["memory"]["usage_percent"],
                    "gpu_utilization": (
                        hw_report["gpu"].get("utilization_percent", 0) if hw_report["gpu"]["available"] else 0
                    ),
                    "gpu_temp": hw_report["gpu"].get("temperature_c", 0) if hw_report["gpu"]["available"] else 0,
                },
                "performance": {
                    "rps": perf_report["requests_per_second"],
                    "latency": perf_report["avg_response_time_ms"],
                    "errors": perf_report["error_rate"],
                },
                "brain": {
                    "active_neurons": int(hw_report["cpu"]["avg_usage_percent"] * 2.8),  # Visual proxy for now
                    "thinking_processes": hw_report["cpu"]["threads"],
                },
            }

            await websocket.send_json(pulse)
            await asyncio.sleep(1)  # 1Hz Pulse

    except WebSocketDisconnect:
        print("Dashboard disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@router.get("/comprehensive")
async def get_comprehensive_report(auth: AuthContext = Depends(require_admin)):
    """
    Generate comprehensive system report.

    Includes:
    - Hardware metrics
    - Performance analytics
    - Training progress
    - Self-evolution status
    - System health
    """
    reporter = get_reporter()
    report = await reporter.generate_full_report()
    return report


@router.get("/comprehensive/markdown")
async def get_comprehensive_report_markdown(auth: AuthContext = Depends(require_admin)):
    """Get comprehensive report as Markdown"""
    reporter = get_reporter()
    report = await reporter.generate_full_report()
    md = await reporter.generate_markdown_report(report)

    return Response(content=md, media_type="text/markdown")


@router.get("/hardware")
async def get_hardware_report(auth: AuthContext = Depends(require_admin)):
    """Get detailed hardware report"""
    reporter = get_reporter()
    return await reporter._generate_hardware_report()


@router.get("/performance")
async def get_performance_report(auth: AuthContext = Depends(require_admin)):
    """Get performance metrics report"""
    reporter = get_reporter()
    return await reporter._generate_performance_report()


@router.get("/training")
async def get_training_report(auth: AuthContext = Depends(require_admin)):
    """Get training progress report"""
    reporter = get_reporter()
    return await reporter._generate_training_report()


@router.get("/evolution")
async def get_evolution_report(auth: AuthContext = Depends(require_admin)):
    """Get self-evolution report"""
    reporter = get_reporter()
    return await reporter._generate_evolution_report()


@router.get("/health")
async def get_health_report(auth: AuthContext = Depends(require_admin)):
    """Get system health report"""
    reporter = get_reporter()
    return await reporter._generate_health_report()


@router.get("/summary")
async def get_executive_summary(auth: AuthContext = Depends(require_admin)):
    """Get executive summary"""
    reporter = get_reporter()
    report = await reporter.generate_full_report()
    return report["summary"]
