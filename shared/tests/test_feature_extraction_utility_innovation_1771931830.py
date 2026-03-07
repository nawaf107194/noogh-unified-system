import pytest
import pandas as pd

from shared.feature_extraction_utility import FeatureExtractionUtility

@pytest.fixture
def utility():
    return FeatureExtractionUtility(scaler=StandardScaler(), pca=PCA(n_components=2))

@pytest.mark.parametrize("data, expected_columns", [
    (
        pd.DataFrame([[1, 2], [3, 4]]),
        ["component_1", "component_2"]
    ),
    (
        pd.DataFrame([[0.5, -0.5], [-1.5, 1.5]]),
        ["component_1", "component_2"]
    )
])
def test_happy_path(utility, data, expected_columns):
    transformed_data = utility.fit_transform(data)
    assert isinstance(transformed_data, pd.DataFrame)
    assert transformed_data.columns.tolist() == expected_columns

def test_edge_case_empty_data(utility):
    empty_df = pd.DataFrame()
    transformed_data = utility.fit_transform(empty_df)
    assert transformed_data is None or transformed_data.empty

def test_error_case_none_input(utility):
    none_input = None
    transformed_data = utility.fit_transform(none_input)
    assert transformed_data is None or transformed_data.empty

def test_edge_case_single_row(utility):
    single_row_df = pd.DataFrame([[1, 2]])
    transformed_data = utility.fit_transform(single_row_df)
    assert isinstance(transformed_data, pd.DataFrame)
    assert len(transformed_data) == 1
    assert len(transformed_data.columns) == 2

def test_error_case_invalid_input(utility):
    invalid_input = "not a dataframe"
    with pytest.raises(TypeError):
        utility.fit_transform(invalid_input)