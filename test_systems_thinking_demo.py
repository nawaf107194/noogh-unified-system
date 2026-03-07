import logging
from unified_core.intelligence.systems_thinking import SystemsThinker, SystemNode, CausalLink, FeedbackLoop

logging.basicConfig(level=logging.INFO)
thinker = SystemsThinker()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Analyzing Tech Debt as a System (The Vicious Cycle)")
    print("=" * 70)
    
    # Define a classic "Technical Debt Escalation" system
    nodes = [
        SystemNode("Feature Pressure", "Demand for new features", 80.0), # High demand
        SystemNode("Hack Fixes", "Quick, dirty code solutions", 50.0),
        SystemNode("Technical Debt", "Accumulation of bad architecture", 90.0),
        SystemNode("Bugs/Incidents", "System failures caused by debt", 40.0),
        SystemNode("Time Spent Fixing", "Engineering capacity drained", 70.0),
        SystemNode("Engineering Velocity", "Speed of delivering new properly", 20.0),
    ]
    
    links = [
        # +1 means increase A causes increase B. -1 means increase A causes decrease B.
        # Demand increases hack fixes (to meet deadlines)
        CausalLink("Feature Pressure", "Hack Fixes", 1, 0.8),
        # Hack fixes increase Tech Debt long term (delayed)
        CausalLink("Hack Fixes", "Technical Debt", 1, 0.9, delay=True),
        # Debt increases Bugs
        CausalLink("Technical Debt", "Bugs/Incidents", 1, 0.7),
        # Bugs demand more Time Spent Fixing
        CausalLink("Bugs/Incidents", "Time Spent Fixing", 1, 0.9),
        # More Time Fixing means LESS Engineering Velocity (-1)
        CausalLink("Time Spent Fixing", "Engineering Velocity", -1, 0.8),
        # Less velocity increases Feature Pressure (because deadlines are missed and backlog grows! -1)
        CausalLink("Engineering Velocity", "Feature Pressure", -1, 0.9),
    ]
    
    thinker.load_system_model(nodes, links)

    print("🌐 System Model Loaded: The Technical Debt Cycle")
    
    # Detect all closed loops that drive the system's underlying nature
    loops = thinker.detect_feedback_loops()
    print("\n-- 🔄 Detected Feedback Loops --")
    for loop in loops:
        print(f"Cycle: {' -> '.join(loop.nodes)} -> (back to {loop.nodes[0]})")
        print(f"Type: {loop.loop_type}")
        print(f"Structural Significance: {loop.significance:.2f}\n")

    # Find where we should intervene
    leverage_points = thinker.identify_leverage_points()
    print("-- 🚀 Identified System Leverage Points (Where to intervene) --")
    
    for pt in leverage_points[:3]: # Show top 3
        print(f"Lever: {pt['node']}")
        print(f"   Score: {pt['leverage_score']:.2f}")
        print(f"   Reasoning: {pt['reasoning']}")
        
    print("\n💡 Conclusion: The highest leverage is not 'working harder' (more Feature Pressure),")
    print("            but interrupting 'Hack Fixes' (the root entry point) to break the Reinforcing Snowball cycle down the chain.")

if __name__ == "__main__":
    run_demo()
