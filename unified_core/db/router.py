"""
DataRouter - Intelligent Query Routing
Automatically determines which database to query based on input type
"""
import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib

from .postgres import PostgresManager, QueryResult
from .vector_db import VectorDBManager, VectorQueryResult
from .graph_db import GraphDBManager, GraphQueryResult, Node

logger = logging.getLogger("unified_core.db.router")


class DataType(Enum):
    """Classification of input data types for routing."""
    EQUATION = auto()        # Mathematical expressions
    LOGICAL = auto()         # Logic rules, conditions
    SEMANTIC = auto()        # Natural language, embeddings
    RELATIONAL = auto()      # Entity relationships
    TEMPORAL = auto()        # Time-series, sequences
    HYBRID = auto()          # Requires multiple DBs
    UNKNOWN = auto()


class RoutingStrategy(Enum):
    """Query routing strategies."""
    SINGLE = "single"        # Route to one DB
    PARALLEL = "parallel"    # Query multiple DBs simultaneously
    SEQUENTIAL = "sequential"  # Query DBs in order, stop on match
    AGGREGATE = "aggregate"  # Combine results from all DBs


@dataclass
class RoutingDecision:
    """Routing decision with explanation."""
    data_type: DataType
    primary_target: str  # "postgres", "vector", "graph"
    secondary_targets: List[str] = field(default_factory=list)
    strategy: RoutingStrategy = RoutingStrategy.SINGLE
    confidence: float = 1.0
    reasoning: str = ""


