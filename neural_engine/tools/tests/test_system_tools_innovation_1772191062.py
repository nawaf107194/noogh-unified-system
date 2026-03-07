import pytest
from system_tools import get_gpu_status

def test_get_gpu_status_happy_path(mocker):
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(
        args=['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'],
        stdout="GPU0,16189,4235,11954,[N/A],75\n"
               "GPU1,16189,2345,13844,32,80",
        stderr='',
        returncode=0
    ))
    
    result = get_gpu_status()
    
    assert result == {
        "status": "available",
        "gpus": [
            {"id": 0, "name": "GPU0", "memory_total_mb": 16189, "memory_used_mb": 4235, "memory_free_mb": 11954, "temperature_c": None, "utilization_percent": 75},
            {"id": 1, "name": "GPU1", "memory_total_mb": 16189, "memory_used_mb": 2345, "memory_free_mb": 13844, "temperature_c": 32, "utilization_percent": 80}
        ],
        "count": 2,
        "total_free_mb": 25798,
        "summary_ar": "GPU متاح: GPU0، الذاكرة المتاحة: 25798 MB"
    }

def test_get_gpu_status_empty_output(mocker):
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(
        args=['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'],
        stdout="",
        stderr='',
        returncode=0
    ))
    
    result = get_gpu_status()
    
    assert result == {
        "status": "available",
        "gpus": [],
        "count": 0,
        "total_free_mb": 0,
        "summary_ar": "GPU متاح: GPU0، الذاكرة المتاحة: 25798 MB"
    }

def test_get_gpu_status_unavailable(mocker):
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(
        args=['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'],
        stdout="",
        stderr='Failed to run nvidia-smi',
        returncode=1
    ))
    
    result = get_gpu_status()
    
    assert result == {
        "status": "unavailable",
        "error": "nvidia-smi failed",
        "summary_ar": "GPU غير متاح أو لا يمكن قراءته"
    }

def test_get_gpu_status_no_nvidia(mocker):
    mocker.patch('subprocess.run', side_effect=FileNotFoundError)
    
    result = get_gpu_status()
    
    assert result == {
        "status": "no_nvidia",
        "error": "nvidia-smi not found",
        "summary_ar": "لا يوجد GPU من NVIDIA"
    }

def test_get_gpu_status_exception(mocker):
    mocker.patch('subprocess.run', side_effect=Exception("Unexpected error"))
    
    result = get_gpu_status()
    
    assert result == {
        "status": "error",
        "error": "Unexpected error",
        "summary_ar": "خطأ في قراءة GPU: Unexpected error"
    }