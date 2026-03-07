from fastapi import FastAPI, HTTPException
import logging
import os
from sandbox_service.app.core.sandbox_impl import DockerSandboxService
from sandbox_service.app.models import ExecuteRequest, ExecuteResponse

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sandbox_service")

app = FastAPI(title="Noogh Sandbox Service")

# Initialize Service
# This service OWNS the docker socket connection
try:
    sandbox = DockerSandboxService()
except Exception as e:
    logger.critical(f"Failed to init Docker Sandbox: {e}")
    sandbox = None

@app.post("/execute", response_model=ExecuteResponse)
async def execute_endpoint(req: ExecuteRequest):
    if not sandbox:
        raise HTTPException(status_code=503, detail="Sandbox Engine Unavailable")
        
    result = sandbox.execute_code(req.code, req.language, req.timeout)
    return result

@app.get("/health")
def health():
    if not sandbox:
        return {"status": "unhealthy", "error": "No Docker Connection"}
    return {"status": "healthy"}
