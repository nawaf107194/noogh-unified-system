from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class CommandRequest(BaseModel):
    command: str


class ReActThought(BaseModel):
    """Schema for Agent's internal reasoning step."""
    thought: str = Field(..., min_length=5, description="Internal reasoning about the task")
    action: str = Field(..., pattern=r"^[a-zA-Z_]+$", description="Tool to execute")
    action_input: str = Field(..., description="Input for the tool")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed_actions = ["ExecuteCode", "ExecuteShell", "ShellExecutor", "RecallMemory", "StoreMemory", "Dream"]
        if v not in allowed_actions:
            raise ValueError(f"Action '{v}' is not a valid tool. Allowed: {allowed_actions}")
        return v

class ToolExecutionRequest(BaseModel):
    """Schema for executing a tool."""
    tool_name: str
    tool_input: str
    # Remove 'allowed' flag - authorization happens via token context

class ExecutionResponse(BaseModel):
    """Schema for tool execution result."""
    output: str
    status: str
    command: Optional[str] = None
    error: Optional[str] = None
