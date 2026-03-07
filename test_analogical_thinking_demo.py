import logging
from unified_core.intelligence.analogical import AnalogicalReasoner, Situation

logging.basicConfig(level=logging.INFO)

def run_demo():
    reasoner = AnalogicalReasoner()

    print("=" * 70)
    print("DEMO 1: Database Congestion translated from Urban Traffic")
    print("=" * 70)

    # 1. Target Situation that the AI is facing
    current_problem = Situation(
        name="Slow Database Queries",
        domain="database_systems",
        description="The database takes 120ms per query because the joined tables create a massive bottleneck for requests waiting.",
        entities=["requests", "join_tables", "engine"],
        relationships={"requests": "wait for", "join_tables": "block"}
    )
    
    analogies = reasoner.find_analogies(current_problem, top_k=2)

    for match in analogies:
        print(f"\n💡 Analogy Match Found:")
        print(f"   Domain: {match.source_situation.domain} ({match.source_situation.name})")
        print(f"   Similarity: {match.similarity_score:.2f}/1.00")
        print(f"   Abstract Core: {current_problem.extract_structure()['core_problem']}")
        print(f"\n{match.mapped_solution}")

    print("\n" + "=" * 70)
    print("DEMO 2: Zero-Day AI Defense translated from Biological Immunity")
    print("=" * 70)

    security_problem = Situation(
        name="Zero-Day Model Poisoning Attack",
        domain="ai_security",
        description="A massive burst of adversarial inputs is overwhelming the parser before the detection module can catch them, causing crashes.",
        entities=["adversarial_inputs", "parser", "detection_module"],
        relationships={"adversarial_inputs": "overwhelm", "parser": "crashes"}
    )
    
    sec_analogies = reasoner.find_analogies(security_problem, top_k=1)
    
    for match in sec_analogies:
        print(f"\n💡 Analogy Match Found:")
        print(f"   Domain: {match.source_situation.domain} ({match.source_situation.name})")
        print(f"   Similarity: {match.similarity_score:.2f}/1.00")
        print(f"   Abstract Core: {security_problem.extract_structure()['core_problem']}")
        print(f"\n{match.mapped_solution}")


if __name__ == "__main__":
    run_demo()
