import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

class MockDataTransformer:
    def __init__(self, numerical_features=None, categorical_features=None):
        self.numerical_features = numerical_features if numerical_features is not None else []
        self.categorical_features = categorical_features if categorical_features is not None else []

def test_happy_path():
    transformer = MockDataTransformer(numerical_features=['age', 'income'], categorical_features=['gender'])
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 2
    assert result.transformers[0][0] == 'num'
    assert isinstance(result.transformers[0][1], Pipeline)
    assert result.transformers[0][1].steps[0][0] == 'scaler'
    assert isinstance(result.transformers[0][1].steps[0][1], StandardScaler)
    assert result.transformers[0][2] == ['age', 'income']
    
    assert result.transformers[1][0] == 'cat'
    assert isinstance(result.transformers[1][1], Pipeline)
    assert result.transformers[1][1].steps[0][0] == 'onehot'
    assert isinstance(result.transformers[1][1].steps[0][1], OneHotEncoder)
    assert result.transformers[1][2] == ['gender']

def test_empty_features():
    transformer = MockDataTransformer(numerical_features=[], categorical_features=[])
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 0

def test_none_features():
    transformer = MockDataTransformer(numerical_features=None, categorical_features=None)
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 0

def test_single_numerical_feature():
    transformer = MockDataTransformer(numerical_features=['age'], categorical_features=[])
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 1
    assert result.transformers[0][0] == 'num'
    assert isinstance(result.transformers[0][1], Pipeline)
    assert result.transformers[0][1].steps[0][0] == 'scaler'
    assert isinstance(result.transformers[0][1].steps[0][1], StandardScaler)
    assert result.transformers[0][2] == ['age']

def test_single_categorical_feature():
    transformer = MockDataTransformer(numerical_features=[], categorical_features=['gender'])
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 1
    assert result.transformers[0][0] == 'cat'
    assert isinstance(result.transformers[0][1], Pipeline)
    assert result.transformers[0][1].steps[0][0] == 'onehot'
    assert isinstance(result.transformers[0][1].steps[0][1], OneHotEncoder)
    assert result.transformers[0][2] == ['gender']

def test_mixed_features():
    transformer = MockDataTransformer(numerical_features=['age', 'income'], categorical_features=['gender', 'occupation'])
    
    result = transformer.create_pipeline()
    
    assert isinstance(result, ColumnTransformer)
    assert len(result.transformers) == 3
    assert result.transformers[0][0] == 'num'
    assert isinstance(result.transformers[0][1], Pipeline)
    assert result.transformers[0][1].steps[0][0] == 'scaler'
    assert isinstance(result.transformers[0][1].steps[0][1], StandardScaler)
    assert result.transformers[0][2] == ['age', 'income']
    
    assert result.transformers[1][0] == 'cat'
    assert isinstance(result.transformers[1][1], Pipeline)
    assert result.transformers[1][1].steps[0][0] == 'onehot'
    assert isinstance(result.transformers[1][1].steps[0][1], OneHotEncoder)
    assert result.transformers[1][2] == ['gender']
    
    assert result.transformers[2][0] == 'cat'
    assert isinstance(result.transformers[2][1], Pipeline)
    assert result.transformers[2][1].steps[0][0] == 'onehot'
    assert isinstance(result.transformers[2][1].steps[0][1], OneHotEncoder)
    assert result.transformers[2][2] == ['occupation']