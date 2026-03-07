from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Set


class Capability(str, Enum):
    CODE_EXEC = "code_exec"
    FS_READ = "fs_read"
    FS_WRITE = "fs_write"
    CODE_ANALYZE = "code_analyze"  # Read-only analysis
    PROJECT_PLAN = "project_plan"  # Planning mode
    OBSERVABILITY_READ = "observability_read"  # Metrics/Health
    REPORT_WRITE = "report_write"

    # Forbidden
    INTERNET = "internet"
    SHELL = "shell"


PLUGIN_SAFE_CAPABILITIES = {Capability.FS_READ, Capability.CODE_ANALYZE, Capability.REPORT_WRITE}


@dataclass(frozen=True)
class CapabilityRequirement:
    required: Set[str]
    forbidden: Set[str]
    mode: Literal["EXECUTE", "PLAN", "REJECT"]
    reason: str
    constraints: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RefusalResponse:
    code: str  # CapabilityBoundaryViolation | AmbiguousIntent | ForbiddenRequest
    message: str
    allowed_alternatives: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
