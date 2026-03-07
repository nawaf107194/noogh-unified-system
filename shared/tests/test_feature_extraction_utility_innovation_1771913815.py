import pytest
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class MockFeatureExtractionUtility:
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)

    def fit_transform(self, data):
        """
        Fit the model with data and perform dimensionality reduction.
        
        Parameters:
            data (pd.DataFrame): The input data frame containing raw data.
            
        Returns:
            pd.DataFrame: Transformed data with extracted features.
        """
        # Scale the data
        scaled_data = self.scaler.fit_transform(data)
        
        # Apply PCA
        transformed_data = self.pca.fit_transform(scaled_data)
        
        # Convert back to DataFrame
        columns = [f"component_{i+1}" for i in range(transformed_data.shape[1])]
        return pd.DataFrame(transformed_data, columns=columns)

# Test cases
def test_fit_transform_happy_path():
    utility = MockFeatureExtractionUtility()
    data = pd.DataFrame({
        'feature1': [1.0, 2.0, 3.0],
        'feature2': [4.0, 5.0, 6.0]
    })
    result = utility.fit_transform(data)
    assert isinstance(result, pd.DataFrame)
    assert result.shape == (3, 2)

def test_fit_transform_empty_data():
    utility = MockFeatureExtractionUtility()
    data = pd.DataFrame(columns=['feature1', 'feature2'])
    result = utility.fit_transform(data)
    assert result is None or result.empty

def test_fit_transform_none_data():
    utility = MockFeatureExtractionUtility()
    result = utility.fit_transform(None)
    assert result is None

def test_fit_transform_invalid_data_type():
    utility = MockFeatureExtractionUtility()
    data = {'feature1': [1.0, 2.0, 3.0], 'feature2': [4.0, 5.0, 6.0]}
    with pytest.raises(ValueError):
        utility.fit_transform(data)