import pytest
from sklearn.preprocessing import StandardScaler, LabelEncoder, SimpleImputer

class DataTransformationUtility:
    def __init__(self, normalize=True, encode_categorical=True, impute_missing=True):
        self.normalize = normalize
        self.encode_categorical = encode_categorical
        self.impute_missing = impute_missing
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.imputer = SimpleImputer(strategy='mean')

def test_init_happy_path():
    utility = DataTransformationUtility()
    assert utility.normalize is True
    assert utility.encode_categorical is True
    assert utility.impute_missing is True
    assert isinstance(utility.scaler, StandardScaler)
    assert isinstance(utility.label_encoders, dict)
    assert isinstance(utility.imputer, SimpleImputer)

def test_init_edge_cases():
    utility = DataTransformationUtility(normalize=None, encode_categorical=None, impute_missing=None)
    assert utility.normalize is False
    assert utility.encode_categorical is False
    assert utility.impute_missing is False

def test_init_invalid_inputs():
    with pytest.raises(RuntimeError):
        DataTransformationUtility(normalize="invalid", encode_categorical="invalid", impute_missing="invalid")