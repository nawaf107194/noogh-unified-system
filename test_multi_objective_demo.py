import logging
from unified_core.intelligence.multi_objective import MultiObjectiveOptimizer, Objective, MultiObjectiveOption

logging.basicConfig(level=logging.INFO)

def run_demo():
    print("=" * 70)
    print("DEMO: Multi-Objective Optimization (Balancing Conflicting Goals)")
    print("=" * 70)

    # NOOGH needs to define what it cares about
    objectives = [
        Objective("speed", minimize=False, weight=0.3),    # We want HIGH speed (weight 30%)
        Objective("security", minimize=False, weight=0.5), # We want HIGH security (weight 50%)
        Objective("cost", minimize=True, weight=0.2)       # We want LOW cost (weight 20%)
    ]
    optimizer = MultiObjectiveOptimizer(objectives)

    # Available Architectural Decisions (Options)
    options = [
        MultiObjectiveOption("A: On-Premise Single Node", {'speed': 500, 'security': 40, 'cost': 100}), # Slow, insecure, but cheap
        MultiObjectiveOption("B: Multi-Cloud K8s", {'speed': 900, 'security': 90, 'cost': 900}),       # Fast, very secure, but very expensive
        MultiObjectiveOption("C: Managed AWS Fargate", {'speed': 800, 'security': 70, 'cost': 400}),   # Balanced
        MultiObjectiveOption("D: Dummy Inefficient", {'speed': 400, 'security': 30, 'cost': 950})      # Terrible in every way
    ]

    print("\n🧐 Evaluating Architectural Options:")
    for opt in options:
        print(f" - {opt.name}: Speed={opt.scores['speed']}, Security={opt.scores['security']}, Cost={opt.scores['cost']}")

    # 1. Pareto Frontier (Eliminate strictly inferior choices)
    # Option D should be eliminated because it's worse than B in speed/security and cost.
    pareto = optimizer.find_pareto_frontier(options)
    print("\n🌟 Pareto Frontier (Rational Options to Choose From):")
    for p in pareto:
        print(f" -> {p.name}")
        
    print("\n   *(Notice that Option D was correctly eliminated without human intervention.)*")

    # 2. Extract best option based on our designated weights
    best_opt = optimizer.select_best_weighted(pareto)
    print("\n⚖️ Weighted Decision Model applied:")
    print(f"Weights: Speed (30%), Security (50%), Cost (20%) [Minimize]")
    print(f"\n🏆 The mathematically optimal choice is: {best_opt.name}")
    print(f"Calculated Weighted Score: {best_opt.normalized_scores['_weighted_total']:.2f}/1.00")

    # 3. Transparent Trade-off Analysis
    # Let's say a human asked: "Why not choose Option B (Multi-Cloud) instead of C (Balanced AWS)?"
    # We compare C to B
    print("\n📊 Trade-off Explanation (Choosing C instead of B):")
    tradeoffs = optimizer.calculate_tradeoffs(options[2], options[1]) # Compare C vs B
    
    for gain in tradeoffs['choosing_A_instead_of_B_gains']:
        print(f"  + GAIN: Save {gain}")
    for loss in tradeoffs['choosing_A_instead_of_B_loses']:
        print(f"  - LOSE: Sacrifice {loss}")

if __name__ == "__main__":
    run_demo()
