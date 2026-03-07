"""
NOOGH Port Configuration - Single Source of Truth

ALL port definitions MUST reference this file.
Do not hardcode ports elsewhere in the codebase.

Usage:
    from config.ports import PORTS
    
    neural_url = f"http://localhost:{PORTS.NEURAL_ENGINE}"
    gateway_url = f"http://localhost:{PORTS.GATEWAY}"
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PortConfig:
    """
    Immutable port configuration.
    All ports are centralized here to prevent conflicts.
    """
    
    # ==========================================
    # CORE SERVICES (Required)
    # ==========================================
    
    NEURAL_ENGINE: int = int(os.getenv("NOOGH_NEURAL_PORT", "8000"))
    """Neural Engine API - LLM inference"""
    
    GATEWAY: int = int(os.getenv("NOOGH_GATEWAY_PORT", "8001"))
    """Gateway API + Dashboard"""
    
    REDIS: int = int(os.getenv("NOOGH_REDIS_PORT", "6379"))
    """Redis Cache"""
    
    MCP_EXECUTION: int = int(os.getenv("NOOGH_MCP_PORT", "8766"))
    """MCP Execution Server (Tunnel: exec.nooogh.com)"""
    
    # ==========================================
    # DATABASES (Optional)
    # ==========================================
    
    POSTGRES: int = int(os.getenv("NOOGH_POSTGRES_PORT", "5432"))
    """PostgreSQL Database"""
    
    NEO4J: int = int(os.getenv("NOOGH_NEO4J_PORT", "7687"))
    """Neo4j Graph Database"""
    
    MILVUS: int = int(os.getenv("NOOGH_MILVUS_PORT", "19530"))
    """Milvus Vector Database"""
    
    # ==========================================
    # MONITORING (Optional)
    # ==========================================
    
    PROMETHEUS: int = int(os.getenv("NOOGH_PROMETHEUS_PORT", "9090"))
    """Prometheus Metrics"""
    
    GRAFANA: int = int(os.getenv("NOOGH_GRAFANA_PORT", "3000"))
    """Grafana Dashboard"""
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def get_neural_url(self, host: str = "localhost") -> str:
        """Get Neural Engine URL."""
        return f"http://{host}:{self.NEURAL_ENGINE}"
    
    def get_gateway_url(self, host: str = "localhost") -> str:
        """Get Gateway URL."""
        return f"http://{host}:{self.GATEWAY}"
    
    def get_redis_url(self, host: str = "localhost") -> str:
        """Get Redis URL."""
        return f"redis://{host}:{self.REDIS}"
    
    def to_dict(self) -> dict:
        """Export all ports as dictionary."""
        return {
            "neural_engine": self.NEURAL_ENGINE,
            "gateway": self.GATEWAY,
            "redis": self.REDIS,
            "postgres": self.POSTGRES,
            "neo4j": self.NEO4J,
            "milvus": self.MILVUS,
            "prometheus": self.PROMETHEUS,
            "grafana": self.GRAFANA,
        }


# Global singleton
PORTS = PortConfig()


# ==========================================
# VALIDATION
# ==========================================

def validate_no_conflicts():
    """Ensure no port conflicts."""
    ports = list(PORTS.to_dict().values())
    duplicates = [p for p in ports if ports.count(p) > 1]
    if duplicates:
        raise ValueError(f"Port conflict detected: {set(duplicates)}")
    return True


# Validate on import
validate_no_conflicts()


# ==========================================
# CLI
# ==========================================

if __name__ == "__main__":
    print("=== NOOGH Port Configuration ===")
    print()
    for name, port in PORTS.to_dict().items():
        print(f"  {name:15} : {port}")
    print()
    print(f"Neural Engine URL: {PORTS.get_neural_url()}")
    print(f"Gateway URL: {PORTS.get_gateway_url()}")
