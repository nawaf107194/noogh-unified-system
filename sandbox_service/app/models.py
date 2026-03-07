from pydantic import BaseModel
from typing import Optional

class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 10
    workdir: str = "/tmp"

class ExecuteResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int
    duration_ms: float
