"""Console configuration stub."""
import os
from dataclasses import dataclass

@dataclass
class ConsoleSettings:
    GATEWAY_LOG: str = "/tmp/gateway.log"
    NEURAL_LOG: str = "/tmp/neural_engine.log"
    NEURAL_ENGINE_URL: str = os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
    DATA_DIR: str = os.getenv("NOOGH_DATA_DIR", ".")

settings = ConsoleSettings()
