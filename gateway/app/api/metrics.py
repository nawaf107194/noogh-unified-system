from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

router = APIRouter()

# Existing
REQUEST_COUNT = Counter("noogh_request_count", "Total request count", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("noogh_request_latency_seconds", "Request latency", ["method", "endpoint"])

# New Observability Metrics
JOBS_SUBMITTED = Counter("noogh_jobs_submitted_total", "Total number of jobs submitted")

JOBS_RUNNING = Gauge("noogh_jobs_running", "Current number of running jobs")

JOBS_COMPLETED = Counter(
    "noogh_jobs_completed_total", "Total number of completed jobs", ["status"]  # succeeded, failed, rejected, cancelled
)

PLUGINS_LOADED = Counter("noogh_plugins_loaded_total", "Plugin load events", ["status"])  # success, fail


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def metrics_endpoint():
    # Alias if needed for import compatibility
    return metrics
