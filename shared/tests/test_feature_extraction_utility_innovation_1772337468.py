import pytest
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class MockFeatureExtractionUtility:
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA()

    def fit_transform(self, data):
        scaled_data = self.scaler.fit_transform(data)
        transformed_data = self.pca.fit_transform(scaled_data)
        columns = [f"component_{i+1}" for i in range(transformed_data.shape[1])]
        return pd.DataFrame(transformed_data, columns=columns)

@pytest.fixture
def feature_extraction_utility():
    return MockFeatureExtractionUtility()

# Happy path (normal inputs)
def test_fit_transform_happy_path(feature_extraction_utility):
    data = pd.DataFrame({
        'feature1': [1.0, 2.0, 3.0],
        'feature2': [4.0, 5.0, 6.0]
    })
    result = feature_extraction_utility.fit_transform(data)
    assert isinstance(result, pd.DataFrame)
    assert all(column.startswith('component_') for column in result.columns)

# Edge cases (empty dataset)
def test_fit_transform_empty_dataset(feature_extraction_utility):
    data = pd.DataFrame()
    result = feature_extraction_utility.fit_transform(data)
    assert result is not None
    assert len(result) == 0

# Edge cases (None input)
def test_fit_transform_none_input(feature_extraction_utility):
    with pytest.raises(ValueError):
        feature_extraction_utility.fit_transform(None)

# Error cases (invalid inputs)
def test_fit_transform_invalid_input_types(feature_extraction_utility):
    with pytest.raises(TypeError):
        feature_extraction_utility.fit_transform('not a DataFrame')

# Edge cases (boundary conditions)
def test_fit_transform_boundary_conditions(feature_extraction_utility):
    data = pd.DataFrame({
        'feature1': [0.0, 0.0, 0.0],
        'feature2': [0.0, 0.0, 0.0]
    })
    result = feature_extraction_utility.fit_transform(data)
    assert isinstance(result, pd.DataFrame)
    assert all(component == 0 for component in result.iloc[:, 0])