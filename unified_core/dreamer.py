import threading
import time
import logging
from typing import Optional
from .state import get_state
# NOTE: meta_learning was archived (unused) - import removed

logger = logging.getLogger("unified_core.dreamer")

class Dreamer:
    """
    Background component that previously 'dreamed' up goals.
    
    COGNITIVE AUTHORITY TRANSFERRED to GravityWell.
    
    This class now operates as a THIN WRAPPER that:
    1. Periodically invokes GravityWell.generate_goals()
    2. Reports on scar depth and decision count
    3. Does NOT make autonomous decisions
    
    The dreaming is now genuine: goals emerge from WorldModel beliefs,
    not from Q-table policies.
    """
    
    def __init__(self, interval_seconds: float = 60.0):
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        # GravityWell reference (set during initialization)
        self._gravity_well = None
        
        # Track metrics (for observability, not decisions)
        self._cycle_count = 0

    def set_gravity_well(self, gravity_well):
        """Set reference to GravityWell for goal delegation."""
        self._gravity_well = gravity_well
        logger.info("Dreamer: GravityWell reference set - goals will be genuine")

    def start(self):
        """Start the dreamer loop in a background thread."""
        if self._running:
            return
            
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._dream_loop, name="DreamerThread", daemon=True)
        self._thread.start()
        logger.info("Dreamer started - delegating to GravityWell for genuine goal synthesis")

    def stop(self):
        """Stop the dreamer."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Dreamer stopped")

    def _dream_loop(self):
        """Main loop that periodically analyzes state and creates goals."""
        while not self._stop_event.is_set():
            try:
                self._dream()
            except Exception as e:
                logger.error(f"Error in Dreamer loop: {e}")
            
            # Sleep for interval or until stopped
            if self._stop_event.wait(timeout=self._interval):
                break

    def _calculate_health(self, avg_risk: float, failure_rate: float) -> float:
        """
        Calculate generic system health score [0.0 - 1.0].
        Higher is better.
        """
        # Risk 1.0 -> Health 0.0
        # Fail 1.0 -> Health 0.0
        return 1.0 - ((avg_risk * 0.5) + (failure_rate * 0.5))
    
    # Phase 2 v13.5.5: Public API for external invocation
    async def dream(self):
        """Public API to trigger dream cycle (delegates to _dream)."""
        await self._dream()

    async def _dream(self):
        """
        COGNITIVE AUTHORITY DELEGATED TO GRAVITY_WELL.
        
        Previous implementation used MetaGoalAgent (Q-table) to choose goals.
        That was NOT dreaming. It was policy lookup.
        
        Now: Goals emerge from WorldModel via GravityWell.generate_goals()
        """
        self._cycle_count += 1
        logger.info(f"Dreamer cycle {self._cycle_count} - delegating to GravityWell")
        
        # Check if GravityWell is available
        if self._gravity_well is None:
            logger.warning("Dreamer: No GravityWell reference - cannot generate genuine goals")
            return
        
        # Delegate goal synthesis to GravityWell
        try:
            generated_goals = await self._gravity_well.generate_goals()
            
            if generated_goals:
                logger.info(f"GravityWell generated {len(generated_goals)} genuine goals")
                for goal in generated_goals:
                    logger.info(f"  - {goal.description} (priority={goal.priority:.2f})")
            else:
                logger.info("GravityWell: No new goals needed at this time")
                
        except Exception as e:
            logger.error(f"Error in GravityWell goal synthesis: {e}")
            
            # If GravityWell has ScarTissue, this failure should scar
            if hasattr(self._gravity_well, '_scars') and self._gravity_well._scars:
                from unified_core.core.scar import Failure
                import hashlib
                import time
                
                failure = Failure(
                    failure_id=hashlib.sha256(
                        f"dreamer_failure:{self._cycle_count}:{time.time()}".encode()
                    ).hexdigest()[:16],
                    action_type="goal_synthesis",
                    action_params={"cycle": self._cycle_count},
                    error_message=str(e)
                )
                self._gravity_well._scars.inflict(failure)
                logger.warning(f"Dreamer failure scarred the system")

    def _discover_new_goals(self, state, history):
        """
        Scan history for metrics that correlate with issues but have no goals.
        This provides Open-Endedness (Goal Discovery).
        """
        # Simplistic Discovery Logic:
        # If we see a metric tracked in state that is NOT 'average_risk' or 'success_rate',
        # and it seems high, we invent a goal for it.
        
        known_metrics = ["average_risk", "success_rate", "adaptation_count", "uptime", "failures"]
        
        # Check snapshot keys
        snapshot = state.snapshot()
        for key, value in snapshot.items():
            if isinstance(value, (int, float)) and key not in known_metrics:
                # Potential candidate!
                # If value is 'high' (arbitrary threshold for demo context > 50)
                if value > 50.0:
                    action_name = f"SET_GOAL_OPTIMIZE_{key.upper()}"
                    
                    # Register this new goal possibility with the Meta-Agent
                    # The Agent won't choose it immediately, but it becomes an OPTION.
                    # Exploration will eventually try it.
                    if action_name not in self._meta_agent.actions.values():
                        logger.warning(f"Dreamer Discovery: Found high metric '{key}' ({value}). Inventing new goal type.")
                        self._meta_agent.register_action(action_name)

    def _update_goal_progress(self, state, goals):
        """Auto-update progress for known metrics."""
        # Risk Goal
        if "Stabilize Risk" in goals and goals["Stabilize Risk"]["status"] == "active":
            _, avg = state.get_risk_trend()
            state.update_goal_progress("Stabilize Risk", avg)
            # Check if achieved (inverse logic: value <= target)
            if avg <= 0.5:
                 # Manually marking achieved because the default logic is >= target
                 # We might need to enhance goal logic later for 'min' vs 'max' targets
                 # For now, let's rely on the update_goal_progress simple check or override here
                 pass # The state.update_goal_progress uses >= logic. 
                      # TODO: Enhance Goal struct to support 'Minimize' type goals.
