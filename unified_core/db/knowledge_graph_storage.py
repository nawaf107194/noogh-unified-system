# unified_core/db/knowledge_graph_storage.py

from unified_core.db.router import DataRouter
from unified_core.db.vector_db import VectorDBManager

class KnowledgeGraphStorage:
    def __init__(self):
        self.router = DataRouter()
        self.vector_db_manager = VectorDBManager()

    def store_innovation(self, innovation_data):
        # Store innovation data in a structured format
        self.vector_db_manager.store_document(innovation_data)

    def store_belief(self, belief_data):
        # Store belief data in a structured format
        self.vector_db_manager.store_document(belief_data)

    def store_outcome(self, outcome_data):
        # Store outcome data in a structured format
        self.vector_db_manager.store_document(outcome_data)

    def query_knowledge_graph(self, query):
        # Query the knowledge graph and return results
        return self.vector_db_manager.query(query)

if __name__ == '__main__':
    kg_storage = KnowledgeGraphStorage()
    
    innovation = {
        "id": 1,
        "type": "innovation",
        "description": "New AI algorithm for prediction"
    }
    
    belief = {
        "id": 1,
        "type": "belief",
        "content": "Market is expected to rise"
    }
    
    outcome = {
        "id": 1,
        "type": "outcome",
        "result": "Positive market movement"
    }
    
    kg_storage.store_innovation(innovation)
    kg_storage.store_belief(belief)
    kg_storage.store_outcome(outcome)
    
    query = """
    MATCH (n:Innovation)-[:HAS_BELIEF]->(b:Belief), (n)->[:HAS_OUTCOME]->(o:Outcome)
    RETURN n, b, o
    """
    
    results = kg_storage.query_knowledge_graph(query)
    print(results)