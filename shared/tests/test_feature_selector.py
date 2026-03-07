import pytest
from shared.feature_selector import FeatureSelector

def test_fit_transform_happy_path():
    selector = FeatureSelector()
    X = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    y = pd.Series([0, 1, 0])
    result = selector.fit_transform(X, y)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    # Add more specific assertions based on expected output

def test_fit_transform_empty_input():
    selector = FeatureSelector()
    X = pd.DataFrame(columns=['A', 'B'])
    y = pd.Series([])
    result = selector.fit_transform(X, y)
    assert isinstance(result, pd.DataFrame)
    assert result.empty

def test_fit_transform_none_input():
    selector = FeatureSelector()
    X = None
    y = None
    result = selector.fit_transform(X, y)
    assert result is None

def test_fit_transform_invalid_input():
    selector = FeatureSelector()
    X = 'not a dataframe'
    y = 123
    result = selector.fit_transform(X, y)
    assert result is None