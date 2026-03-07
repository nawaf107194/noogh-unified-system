"""
PostgreSQL Manager - Relational & Logical Data Store
Handles mathematical expressions, transactions, structured queries
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    import asyncpg
    from asyncpg import Pool, Connection
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None
    Pool = None
    Connection = None

logger = logging.getLogger("unified_core.db.postgres")


class QueryType(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


@dataclass
class QueryResult:
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    affected_rows: int = 0
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class PostgresManager:
    """
    Async PostgreSQL connection manager for logical/mathematical data.
    Thread-safe connection pooling with automatic reconnection.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "unified_core",
        user: str = "postgres",
        password: str = "",
        min_connections: int = 5,
        max_connections: int = 20,
        command_timeout: float = 60.0
    ):
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        self._pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize connection pool."""
        if self._initialized:
            return True
        try:
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.command_timeout,
                server_settings={
                    "application_name": "unified_core",
                    "timezone": "UTC"
                }
            )
            self._initialized = True
            logger.info("PostgreSQL pool initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            return False
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._initialized = False
            logger.info("PostgreSQL pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        if not self._initialized:
            await self.initialize()
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute(
        self,
        query: str,
        params: Optional[Tuple] = None,
        query_type: QueryType = QueryType.EXECUTE
    ) -> QueryResult:
        """Execute SQL query with automatic type detection."""
        import time
        start = time.perf_counter()
        
        try:
            async with self.acquire() as conn:
                if query_type == QueryType.SELECT or query.strip().upper().startswith("SELECT"):
                    rows = await conn.fetch(query, *(params or ()))
                    data = [dict(row) for row in rows]
                    return QueryResult(
                        success=True,
                        data=data,
                        affected_rows=len(data),
                        execution_time_ms=(time.perf_counter() - start) * 1000
                    )
                else:
                    result = await conn.execute(query, *(params or ()))
                    affected = int(result.split()[-1]) if result else 0
                    return QueryResult(
                        success=True,
                        affected_rows=affected,
                        execution_time_ms=(time.perf_counter() - start) * 1000
                    )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
    
    async def execute_transaction(
        self,
        queries: List[Tuple[str, Optional[Tuple]]]
    ) -> QueryResult:
        """Execute multiple queries in a transaction."""
        import time
        start = time.perf_counter()
        
        try:
            async with self.acquire() as conn:
                async with conn.transaction():
                    results = []
                    for query, params in queries:
                        result = await conn.execute(query, *(params or ()))
                        results.append(result)
                    return QueryResult(
                        success=True,
                        affected_rows=len(results),
                        execution_time_ms=(time.perf_counter() - start) * 1000
                    )
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
    
    # Mathematical/Logical specialized methods
    async def store_equation(
        self,
        expression: str,
        result: float,
        variables: Dict[str, float],
        context_id: Optional[str] = None
    ) -> QueryResult:
        """Store mathematical equation with result."""
        import json
        query = """
            INSERT INTO equations (expression, result, variables, context_id, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            RETURNING id
        """
        return await self.execute(
            query,
            (expression, result, json.dumps(variables), context_id),
            QueryType.INSERT
        )
    
    async def query_equations(
        self,
        pattern: Optional[str] = None,
        context_id: Optional[str] = None,
        limit: int = 100
    ) -> QueryResult:
        """Query stored equations with optional filtering."""
        conditions = []
        params = []
        idx = 1
        
        if pattern:
            conditions.append(f"expression LIKE ${idx}")
            params.append(f"%{pattern}%")
            idx += 1
        if context_id:
            conditions.append(f"context_id = ${idx}")
            params.append(context_id)
            idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # SECURITY FIX: Use parameterized query for LIMIT to prevent injection
        params.append(min(limit, 1000))  # Also enforce max limit
        limit_param = f"${idx}"
        
        query = f"""
            SELECT id, expression, result, variables, context_id, created_at
            FROM equations
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_param}
        """
        return await self.execute(query, tuple(params), QueryType.SELECT)
    
    async def store_logical_rule(
        self,
        rule_name: str,
        condition: str,
        action: str,
        priority: int = 0
    ) -> QueryResult:
        """Store logical inference rule."""
        query = """
            INSERT INTO logical_rules (name, condition, action, priority, active, created_at)
            VALUES ($1, $2, $3, $4, true, NOW())
            ON CONFLICT (name) DO UPDATE SET
                condition = EXCLUDED.condition,
                action = EXCLUDED.action,
                priority = EXCLUDED.priority
            RETURNING id
        """
        return await self.execute(
            query,
            (rule_name, condition, action, priority),
            QueryType.INSERT
        )
    
    async def get_active_rules(self, min_priority: int = 0) -> QueryResult:
        """Get active logical rules ordered by priority."""
        query = """
            SELECT id, name, condition, action, priority
            FROM logical_rules
            WHERE active = true AND priority >= $1
            ORDER BY priority DESC
        """
        return await self.execute(query, (min_priority,), QueryType.SELECT)


# Schema initialization
POSTGRES_SCHEMA = """
-- Equations table for mathematical data
CREATE TABLE IF NOT EXISTS equations (
    id SERIAL PRIMARY KEY,
    expression TEXT NOT NULL,
    result DOUBLE PRECISION,
    variables JSONB DEFAULT '{}',
    context_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_equations_context (context_id),
    INDEX idx_equations_created (created_at DESC)
);

-- Logical rules for inference engine
CREATE TABLE IF NOT EXISTS logical_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_rules_priority (priority DESC),
    INDEX idx_rules_active (active)
);

-- Transaction log for audit
CREATE TABLE IF NOT EXISTS transaction_log (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(32) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    agent_id VARCHAR(64),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent state storage
CREATE TABLE IF NOT EXISTS agent_states (
    agent_id VARCHAR(64) PRIMARY KEY,
    state JSONB NOT NULL DEFAULT '{}',
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);
"""
