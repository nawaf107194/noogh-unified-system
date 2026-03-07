import pytest

from gateway.app.ml.specialization import IntegratedDomainSpecializer, Specialization

def test_specialization_init_happy_path():
    secrets = {
        'key1': 'value1',
        'key2': 'value2'
    }
    specialization = Specialization(secrets=secrets)
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)

def test_specialization_init_edge_case_empty_secrets():
    secrets = {}
    specialization = Specialization(secrets=secrets)
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)

def test_specialization_init_edge_case_none_secrets():
    specialization = Specialization(secrets=None)
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)

def test_specialization_init_error_case_invalid_secrets():
    class InvalidSecrets:
        pass

    with pytest.raises(TypeError):
        Specialization(secrets=InvalidSecrets())