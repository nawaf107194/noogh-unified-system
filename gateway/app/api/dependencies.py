from fastapi import Request

from gateway.app.core.jobs import get_job_store


def job_store_provider(request: Request):
    """Provide JobStore with injected secrets."""
    secrets = getattr(request.app.state, "secrets", {})
    return get_job_store(secrets=secrets)
