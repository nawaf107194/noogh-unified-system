import pytest
from sklearn.feature_selection import SelectKBest, f_classif

class FeatureSelector:
    def __init__(self, k=10):
        self.k = k
        self.selector = SelectKBest(score_func=f_classif, k=k)

def test_happy_path():
    selector = FeatureSelector(k=5)
    assert selector.k == 5
    assert isinstance(selector.selector, SelectKBest)
    assert selector.selector.score_func == f_classif

def test_edge_case_k_zero():
    selector = FeatureSelector(k=0)
    assert selector.k == 0
    assert isinstance(selector.selector, SelectKBest)
    assert selector.selector.score_func == f_classif

def test_edge_case_k_negative():
    selector = FeatureSelector(k=-5)
    assert selector.k == -5
    assert isinstance(selector.selector, SelectKBest)
    assert selector.selector.score_func == f_classif

def test_error_case_non_integer_k():
    with pytest.raises(TypeError):
        FeatureSelector(k='five')

def test_error_case_negative_k():
    with pytest.raises(ValueError):
        FeatureSelector(k=-1)