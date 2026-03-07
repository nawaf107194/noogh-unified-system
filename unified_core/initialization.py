"""
Startup Initialization Barrier

CRITICAL SECURITY COMPONENT
Prevents ANY execution before FULL system initialization completes.

This prevents partial-initialization attacks where:
- Requests arrive before auth is configured
- Actuators execute before allowlists are loaded
- Services start before integrity verification

DESIGN:
- Global singleton tracks component initialization state
- Required components MUST register and mark ready
- All entry points MUST call wait_for_startup() or require_ready()
- Timeout triggers emergency shutdown
"""
import threading
import time
import logging
from enum import Enum
from typing import Set, Dict

logger = logging.getLogger(__name__)


class ComponentState(Enum):
    """Initialization states for system components."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"


class InitializationBarrier:
    """
    Global barrier preventing execution before full initialization.
    
    SECURITY: This is a MANDATORY gate. Bypassing this barrier = system compromise.
    """
    
    _lock = threading.Lock()
    _components: Dict[str, ComponentState] = {}
    _startup_complete = False
    _failure_reason: str = None
    
    # Required components that MUST be ready before processing requests
    REQUIRED_COMPONENTS = {
        "config",           # Configuration loaded and verified
        "config_integrity", # Allowlists integrity verified
        "auth",            # Auth tokens registered and sealed
        "actuators",       # Actuators initialized with AMLA
    }
    
    @classmethod
    def register_component(cls, name: str):
        """
        Register a component as initializing.
        
        Args:
            name: Component identifier
            
        Raises:
            RuntimeError: If startup already complete
        """
        with cls._lock:
            if cls._startup_complete:
                raise RuntimeError(
                    f"Cannot register {name}: startup already complete"
                )
            cls._components[name] = ComponentState.INITIALIZING
            logger.info(f"Component registered: {name}")
    
    @classmethod
    def mark_ready(cls, name: str):
        """
        Mark a component as ready.
        
        Args:
            name: Component identifier
            
        Raises:
            RuntimeError: If component not registered
        """
        with cls._lock:
            if name not in cls._components:
                raise RuntimeError(f"Component {name} not registered")
            cls._components[name] = ComponentState.READY
            logger.info(f"✓ Component ready: {name}")
    
    @classmethod
    def mark_failed(cls, name: str, error: str):
        """
        Mark a component as failed.
        
        Args:
            name: Component identifier
            error: Failure reason
            
        Raises:
            RuntimeError: Always (failure is fatal)
        """
        with cls._lock:
            cls._components[name] = ComponentState.FAILED
            cls._failure_reason = error
            logger.critical(f"❌ Component FAILED: {name} - {error}")
            raise RuntimeError(
                f"FATAL: Component {name} failed to initialize: {error}"
            )
    
    @classmethod
    def wait_for_startup(cls, timeout: float = 30.0):
        """
        Block until all required components are ready.
        
        CRITICAL: This MUST complete before processing any requests.
        
        Args:
            timeout: Maximum seconds to wait
            
        Raises:
            RuntimeError: If timeout or component failure
        """
        start = time.time()
        
        while True:
            with cls._lock:
                # Check for missing components
                missing = cls.REQUIRED_COMPONENTS - set(cls._components.keys())
                if missing:
                    if time.time() - start > timeout:
                        raise RuntimeError(
                            f"Startup timeout. Missing components: {missing}"
                        )
                    time.sleep(0.1)
                    continue
                
                # Check for failed components
                failed = [
                    name for name, state in cls._components.items()
                    if state == ComponentState.FAILED
                ]
                if failed:
                    raise RuntimeError(
                        f"Startup failed. Failed components: {failed}. "
                        f"Reason: {cls._failure_reason}"
                    )
                
                # Check for components not ready
                not_ready = [
                    name for name, state in cls._components.items()
                    if state != ComponentState.READY
                ]
                if not_ready:
                    if time.time() - start > timeout:
                        raise RuntimeError(
                            f"Startup timeout. Not ready: {not_ready}"
                        )
                    time.sleep(0.1)
                    continue
                
                # All components ready!
                cls._startup_complete = True
                logger.info("🚀 System initialization COMPLETE - all components ready")
                return
    
    @classmethod
    def require_ready(cls):
        """
        Enforce that startup is complete before proceeding.
        
        MUST be called at entry points (API routes, daemon loops, etc).
        
        Raises:
            RuntimeError: If system not initialized
        """
        if not cls._startup_complete:
            raise RuntimeError(
                "SECURITY: System not initialized. "
                "Call wait_for_startup() before processing requests."
            )
    
    @classmethod
    def get_status(cls) -> Dict[str, str]:
        """
        Get current initialization status.
        
        Returns:
            Dict mapping component names to state strings
        """
        with cls._lock:
            return {
                name: state.value
                for name, state in cls._components.items()
            }
    
    @classmethod
    def is_ready(cls) -> bool:
        """Check if startup is complete."""
        return cls._startup_complete
