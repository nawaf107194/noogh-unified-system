import numpy as np
from unittest.mock import patch, MagicMock
from torch.utils.data import DataLoader
from noogh_unified_system.src.unified_core.ml.time_series_predictor import TimeSeriesPredictor, MetricsData, TimeSeriesDataset

@pytest.fixture
def predictor():
    return TimeSeriesPredictor(config=MagicMock(features=['feature1', 'feature2'], sequence_length=10, prediction_horizon=5, batch_size=32))

@pytest.fixture
def metrics_history():
    return [
        MetricsData({'feature1': 1.0, 'feature2': 2.0}),
        MetricsData({'feature1': 2.0, 'feature2': 3.0}),
        MetricsData({'feature1': 3.0, 'feature2': 4.0})
    ]

def test_prepare_data_happy_path(predictor, metrics_history):
    train_loader, val_loader = predictor.prepare_data(metrics_history)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)
    assert len(train_loader) > 0
    assert len(val_loader) > 0

@patch('noogh_unified_system.src.unified_core.ml.time_series_predictor.TORCH_AVAILABLE', False)
def test_prepare_data_torch_not_available(predictor, metrics_history):
    with pytest.raises(RuntimeError) as e:
        predictor.prepare_data(metrics_history)
    
    assert "PyTorch not available" in str(e)

def test_prepare_data_empty_metrics_history(predictor, metrics_history):
    train_loader, val_loader = predictor.prepare_data([])
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)
    assert len(train_loader) == 0
    assert len(val_loader) == 0

def test_prepare_data_none_metrics_history(predictor, metrics_history):
    train_loader, val_loader = predictor.prepare_data(None)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)
    assert len(train_loader) == 0
    assert len(val_loader) == 0

@patch('noogh_unified_system.src.unified_core.ml.time_series_predictor.MetricsData.to_array', return_value=np.array([1.0, 2.0]))
def test_prepare_data_normalize(predictor, metrics_history, mock_to_array):
    predictor.config.normalize = True
    train_loader, val_loader = predictor.prepare_data(metrics_history)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)
    assert len(mock_to_array.call_args_list) == 3

def test_prepare_data_sequence_length_error(predictor, metrics_history):
    predictor.config.sequence_length = 100
    train_loader, val_loader = predictor.prepare_data(metrics_history)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)

@patch('noogh_unified_system.src.unified_core.ml.time_series_predictor.MetricsData.to_array', return_value=np.array([1.0, 2.0]))
def test_prepare_data_prediction_horizon_error(predictor, metrics_history, mock_to_array):
    predictor.config.prediction_horizon = 100
    train_loader, val_loader = predictor.prepare_data(metrics_history)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)

@patch('noogh_unified_system.src.unified_core.ml.time_series_predictor.TORCH_AVAILABLE', True)
def test_prepare_data_async_behavior(predictor, metrics_history):
    train_loader, val_loader = predictor.prepare_data(metrics_history)
    
    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)