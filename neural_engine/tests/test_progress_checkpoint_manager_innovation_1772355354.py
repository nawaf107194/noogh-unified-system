import pytest

from neural_engine.progress_checkpoint_manager import ProgressCheckpointManager

def test_get_overall_stats_happy_path():
    checkpoints = [
        {"actions_count": 10, "actions": [{"success": True}, {"success": False}]},
        {"actions_count": 5, "actions": [{"success": True}]}
    ]
    actions = [{"success": True}, {"success": True}]
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 2,
        "total_actions": 18,
        "successful_actions": 7,
        "success_rate": 38.89,
        "pending_actions": 0
    }

def test_get_overall_stats_empty_checkpoints():
    checkpoints = []
    actions = [{"success": True}, {"success": True}]
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 0,
        "total_actions": 2,
        "successful_actions": 2,
        "success_rate": 100.0,
        "pending_actions": 0
    }

def test_get_overall_stats_empty_actions():
    checkpoints = [{"actions_count": 10, "actions": [{"success": True}, {"success": False}]}]
    actions = []
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 1,
        "total_actions": 10,
        "successful_actions": 2,
        "success_rate": 20.0,
        "pending_actions": 0
    }

def test_get_overall_stats_empty_both():
    checkpoints = []
    actions = []
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 0,
        "total_actions": 0,
        "successful_actions": 0,
        "success_rate": 0.0,
        "pending_actions": 0
    }

def test_get_overall_stats_all_successful():
    checkpoints = [
        {"actions_count": 10, "actions": [{"success": True}] * 10},
        {"actions_count": 5, "actions": [{"success": True}] * 5}
    ]
    actions = [{"success": True}] * 2
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 2,
        "total_actions": 17,
        "successful_actions": 17,
        "success_rate": 100.0,
        "pending_actions": 0
    }

def test_get_overall_stats_all_failed():
    checkpoints = [
        {"actions_count": 10, "actions": [{"success": False}] * 10},
        {"actions_count": 5, "actions": [{"success": False}] * 5}
    ]
    actions = [{"success": False}] * 2
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 2,
        "total_actions": 17,
        "successful_actions": 0,
        "success_rate": 0.0,
        "pending_actions": 0
    }

def test_get_overall_stats_mixed_success():
    checkpoints = [
        {"actions_count": 10, "actions": [{"success": True}] * 5 + [{"success": False}] * 5},
        {"actions_count": 5, "actions": [{"success": True}, {"success": False}]}
    ]
    actions = [{"success": True}, {"success": False}]
    
    manager = ProgressCheckpointManager(checkpoints, actions)
    result = manager.get_overall_stats()
    
    assert result == {
        "total_checkpoints": 2,
        "total_actions": 18,
        "successful_actions": 7,
        "success_rate": 38.89,
        "pending_actions": 0
    }