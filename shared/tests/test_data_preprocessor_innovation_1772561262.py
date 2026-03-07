import pytest
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from src.shared.data_preprocessor import DataPreprocessor

def test_data_preprocessor_init_happy_path():
    # Test that scalers and encoders are initialized correctly
    data_preprocessor = DataPreprocessor()
    
    # Check scalers
    assert isinstance(data_preprocessor.scalers, dict)
    assert len(data_preprocessor.scalers) == 2
    assert 'standard' in data_preprocessor.scalers
    assert isinstance(data_preprocessor.scalers['standard'], StandardScaler)
    assert 'minmax' in data_preprocessor.scalers
    assert isinstance(data_preprocessor.scalers['minmax'], MinMaxScaler)
    
    # Check encoders
    assert isinstance(data_preprocessor.encoders, dict)
    assert len(data_preprocessor.encoders) == 1
    assert 'onehot' in data_preprocessor.encoders
    assert isinstance(data_preprocessor.encoders['onehot'], OneHotEncoder)

def test_data_preprocessor_init_edge_cases():
    # Test initialization with no arguments
    data_preprocessor = DataPreprocessor()
    assert data_preprocessor.scalers is not None
    assert data_preprocessor.encoders is not None