import os
from unittest.mock import patch, mock_open

def write_env_file(pod_id: str):
    """Write the environment config with the correct pod ID."""
    env_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "runpod_brain.env"
    )
    env_path = os.path.abspath(env_path)
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        content = content.replace("REPLACE_WITH_YOUR_POD_ID", pod_id)
        content = content.replace(
            f"RUNPOD_POD_ID={pod_id}\nNEURAL_ENGINE_URL=https://${{{pod_id}}}-8000.proxy.runpod.net",
            f"RUNPOD_POD_ID={pod_id}\nNEURAL_ENGINE_URL=https://{pod_id}-8000.proxy.runpod.net"
        )
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"   ✅ Updated {env_path}")

# Test code
import pytest

def test_write_env_file_happy_path():
    pod_id = "test-pod-id"
    env_content = """REPLACE_WITH_YOUR_POD_ID=old-pod-id
RUNPOD_POD_ID=old-pod-id
NEURAL_ENGINE_URL=https://old-pod-id-8000.proxy.runpod.net"""
    
    with patch('builtins.open', mock_open(read_data=env_content)) as mock_file:
        write_env_file(pod_id)
        
        mock_file().write.assert_called_once_with(env_content.replace("REPLACE_WITH_YOUR_POD_ID", pod_id).replace(
            "RUNPOD_POD_ID=old-pod-id\nNEURAL_ENGINE_URL=https://old-pod-id-8000.proxy.runpod.net",
            f"RUNPOD_POD_ID={pod_id}\nNEURAL_ENGINE_URL=https://{pod_id}-8000.proxy.runpod.net"
        ))

def test_write_env_file_empty_pod_id():
    pod_id = ""
    env_content = """REPLACE_WITH_YOUR_POD_ID=old-pod-id
RUNPOD_POD_ID=old-pod-id
NEURAL_ENGINE_URL=https://old-pod-id-8000.proxy.runpod.net"""
    
    with patch('builtins.open', mock_open(read_data=env_content)) as mock_file:
        write_env_file(pod_id)
        
        mock_file().write.assert_not_called()

def test_write_env_file_none_pod_id():
    pod_id = None
    env_content = """REPLACE_WITH_YOUR_POD_ID=old-pod-id
RUNPOD_POD_ID=old-pod-id
NEURAL_ENGINE_URL=https://old-pod-id-8000.proxy.runpod.net"""
    
    with patch('builtins.open', mock_open(read_data=env_content)) as mock_file:
        write_env_file(pod_id)
        
        mock_file().write.assert_not_called()

def test_write_env_file_nonexistent_file():
    pod_id = "test-pod-id"
    env_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "runpod_brain.env"
    )
    
    with patch('os.path.exists', return_value=False):
        write_env_file(pod_id)
        
        assert not os.path.exists(env_path)

def test_write_env_file_with_error():
    pod_id = "test-pod-id"
    env_content = """REPLACE_WITH_YOUR_POD_ID=old-pod-id
RUNPOD_POD_ID=old-pod-id
NEURAL_ENGINE_URL=https://old-pod-id-8000.proxy.runpod.net"""
    
    with patch('builtins.open', mock_open(read_data=env_content)) as mock_file:
        mock_file.side_effect = Exception("Mocked error")
        
        write_env_file(pod_id)
        
        mock_file().write.assert_not_called()