@dataclass
class UnifiedQueryResult:
    """Unified result from potentially multiple databases."""
    success: bool
    data_type: DataType
    sources: List[str]
    
    # Type-specific results
    sql_result: Optional[QueryResult] = None
    vector_result: Optional[VectorQueryResult] = None
    graph_result: Optional[GraphQueryResult] = None
    
    # Aggregated data
    combined_data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class DataRouter:
    """
    Intelligent router that classifies input and routes to appropriate database.
    Uses pattern matching, NLP features, and configurable rules.
    """
    
    # Pattern definitions for classification
    EQUATION_PATTERNS = [
        r'^\s*[\d\+\-\*\/\^\(\)\s\.]+\s*$',  # Pure math: 2 + 3 * 4
        r'[a-z]\s*=\s*[\d\+\-\*\/\(\)\s\.]+',  # Assignment: x = 5 + 3
        r'(sin|cos|tan|log|exp|sqrt)\s*\(',   # Functions
        r'∫|∑|∏|∂|∇',                          # Math symbols
        r'\d+\s*(mod|div)\s*\d+',              # Modular arithmetic
    ]
    
    LOGICAL_PATTERNS = [
        r'\b(if|then|else|and|or|not|implies|iff)\b',
        r'\b(forall|exists|∀|∃)\b',
        r'→|←|↔|¬|∧|∨',                        # Logic symbols
        r'true|false|null',
        r'\b(rule|condition|predicate)\b',
    ]
    
    RELATIONSHIP_PATTERNS = [
        r'\b(is\s+a|has\s+a|belongs\s+to|related\s+to)\b',
        r'\b(parent|child|sibling|ancestor)\b',
        r'\b(causes|enables|prevents|requires)\b',
        r'\b(before|after|during)\b',
        r'\b(connect|link|path|traverse)\b',
    ]
    
    def __init__(
        self,
        postgres: Optional[PostgresManager] = None,
        vector_db: Optional[VectorDBManager] = None,
        graph_db: Optional[GraphDBManager] = None
    ):
        self.postgres = postgres
        self.vector_db = vector_db
        self.graph_db = graph_db
        
        self._custom_rules: List[Callable[[str], Optional[RoutingDecision]]] = []
        self._cache: Dict[str, RoutingDecision] = {}
        self._cache_size = 1000
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all database connections."""
        results = {}
        
        if self.postgres:
            results["postgres"] = await self.postgres.initialize()
        if self.vector_db:
            results["vector"] = await self.vector_db.initialize()
        if self.graph_db:
            results["graph"] = await self.graph_db.initialize()
        
        return results
    
    def add_custom_rule(self, rule: Callable[[str], Optional[RoutingDecision]]):
        """Add custom routing rule (checked first)."""
        self._custom_rules.append(rule)
    
    def classify(self, input_data: Union[str, Dict, List]) -> RoutingDecision:
        """
        Classify input data type and determine routing.
        Returns RoutingDecision with target DB and strategy.
        """
        # Handle different input types
        if isinstance(input_data, dict):
            return self._classify_dict(input_data)
        elif isinstance(input_data, list):
            # If list of floats, likely embedding
            if input_data and isinstance(input_data[0], (int, float)):
                return RoutingDecision(
                    data_type=DataType.SEMANTIC,
                    primary_target="vector",
                    confidence=0.95,
                    reasoning="Numeric list detected as embedding vector"
                )
            return self._classify_text(str(input_data))
        else:
            text = str(input_data)
        
        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()[:16]
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Apply custom rules first
        for rule in self._custom_rules:
            decision = rule(text)
            if decision:
                self._cache[cache_key] = decision
                return decision
        
        # Pattern-based classification
        decision = self._classify_text(text)
        
        # Cache result
        if len(self._cache) < self._cache_size:
            self._cache[cache_key] = decision
        
        return decision
    
    def _classify_text(self, text: str) -> RoutingDecision:
        """Classify text input using pattern matching."""
        text_lower = text.lower()
        scores = {
            DataType.EQUATION: 0.0,
            DataType.LOGICAL: 0.0,
            DataType.RELATIONAL: 0.0,
            DataType.SEMANTIC: 0.0,
        }
        
        # Check equation patterns
        for pattern in self.EQUATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[DataType.EQUATION] += 0.3
        
        # Check logical patterns
        for pattern in self.LOGICAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[DataType.LOGICAL] += 0.25
        
        # Check relationship patterns
        for pattern in self.RELATIONSHIP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[DataType.RELATIONAL] += 0.25
        
        # Semantic indicators (natural language characteristics)
        word_count = len(text.split())
        if word_count > 10:
            scores[DataType.SEMANTIC] += 0.2
        if re.search(r'[?.!]$', text):  # Ends with punctuation
            scores[DataType.SEMANTIC] += 0.15
        
        # Find highest score
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # Default to semantic if no strong match
        if max_score < 0.2:
            max_type = DataType.SEMANTIC
            max_score = 0.5
        
        # Determine target and strategy
        target_map = {
            DataType.EQUATION: "postgres",
            DataType.LOGICAL: "postgres",
            DataType.RELATIONAL: "graph",
            DataType.SEMANTIC: "vector",
        }
        
        primary_target = target_map.get(max_type, "vector")
        
        # Check for hybrid (multiple high scores)
        high_scores = [t for t, s in scores.items() if s > 0.2 and t != max_type]
        secondary_targets = [target_map[t] for t in high_scores]
        
        strategy = RoutingStrategy.SINGLE
        if secondary_targets:
            strategy = RoutingStrategy.PARALLEL
        
        return RoutingDecision(
            data_type=max_type,
            primary_target=primary_target,
            secondary_targets=secondary_targets,
            strategy=strategy,
            confidence=min(max_score + 0.5, 1.0),
            reasoning=f"Pattern match scores: {scores}"
        )
    
    def _classify_dict(self, data: Dict) -> RoutingDecision:
        """Classify dictionary input based on keys and values."""
        keys = set(data.keys())
        
        # Check for vector/embedding
        if "embedding" in keys or "vector" in keys:
            return RoutingDecision(
                data_type=DataType.SEMANTIC,
                primary_target="vector",
                confidence=0.95,
                reasoning="Dictionary contains embedding/vector key"
            )
        
        # Check for relationship structure
        if {"from", "to", "relationship"}.issubset(keys) or {"source", "target"}.issubset(keys):
            return RoutingDecision(
                data_type=DataType.RELATIONAL,
                primary_target="graph",
                confidence=0.9,
                reasoning="Dictionary has relationship structure"
            )
        
        # Check for equation/expression
        if "expression" in keys or "equation" in keys:
            return RoutingDecision(
                data_type=DataType.EQUATION,
                primary_target="postgres",
                confidence=0.9,
                reasoning="Dictionary contains expression/equation"
            )
        
        # Default to semantic (store as JSON in vector with metadata)
        return RoutingDecision(
            data_type=DataType.SEMANTIC,
            primary_target="vector",
            secondary_targets=["postgres"],
            strategy=RoutingStrategy.PARALLEL,
            confidence=0.6,
            reasoning="Generic dictionary, defaulting to vector with SQL backup"
        )
    
    async def route_and_execute(
        self,
        input_data: Union[str, Dict, List],
        operation: str = "query",  # "query", "insert", "delete"
        params: Optional[Dict] = None
    ) -> UnifiedQueryResult:
        """
        Classify input, route to appropriate DB(s), and execute.
        """
        import time
        import asyncio
        start = time.perf_counter()
        
        decision = self.classify(input_data)
        params = params or {}
        
        logger.info(f"Routing decision: {decision.data_type.name} -> {decision.primary_target}")
        
        sources = []
        sql_result = None
        vector_result = None
        graph_result = None
        
        try:
            if decision.strategy == RoutingStrategy.SINGLE:
                # Single target execution
                if decision.primary_target == "postgres" and self.postgres:
                    sql_result = await self._execute_postgres(input_data, operation, params)
                    sources.append("postgres")
                elif decision.primary_target == "vector" and self.vector_db:
                    vector_result = await self._execute_vector(input_data, operation, params)
                    sources.append("vector")
                elif decision.primary_target == "graph" and self.graph_db:
                    graph_result = await self._execute_graph(input_data, operation, params)
                    sources.append("graph")
            
            elif decision.strategy == RoutingStrategy.PARALLEL:
                # Parallel execution
                tasks = []
                target_order = []
                
                if decision.primary_target == "postgres" or "postgres" in decision.secondary_targets:
                    if self.postgres:
                        tasks.append(self._execute_postgres(input_data, operation, params))
                        target_order.append("postgres")
                
                if decision.primary_target == "vector" or "vector" in decision.secondary_targets:
                    if self.vector_db:
                        tasks.append(self._execute_vector(input_data, operation, params))
                        target_order.append("vector")
                
                if decision.primary_target == "graph" or "graph" in decision.secondary_targets:
                    if self.graph_db:
                        tasks.append(self._execute_graph(input_data, operation, params))
                        target_order.append("graph")
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Parallel query failed for {target_order[i]}: {result}")
                            continue
                        sources.append(target_order[i])
                        if target_order[i] == "postgres":
                            sql_result = result
                        elif target_order[i] == "vector":
                            vector_result = result
                        elif target_order[i] == "graph":
                            graph_result = result
            
            return UnifiedQueryResult(
                success=bool(sources),
                data_type=decision.data_type,
                sources=sources,
                sql_result=sql_result,
                vector_result=vector_result,
                graph_result=graph_result,
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
            
        except Exception as e:
            logger.error(f"Routing execution failed: {e}")
            return UnifiedQueryResult(
                success=False,
                data_type=decision.data_type,
                sources=[],
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
    
    async def _execute_postgres(
        self,
        input_data: Union[str, Dict],
        operation: str,
        params: Dict
    ) -> QueryResult:
        """Execute PostgreSQL operation."""
        if operation == "query":
            if isinstance(input_data, str):
                # Direct SQL or expression query
                if input_data.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
                    return await self.postgres.execute(input_data)
                else:
                    # Search equations
                    return await self.postgres.query_equations(pattern=input_data)
            else:
                # Dict-based query
                return await self.postgres.query_equations(**input_data)
        
        elif operation == "insert":
            if isinstance(input_data, dict):
                if "expression" in input_data:
                    return await self.postgres.store_equation(**input_data)
                elif "rule_name" in input_data:
                    return await self.postgres.store_logical_rule(**input_data)
        
        return QueryResult(success=False, error="Unsupported postgres operation")
    
    async def _execute_vector(
        self,
        input_data: Union[str, Dict, List],
        operation: str,
        params: Dict
    ) -> VectorQueryResult:
        """Execute Vector DB operation."""
        if operation == "query":
            if isinstance(input_data, list):
                # Direct vector query
                return await self.vector_db.search(
                    query_vector=input_data,
                    top_k=params.get("top_k", 10),
                    category=params.get("category"),
                    min_score=params.get("min_score", 0.0)
                )
            elif isinstance(input_data, dict) and "query_vector" in input_data:
                return await self.vector_db.search(**input_data)
        
        elif operation == "insert":
            if isinstance(input_data, dict):
                success = await self.vector_db.insert(**input_data)
                return VectorQueryResult(success=success)
        
        return VectorQueryResult(success=False, error="Unsupported vector operation")
    
    async def _execute_graph(
        self,
        input_data: Union[str, Dict],
        operation: str,
        params: Dict
    ) -> GraphQueryResult:
        """Execute Graph DB operation."""
        if operation == "query":
            if isinstance(input_data, str):
                # Cypher query or node ID
                if input_data.upper().startswith(("MATCH", "CREATE", "MERGE")):
                    return await self.graph_db.execute_cypher(input_data, params)
                else:
                    # Get node and neighbors
                    node = await self.graph_db.get_node(input_data)
                    return GraphQueryResult(
                        success=node is not None,
                        nodes=[node] if node else []
                    )
            elif isinstance(input_data, dict):
                if "from_id" in input_data and "to_id" in input_data:
                    path = await self.graph_db.find_path(
                        input_data["from_id"],
                        input_data["to_id"],
                        input_data.get("max_depth", 5)
                    )
                    return GraphQueryResult(
                        success=path is not None,
                        paths=[path] if path else []
                    )
        
        elif operation == "insert":
            if isinstance(input_data, dict):
                if "node_id" in input_data:
                    success = await self.graph_db.create_node(
                        input_data["node_id"],
                        input_data.get("labels", []),
                        input_data.get("properties", {})
                    )
                    return GraphQueryResult(success=success)
                elif "from_id" in input_data and "to_id" in input_data:
                    success = await self.graph_db.create_relationship(
                        input_data["from_id"],
                        input_data["to_id"],
                        input_data.get("rel_type", "RELATED_TO"),
                        input_data.get("properties")
                    )
                    return GraphQueryResult(success=success)
        
        return GraphQueryResult(success=False, error="Unsupported graph operation")
    
    # Convenience methods
    async def store(self, input_data: Union[str, Dict, List], **kwargs) -> UnifiedQueryResult:
        """Auto-route and store data."""
        return await self.route_and_execute(input_data, operation="insert", params=kwargs)
    
    async def query(self, input_data: Union[str, Dict, List], **kwargs) -> UnifiedQueryResult:
        """Auto-route and query data."""
        return await self.route_and_execute(input_data, operation="query", params=kwargs)
    
    async def close_all(self):
        """Close all database connections."""
        if self.postgres:
            await self.postgres.close()
        if self.graph_db:
            await self.graph_db.close()
        # Vector DB doesn't need explicit close for Milvus
