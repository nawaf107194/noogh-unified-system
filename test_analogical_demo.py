import logging
from unified_core.intelligence.analogical import AnalogicalReasoner

logging.basicConfig(level=logging.INFO)
reasoner = AnalogicalReasoner()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Database Latency Problem")
    print("=" * 70)
    
    situation = "The database is extremely slow due to too many complex joins waiting on index bottlenecks"
    print(f"Current Situation: {situation}")
    
    analogies = reasoner.find_analogies(situation, target_domain="Software Engineering")
    
    if not analogies:
        print("No structural analogies found.")
    
    for i, analogy in enumerate(analogies, 1):
        print(f"\n🧠 Analogy #{i} (Score: {analogy.similarity_score:.2f})")
        print(f"Source Domain: {analogy.source_domain}")
        print(f"Analogous Situation: {analogy.source_situation.description}")
        print(f"Concept Transferred: {analogy.transferable_knowledge}")
        print(f"🛠️  Adapted Suggestion for our domain: {analogy.adapted_solution}")

    print("\n" + "=" * 70)
    print("DEMO 2: Cybersecurity Breach Scenario")
    print("=" * 70)
    
    sec_situation = "Malicious actors are attempting to attack the server by exploiting known vulnerable endpoints"
    print(f"Current Situation: {sec_situation}")
    
    sec_analogies = reasoner.find_analogies(sec_situation, target_domain="Software Engineering")
    
    for i, analogy in enumerate(sec_analogies, 1):
        print(f"\n🧠 Analogy #{i} (Score: {analogy.similarity_score:.2f})")
        print(f"Source Domain: {analogy.source_domain}")
        print(f"Analogous Situation: {analogy.source_situation.description}")
        print(f"Concept Transferred: {analogy.transferable_knowledge}")
        print(f"🛠️  Adapted Suggestion for our domain: {analogy.adapted_solution}")

if __name__ == "__main__":
    run_demo()
