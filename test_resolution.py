import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    from unified_core.bridge import UnifiedCoreBridge
    from unified_core.core.planning_engine import PlanningEngine
    
    bridge = UnifiedCoreBridge()
    await bridge.initialize()
    
    if hasattr(bridge, '_gravity_well') and bridge._gravity_well:
        gravity = bridge._gravity_well
        
        # Give it a fake goal
        from unified_core.core.gravity import Goal
        import hashlib, time
        
        desc = "Verify or strengthen: Fake Test Goal"
        goal_id = hashlib.sha256(f"fake:{time.time()}".encode()).hexdigest()[:16]
        fp = gravity._compute_goal_fingerprint(desc)
        
        goal = Goal(
            goal_id=goal_id,
            description=desc,
            derived_from_beliefs=[],
            derived_from_discrepancy="fake",
            fingerprint=fp
        )
        gravity._commit_goal(goal)
        
        # Check active goals
        active = gravity.get_active_goals()
        print(f"Active Goals: {len(active)}")
        
        # Planner
        planner = PlanningEngine(world_model=bridge._world_model)
        planner._gravity = gravity
        
        # Simulate planning engine
        plan = planner.create_plan(f"[Synthetic:GravityWell] {desc}")
        
        # Mark tasks complete
        for task in plan.tasks:
            from unified_core.core.planning_engine import TaskStatus
            task.status = TaskStatus.COMPLETED
            
        # Finalize plan (this should resolve the goal)
        plan.started_at = time.time()
        planner._finalize_plan(plan)
        
        # Check active goals again
        active_after = gravity.get_active_goals()
        print(f"Active Goals after finalize: {len(active_after)}")

if __name__ == "__main__":
    asyncio.run(test())
