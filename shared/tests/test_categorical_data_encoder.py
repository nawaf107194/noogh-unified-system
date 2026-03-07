import pytest
import pandas as pd

from shared.categorical_data_encoder import CategoricalDataEncoder

def test_happy_path():
    # Arrange
    df = pd.DataFrame({
        'A': ['a', 'b', 'c'],
        'B': [1, 2, 3]
    })

    # Act
    encoder = CategoricalDataEncoder(df)

    # Assert
    assert isinstance(encoder, CategoricalDataEncoder)
    assert encoder.df.equals(df)
    assert not hasattr(encoder, 'transformed_df')

def test_edge_case_empty_dataframe():
    # Arrange
    df = pd.DataFrame()

    # Act
    encoder = CategoricalDataEncoder(df)

    # Assert
    assert isinstance(encoder, CategoricalDataEncoder)
    assert encoder.df.empty
    assert not hasattr(encoder, 'transformed_df')

def test_edge_case_none_input():
    # Arrange
    df = None

    # Act & Assert
    with pytest.raises(ValueError):
        CategoricalDataEncoder(df)

def test_error_case_invalid_dataframe_type():
    # Arrange
    invalid_input = "Not a DataFrame"

    # Act & Assert
    with pytest.raises(TypeError):
        CategoricalDataEncoder(invalid_input)