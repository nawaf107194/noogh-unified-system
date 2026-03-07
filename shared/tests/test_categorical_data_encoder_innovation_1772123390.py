import pytest
from categorical_data_encoder import CategoricalDataEncoder
from sklearn.preprocessing import LabelEncoder
import pandas as pd

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'A': ['foo', 'bar', 'baz'],
        'B': [1, 2, 3],
        'C': ['one', 'two', 'one']
    })

def test_label_encode_happy_path(sample_data):
    encoder = CategoricalDataEncoder(sample_data.copy())
    result = encoder.label_encode()
    expected_columns = ['A', 'C']
    for col in expected_columns:
        assert all(isinstance(x, int) for x in result[col])
    
    le_a = LabelEncoder().fit_transform(['foo', 'bar', 'baz'])
    le_c = LabelEncoder().fit_transform(['one', 'two', 'one'])
    assert (result['A'].values == le_a).all()
    assert (result['C'].values == le_c).all()

def test_label_encode_all_columns(sample_data):
    encoder = CategoricalDataEncoder(sample_data.copy())
    result = encoder.label_encode(columns=None)
    expected_columns = ['A', 'C']
    for col in expected_columns:
        assert all(isinstance(x, int) for x in result[col])
    
    le_a = LabelEncoder().fit_transform(['foo', 'bar', 'baz'])
    le_c = LabelEncoder().fit_transform(['one', 'two', 'one'])
    assert (result['A'].values == le_a).all()
    assert (result['C'].values == le_c).all()

def test_label_encode_empty_columns(sample_data):
    encoder = CategoricalDataEncoder(pd.DataFrame({}))
    result = encoder.label_encode(columns=[])
    assert result.empty

def test_label_encode_invalid_column(sample_data):
    encoder = CategoricalDataEncoder(sample_data.copy())
    with pytest.raises(KeyError):
        encoder.label_encode(columns=['D'])

def test_label_encode_none_columns(sample_data):
    encoder = CategoricalDataEncoder(sample_data.copy())
    result = encoder.label_encode(columns=None)
    expected_columns = ['A', 'C']
    for col in expected_columns:
        assert all(isinstance(x, int) for x in result[col])
    
    le_a = LabelEncoder().fit_transform(['foo', 'bar', 'baz'])
    le_c = LabelEncoder().fit_transform(['one', 'two', 'one'])
    assert (result['A'].values == le_a).all()
    assert (result['C'].values == le_c).all()

def test_label_encode_mixed_types(sample_data):
    encoder = CategoricalDataEncoder(pd.DataFrame({
        'A': ['foo', 'bar', 'baz'],
        'B': [1, 2, 3],
        'C': ['one', 'two', 'one']
    }))
    result = encoder.label_encode(columns=['A', 'B'])
    expected_columns = ['A', 'C']
    for col in expected_columns:
        assert all(isinstance(x, int) for x in result[col])
    
    le_a = LabelEncoder().fit_transform(['foo', 'bar', 'baz'])
    le_c = LabelEncoder().fit_transform(['one', 'two', 'one'])
    assert (result['A'].values == le_a).all()
    assert (result['C'].values == le_c).all()