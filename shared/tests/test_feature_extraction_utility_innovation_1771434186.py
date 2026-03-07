import pytest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class FeatureExtractionUtility:
    def __init__(self, n_components=None, scaler=StandardScaler()):
        self.n_components = n_components
        self.scaler = scaler
        self.pca = PCA(n_components=n_components)

def test_happy_path():
    feu = FeatureExtractionUtility(n_components=5)
    assert feu.n_components == 5
    assert isinstance(feu.scaler, StandardScaler)
    assert isinstance(feu.pca, PCA)
    assert feu.pca.n_components == 5

def test_default_values():
    feu = FeatureExtractionUtility()
    assert feu.n_components is None
    assert isinstance(feu.scaler, StandardScaler)
    assert isinstance(feu.pca, PCA)
    assert feu.pca.n_components is None

def test_edge_case_n_components_none():
    feu = FeatureExtractionUtility(n_components=None)
    assert feu.n_components is None
    assert isinstance(feu.scaler, StandardScaler)
    assert isinstance(feu.pca, PCA)
    assert feu.pca.n_components is None

def test_custom_scaler():
    custom_scaler = MinMaxScaler()
    feu = FeatureExtractionUtility(scaler=custom_scaler)
    assert feu.n_components is None
    assert feu.scaler == custom_scaler
    assert isinstance(feu.pca, PCA)
    assert feu.pca.n_components is None

def test_error_case_invalid_n_components():
    with pytest.raises(ValueError):
        FeatureExtractionUtility(n_components="five")

def test_error_case_invalid_scaler():
    with pytest.raises(TypeError):
        FeatureExtractionUtility(scaler="not_a_scaler")

# Since the class does not involve asynchronous operations, we skip the async behavior test.