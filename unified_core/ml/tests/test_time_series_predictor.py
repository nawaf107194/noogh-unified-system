import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import torch

class MockTimeSeriesPredictor:
    def __init__(self):
        self.model = None
        self.optimizer = None
        self.scaler_mean = None
        self.scaler_std = None
        self.train_losses = []
        self.val_losses = []

    def build_model(self):
        self.model = MagicMock()
        self.optimizer = MagicMock()

@patch('torch.load', return_value={'model_state_dict': {}, 'optimizer_state_dict': {}, 'scaler_mean': 0.5, 'scaler_std': 1.0})
def test_load_model_happy_path(mock_torch_load):
    predictor = MockTimeSeriesPredictor()
    predictor.config = MagicMock()
    predictor.config.model_dir = Path('test_models')
    
    predictor.load_model('model.pth')
    
    assert predictor.model is not None
    assert predictor.optimizer is not None
    assert predictor.scaler_mean == 0.5
    assert predictor.scaler_std == 1.0

def test_load_model_file_not_found():
    predictor = MockTimeSeriesPredictor()
    predictor.config = MagicMock()
    predictor.config.model_dir = Path('nonexistent_models')
    
    with pytest.raises(FileNotFoundError):
        predictor.load_model('model.pth')

@patch('torch.cuda.is_available', return_value=False)
@patch('torch.load', side_effect=RuntimeError("CUDA error"))
def test_load_model_cuda_error(mock_torch_load, mock_cuda_is_available):
    predictor = MockTimeSeriesPredictor()
    predictor.config = MagicMock()
    predictor.config.model_dir = Path('test_models')
    
    with pytest.raises(RuntimeError) as e:
        predictor.load_model('model.pth')
    
    assert str(e.value) == "PyTorch not available"

@patch('torch.cuda.is_available', return_value=True)
@patch('torch.load', side_effect=RuntimeError("CUDA error"))
def test_load_model_fallback_to_cpu(mock_torch_load, mock_cuda_is_available):
    predictor = MockTimeSeriesPredictor()
    predictor.config = MagicMock()
    predictor.config.model_dir = Path('test_models')
    
    with pytest.raises(RuntimeError) as e:
        predictor.load_model('model.pth')
    
    assert str(e.value) == "CUDA error during load, falling back to CPU"

@patch('torch.cuda.is_available', return_value=False)
def test_load_model_no_cuda_available(mock_cuda_is_available):
    predictor = MockTimeSeriesPredictor()
    predictor.config = MagicMock()
    predictor.config.model_dir = Path('test_models')
    
    with pytest.raises(RuntimeError) as e:
        predictor.load_model('model.pth')
    
    assert str(e.value) == "PyTorch not available"