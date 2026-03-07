"""
Graph Database Manager - Entity Relationships
Neo4j interface for knowledge graphs and relationship mapping
"""
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("unified_core.db.graph")


@dataclass
class Node:
    id: str
    labels: List[str]
    properties: Dict[str, Any]


@dataclass
class Relationship:
    id: str
    type: str
    start_node: str
    end_node: str
    properties: Dict[str, Any]


@dataclass
class GraphPath:
    nodes: List[Node]
    relationships: List[Relationship]
    length: int


@dataclass
class GraphQueryResult:
    success: bool
    nodes: List[Node] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    paths: List[GraphPath] = field(default_factory=list)
    data: Optional[List[Dict]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class RelationType(Enum):
    # Agent relationships
    OWNS = "OWNS"
    CREATED_BY = "CREATED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    
    # Knowledge relationships
    IS_A = "IS_A"
    HAS_PROPERTY = "HAS_PROPERTY"
    RELATED_TO = "RELATED_TO"
    CAUSES = "CAUSES"
    PART_OF = "PART_OF"
    
    # Temporal relationships
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    DURING = "DURING"
    
    # Causal relationships
    ENABLES = "ENABLES"
    PREVENTS = "PREVENTS"
    REQUIRES = "REQUIRES"


# SECURITY: Regex for safe identifiers (letters, numbers, underscore only)
import re
_SAFE_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def _sanitize_label(label: str) -> str:
    """Sanitize label to prevent Cypher injection."""
    if not _SAFE_IDENTIFIER.match(label):
        raise ValueError(f"Invalid label '{label}': must be alphanumeric with underscores")
    return label

def _sanitize_rel_type(rel_type: str) -> str:
    """Sanitize relationship type to prevent Cypher injection."""
    if not _SAFE_IDENTIFIER.match(rel_type):
        raise ValueError(f"Invalid relationship type '{rel_type}': must be alphanumeric with underscores")
    return rel_type


class GraphDBManager:
    """
    Neo4j graph database manager for entity relationships.
    Maps complex relationships between agents, concepts, and actions.
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
        use_memory_fallback: bool = True
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.max_pool_size = max_connection_pool_size
        self.use_memory_fallback = use_memory_fallback
        
        self._driver = None
        self._initialized = False
        self._using_memory = False
        
        # In-memory fallback
        self._memory_nodes: Dict[str, Node] = {}
        self._memory_relationships: Dict[str, Relationship] = {}
        self._memory_adjacency: Dict[str, Set[str]] = {}
    
    async def initialize(self) -> bool:
        """Initialize Neo4j connection."""
        if self._initialized:
            return True
        
        try:
            from neo4j import AsyncGraphDatabase
            
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.max_pool_size
            )
            
            # Verify connection
            async with self._driver.session(database=self.database) as session:
                await session.run("RETURN 1")
            
            self._initialized = True
            logger.info("Neo4j initialized")
            return True
            
        except Exception as e:
            logger.warning(f"Neo4j unavailable: {e}, using memory fallback")
            if self.use_memory_fallback:
                self._using_memory = True
                self._initialized = True
                return True
            return False
    
    async def close(self):
        """Close driver connection."""
        if self._driver:
            await self._driver.close()
            self._initialized = False
    
    async def execute_cypher(self, query: str, params: Optional[Dict] = None) -> GraphQueryResult:
        """Execute raw Cypher query."""
        import time
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        if self._using_memory:
            return GraphQueryResult(
                success=False,
                error="Cypher queries not supported in memory mode",
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
        
        try:
            async with self._driver.session(database=self.database) as session:
                result = await session.run(query, params or {})
                records = await result.data()
                
                return GraphQueryResult(
                    success=True,
                    data=records,
                    execution_time_ms=(time.perf_counter() - start) * 1000
                )
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return GraphQueryResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
    
    async def create_node(
        self,
        node_id: str,
        labels: List[str],
        properties: Dict[str, Any]
    ) -> bool:
        """Create a node with labels and properties."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._using_memory:
                self._memory_nodes[node_id] = Node(
                    id=node_id, labels=labels, properties=properties
                )
                return True
            
            # SECURITY FIX: Sanitize labels to prevent Cypher injection
            sanitized_labels = [_sanitize_label(l) for l in labels]
            label_str = ":".join(sanitized_labels)
            query = f"""
                MERGE (n:{label_str} {{id: $id}})
                SET n += $props
                RETURN n
            """
            result = await self.execute_cypher(query, {"id": node_id, "props": properties})
            return result.success
            
        except Exception as e:
            logger.error(f"Create node failed: {e}")
            return False
    
    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: Union[RelationType, str],
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between two nodes."""
        import uuid
        
        if not self._initialized:
            await self.initialize()
        
        rel_type_str = rel_type.value if isinstance(rel_type, RelationType) else rel_type
        
        try:
            if self._using_memory:
                rel_id = str(uuid.uuid4())[:8]
                self._memory_relationships[rel_id] = Relationship(
                    id=rel_id,
                    type=rel_type_str,
                    start_node=from_id,
                    end_node=to_id,
                    properties=properties or {}
                )
                # Update adjacency
                if from_id not in self._memory_adjacency:
                    self._memory_adjacency[from_id] = set()
                self._memory_adjacency[from_id].add(to_id)
                return True
            
            # SECURITY FIX: Sanitize relationship type to prevent Cypher injection
            sanitized_rel_type = _sanitize_rel_type(rel_type_str)
            query = f"""
                MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                MERGE (a)-[r:{sanitized_rel_type}]->(b)
                SET r += $props
                RETURN r
            """
            result = await self.execute_cypher(
                query,
                {"from_id": from_id, "to_id": to_id, "props": properties or {}}
            )
            return result.success
            
        except Exception as e:
            logger.error(f"Create relationship failed: {e}")
            return False
    
    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        if self._using_memory:
            return self._memory_nodes.get(node_id)
        
        result = await self.execute_cypher(
            "MATCH (n {id: $id}) RETURN n",
            {"id": node_id}
        )
        
        if result.success and result.data:
            n = result.data[0]["n"]
            return Node(id=node_id, labels=list(n.labels), properties=dict(n))
        return None
    
    async def get_neighbors(
        self,
        node_id: str,
        rel_type: Optional[Union[RelationType, str]] = None,
        direction: str = "both"  # "in", "out", "both"
    ) -> List[Node]:
        """Get neighboring nodes."""
        if self._using_memory:
            neighbors = []
            for rel in self._memory_relationships.values():
                if rel_type and rel.type != (rel_type.value if isinstance(rel_type, RelationType) else rel_type):
                    continue
                if direction in ("out", "both") and rel.start_node == node_id:
                    if rel.end_node in self._memory_nodes:
                        neighbors.append(self._memory_nodes[rel.end_node])
                if direction in ("in", "both") and rel.end_node == node_id:
                    if rel.start_node in self._memory_nodes:
                        neighbors.append(self._memory_nodes[rel.start_node])
            return neighbors
        
        rel_pattern = f":{rel_type.value if isinstance(rel_type, RelationType) else rel_type}" if rel_type else ""
        
        if direction == "out":
            pattern = f"(a)-[{rel_pattern}]->(b)"
        elif direction == "in":
            pattern = f"(a)<-[{rel_pattern}]-(b)"
        else:
            pattern = f"(a)-[{rel_pattern}]-(b)"
        
        result = await self.execute_cypher(
            f"MATCH {pattern} WHERE a.id = $id RETURN DISTINCT b",
            {"id": node_id}
        )
        
        if result.success and result.data:
            return [
                Node(id=r["b"]["id"], labels=list(r["b"].labels), properties=dict(r["b"]))
                for r in result.data
            ]
        return []
    
    async def find_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 5
    ) -> Optional[GraphPath]:
        """Find shortest path between two nodes."""
        if self._using_memory:
            # BFS for shortest path
            from collections import deque
            visited = {from_id}
            queue = deque([(from_id, [from_id], [])])
            
            while queue:
                current, path_nodes, path_rels = queue.popleft()
                
                if current == to_id:
                    nodes = [self._memory_nodes[n] for n in path_nodes if n in self._memory_nodes]
                    rels = [self._memory_relationships[r] for r in path_rels if r in self._memory_relationships]
                    return GraphPath(nodes=nodes, relationships=rels, length=len(rels))
                
                if len(path_nodes) > max_depth:
                    continue
                
                for rel_id, rel in self._memory_relationships.items():
                    next_node = None
                    if rel.start_node == current and rel.end_node not in visited:
                        next_node = rel.end_node
                    elif rel.end_node == current and rel.start_node not in visited:
                        next_node = rel.start_node
                    
                    if next_node:
                        visited.add(next_node)
                        queue.append((next_node, path_nodes + [next_node], path_rels + [rel_id]))
            
            return None
        
        result = await self.execute_cypher(
            f"""
            MATCH p = shortestPath((a {{id: $from}})-[*..{max_depth}]-(b {{id: $to}}))
            RETURN p
            """,
            {"from": from_id, "to": to_id}
        )
        
        if result.success and result.data:
            # Parse Neo4j path
            path = result.data[0]["p"]
            nodes = [Node(id=n["id"], labels=list(n.labels), properties=dict(n)) for n in path.nodes]
            rels = [
                Relationship(
                    id=str(r.id), type=r.type,
                    start_node=r.start_node["id"], end_node=r.end_node["id"],
                    properties=dict(r)
                ) for r in path.relationships
            ]
            return GraphPath(nodes=nodes, relationships=rels, length=len(rels))
        return None
    
    # Knowledge graph specialized methods
    async def add_concept(
        self,
        concept_id: str,
        name: str,
        description: str,
        parent_concept: Optional[str] = None
    ) -> bool:
        """Add a concept to the knowledge graph."""
        success = await self.create_node(
            concept_id,
            ["Concept"],
            {"name": name, "description": description}
        )
        
        if success and parent_concept:
            await self.create_relationship(
                concept_id, parent_concept, RelationType.IS_A
            )
        return success
    
    async def add_causal_link(
        self,
        cause_id: str,
        effect_id: str,
        confidence: float = 1.0
    ) -> bool:
        """Add causal relationship between concepts."""
        return await self.create_relationship(
            cause_id, effect_id, RelationType.CAUSES,
            {"confidence": confidence}
        )
    
    async def get_causal_chain(
        self,
        start_concept: str,
        max_depth: int = 10
    ) -> List[Node]:
        """Get causal chain starting from a concept."""
        if self._using_memory:
            chain = []
            current = start_concept
            visited = set()
            
            while current and len(chain) < max_depth:
                if current in visited:
                    break
                visited.add(current)
                
                if current in self._memory_nodes:
                    chain.append(self._memory_nodes[current])
                
                # Find next causal link
                next_node = None
                for rel in self._memory_relationships.values():
                    if rel.type == RelationType.CAUSES.value and rel.start_node == current:
                        next_node = rel.end_node
                        break
                current = next_node
            
            return chain
        
        result = await self.execute_cypher(
            f"""
            MATCH path = (start {{id: $id}})-[:CAUSES*..{max_depth}]->(effect)
            RETURN nodes(path) as chain
            ORDER BY length(path) ASC
            LIMIT 1
            """,
            {"id": start_concept}
        )
        
        if result.success and result.data:
            return [
                Node(id=n["id"], labels=list(n.labels), properties=dict(n))
                for n in result.data[0]["chain"]
            ]
        return []
