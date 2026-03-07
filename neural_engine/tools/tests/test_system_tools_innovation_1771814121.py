import pytest
from unittest.mock import patch, MagicMock
from neural_engine.tools.system_tools import get_docker_status

def test_get_docker_status_happy_path():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='container1|Up 2 days|image1\ncontainer2|Up a minute|image2'
        )
        
        result = get_docker_status()
        
        assert result == {
            "status": "available",
            "containers": [
                {"name": "container1", "status": "Up 2 days", "image": "image1"},
                {"name": "container2", "status": "Up a minute", "image": "image2"}
            ],
            "running": 2,
            "total": 2,
            "summary_ar": "Docker يعمل: 2 حاوية نشطة من 2"
        }

def test_get_docker_status_empty_output():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=''
        )
        
        result = get_docker_status()
        
        assert result == {
            "status": "available",
            "containers": [],
            "running": 0,
            "total": 0,
            "summary_ar": "Docker يعمل: 0 حاوية نشطة من 0"
        }

def test_get_docker_status_error_output():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='Error message'
        )
        
        result = get_docker_status()
        
        assert result == {
            "status": "error",
            "error": 'Error message',
            "summary_ar": "لا يمكن قراءة حالة Docker"
        }

def test_get_docker_status_not_installed():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        
        result = get_docker_status()
        
        assert result == {
            "status": "not_installed",
            "error": "docker not found",
            "summary_ar": "Docker غير مثبت"
        }

def test_get_docker_status_exception():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Some error")
        
        result = get_docker_status()
        
        assert result == {
            "status": "error",
            "error": "Some error",
            "summary_ar": "خطأ: Some error"
        }