"""
Unified Module Interface for Noug Neural OS
Provides standard contract for all system modules
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Standard module status states"""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class ModulePriority(Enum):
    """Module execution priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ModuleMetadata:
    """Standard metadata for all modules"""

    name: str
    version: str
    description: str
    dependencies: List[str]
    priority: ModulePriority
    capabilities: List[str]

    def to_dict(self) -> Dict[str, Any]:
            result = {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "dependencies": self.dependencies if self.dependencies is not None else [],
                "priority": getattr(self.priority, "name", "Unknown"),
                "capabilities": self.capabilities if self.capabilities is not None else {},
            }
            return result


@dataclass
class ProcessingResult:
    """Standard result format for module processing"""

    success: bool
    data: Any
    metadata: Dict[str, Any]
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors or [],
            "warnings": self.warnings or [],
        }


class ModuleInterface(ABC):
    """
    Base interface that all Noug modules must implement
    Ensures consistent behavior and communication across the system
    """

    def __init__(self):
        self._status = ModuleStatus.UNINITIALIZED
        self._metadata: Optional[ModuleMetadata] = None
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_metadata(self) -> ModuleMetadata:
        """Return module metadata"""

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the module with configuration

        Args:
            config: Module-specific configuration

        Returns:
            True if initialization successful
        """

    @abstractmethod
    async def process(self, input_data: Any, context: Dict[str, Any]) -> ProcessingResult:
        """
        Process input data with context

        Args:
            input_data: Data to process
            context: Execution context

        Returns:
            ProcessingResult with output and metadata
        """

    @abstractmethod
    async def validate_input(self, input_data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate input data before processing

        Args:
            input_data: Data to validate

        Returns:
            (is_valid, error_message)
        """

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current module status and health metrics

        Returns:
            Status dictionary with health information
        """

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Gracefully shutdown the module

        Returns:
            True if shutdown successful
        """

    # Common helper methods
    def set_status(self, status: ModuleStatus):
        """Update module status"""
        self._status = status
        self._logger.info(f"Status changed to: {status.value}")

    def get_current_status(self) -> ModuleStatus:
        """Get current status"""
        return self._status

    def is_ready(self) -> bool:
        """Check if module is ready for processing"""
        return self._status == ModuleStatus.READY

    def log_error(self, error: str, exception: Optional[Exception] = None):
        """Log error with optional exception"""
        self._logger.error(f"{error}", exc_info=exception)
        self.set_status(ModuleStatus.ERROR)

    def log_warning(self, warning: str):
        """Log warning"""
        self._logger.warning(warning)

    def log_info(self, info: str):
        """Log info"""
        self._logger.info(info)
