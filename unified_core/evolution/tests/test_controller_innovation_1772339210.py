import pytest
from typing import Dict, Any

class MockController:
    def __init__(self):
        self.proposals_processed = 100
        self.proposals_approved = 50
        self.proposals_rejected = 30
        self.proposals_executed = 40
        self.proposals_generated = 60
        self._triggers_handled = 20
        self._dreams_realized = 15
        self.auto_execute_config = True
        self.auto_execute_policy = "default"
        self.auto_execute_code = """
def example():
    pass
"""
        self._consequence_engine = None
        self._scar_tissue = "Some tissue"
        self._world_model = {"key": "value"}
        self._journal = ["log1", "log2"]
        self.memory = MockMemory()
        self.dreamer = MockDreamer()
        self.ledger = MockLedger()

class MockMemory:
    def get_stats(self) -> Dict[str, Any]:
        return {
            "memory_size": 1024,
            "memory_usage": 512
        }

class MockDreamer:
    def get_stats(self) -> Dict[str, Any]:
        return {
            "dream_count": 3
        }

class MockLedger:
    def get_stats(self) -> Dict[str, Any]:
        return {
            "transaction_count": 10
        }

def test_get_stats_happy_path():
    controller = MockController()
    result = controller.get_stats()
    expected_keys = [
        "version", "proposals_processed", "proposals_approved",
        "proposals_rejected", "proposals_executed", "proposals_generated",
        "triggers_handled", "dreams_realized", "auto_execute_config",
        "auto_execute_policy", "auto_execute_code", "cognitive_connected",
        "memory_stats", "dreamer_stats", "ledger_stats"
    ]
    assert all(key in result for key in expected_keys)
    assert result["version"] == "3.0.0"
    assert result["proposals_processed"] == 100
    assert result["cognitive_connected"]["consequence_engine"] is False

def test_get_stats_empty_values():
    controller = MockController()
    controller.proposals_processed = None
    controller._triggers_handled = None
    controller.auto_execute_code = ""
    result = controller.get_stats()
    assert result["proposals_processed"] is None
    assert result["triggers_handled"] is None
    assert result["auto_execute_code"] == ""

def test_get_stats_boundary_cases():
    controller = MockController()
    controller.proposals_processed = 0
    controller._triggers_handled = 0
    controller.auto_execute_code = "\n"
    result = controller.get_stats()
    assert result["proposals_processed"] == 0
    assert result["triggers_handled"] == 0
    assert result["auto_execute_code"] == ""

def test_get_stats_memory_none():
    controller = MockController()
    controller.memory = None
    result = controller.get_stats()
    assert "memory_stats" in result
    assert result["memory_stats"] is None

def test_get_stats_dreamer_none():
    controller = MockController()
    controller.dreamer = None
    result = controller.get_stats()
    assert "dreamer_stats" in result
    assert result["dreamer_stats"] is None

def test_get_stats_ledger_none():
    controller = MockController()
    controller.ledger = None
    result = controller.get_stats()
    assert "ledger_stats" in result
    assert result["ledger_stats"] is None