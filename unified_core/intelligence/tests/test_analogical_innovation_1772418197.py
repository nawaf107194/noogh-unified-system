import pytest

def test_structural_similarity_happy_path():
    struct_a = {'a': 1, 'b': 2, 'c': 3}
    struct_b = {'a': 1, 'b': 2, 'c': 4}
    assert _structural_similarity(struct_a, struct_b) == 0.75

def test_structural_similarity_no_common_keys():
    struct_a = {'a': 1, 'b': 2}
    struct_b = {'c': 3, 'd': 4}
    assert _structural_similarity(struct_a, struct_b) == 0.0

def test_structural_similarity_different_types():
    struct_a = {'a': 1, 'b': [1, 2]}
    struct_b = {'a': 1, 'b': {1: 2}}
    assert _structural_similarity(struct_a, struct_b) == 0.5

def test_structural_similarity_empty_dicts():
    struct_a = {}
    struct_b = {}
    assert _structural_similarity(struct_a, struct_b) == 0.0

def test_structural_similarity_one_empty_dict():
    struct_a = {'a': 1}
    struct_b = {}
    assert _structural_similarity(struct_a, struct_b) == 0.0

def test_structural_similarity_none_input():
    with pytest.raises(TypeError):
        _structural_similarity(None, {'b': 2})

def test_structural_similarity_invalid_types():
    with pytest.raises(TypeError):
        _structural_similarity('not a dict', {'b': 2})