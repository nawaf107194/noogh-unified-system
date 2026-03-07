import pytest
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from shared.feature_extraction_utility import FeatureExtractor

class TestFeatureExtractor:

    @pytest.fixture
    def feature_extractor(self):
        fe = FeatureExtractor()
        fe.scaler = StandardScaler()
        fe.pca = PCA(n_components=2)  # Assuming we want to reduce to 2 components
        return fe

    def test_fit_transform_happy_path(self, feature_extractor):
        # Happy path - normal inputs
        data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        transformed_data = feature_extractor.fit_transform(data)
        assert isinstance(transformed_data, pd.DataFrame)
        assert transformed_data.shape == (3, 2)
        assert all([col.startswith('component_') for col in transformed_data.columns])

    def test_fit_transform_empty_dataframe(self, feature_extractor):
        # Edge case - empty dataframe
        data = pd.DataFrame()
        with pytest.raises(ValueError, match="Input data is empty"):
            feature_extractor.fit_transform(data)

    def test_fit_transform_none_input(self, feature_extractor):
        # Edge case - None input
        with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
            feature_extractor.fit_transform(None)

    def test_fit_transform_invalid_input(self, feature_extractor):
        # Error case - invalid input (not a DataFrame)
        data = "This is not a DataFrame"
        with pytest.raises(AttributeError, match="'str' object has no attribute 'shape'"):
            feature_extractor.fit_transform(data)

    def test_fit_transform_non_numeric_data(self, feature_extractor):
        # Error case - non-numeric data
        data = pd.DataFrame({
            'A': ['a', 'b', 'c'],
            'B': ['d', 'e', 'f']
        })
        with pytest.raises(ValueError, match="could not convert string to float"):
            feature_extractor.fit_transform(data)

    def test_fit_transform_boundary_case_single_row(self, feature_extractor):
        # Edge case - single row
        data = pd.DataFrame({
            'A': [1],
            'B': [2]
        })
        with pytest.raises(ValueError, match="n_components.* must be between 0 and min"):
            feature_extractor.fit_transform(data)

    def test_fit_transform_boundary_case_single_column(self, feature_extractor):
        # Edge case - single column
        data = pd.DataFrame({
            'A': [1, 2, 3]
        })
        with pytest.raises(ValueError, match="n_components.* must be between 0 and min"):
            feature_extractor.fit_transform(data)