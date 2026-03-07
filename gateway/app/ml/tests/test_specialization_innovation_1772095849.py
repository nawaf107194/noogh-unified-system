import pytest
from typing import Dict

class IntegratedDomainSpecializer:
    def __init__(self, secrets: Dict[str, str]):
        self.secrets = secrets

class Specialization:
    def __init__(self, secrets: Dict[str, str]):
        self.specializer = IntegratedDomainSpecializer(secrets=secrets)

def test_init_happy_path():
    secrets = {'key': 'value'}
    specialization = Specialization(secrets)
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)
    assert specialization.specializer.secrets == secrets

def test_init_edge_case_empty_dict():
    secrets = {}
    specialization = Specialization(secrets)
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)
    assert specialization.specializer.secrets == {}

def test_init_edge_case_none():
    with pytest.raises(TypeError):
        Specialization(None)

def test_init_error_case_invalid_input():
    invalid_secrets = 'not a dictionary'
    with pytest.raises(TypeError):
        Specialization(invalid_secrets)