import pytest
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

class DataTransformer:
    def __init__(self, numerical_features, categorical_features):
        self.numerical_features = numerical_features
        self.categorical_features = categorical_features
    
    def create_pipeline(self):
        """Creates a preprocessing pipeline for numerical and categorical data."""
        # Numerical preprocessing: standard scaling
        num_pipeline = Pipeline([
            ('scaler', StandardScaler())
        ])

        # Categorical preprocessing: one-hot encoding
        cat_pipeline = Pipeline([
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', num_pipeline, self.numerical_features),
                ('cat', cat_pipeline, self.categorical_features)
            ]
        )
        
        return preprocessor

# Test cases
def test_create_pipeline_happy_path():
    transformer = DataTransformer(numerical_features=['age'], categorical_features=['gender'])
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)

def test_create_pipeline_empty_numerical_features():
    transformer = DataTransformer(numerical_features=[], categorical_features=['gender'])
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)
    
def test_create_pipeline_empty_categorical_features():
    transformer = DataTransformer(numerical_features=['age'], categorical_features=[])
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)

def test_create_pipeline_none_numerical_features():
    transformer = DataTransformer(numerical_features=None, categorical_features=['gender'])
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)

def test_create_pipeline_none_categorical_features():
    transformer = DataTransformer(numerical_features=['age'], categorical_features=None)
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)

def test_create_pipeline_empty_tuple_numerical_features():
    transformer = DataTransformer(numerical_features=(), categorical_features=['gender'])
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)

def test_create_pipeline_empty_tuple_categorical_features():
    transformer = DataTransformer(numerical_features=['age'], categorical_features=())
    pipeline = transformer.create_pipeline()
    assert isinstance(pipeline, ColumnTransformer)