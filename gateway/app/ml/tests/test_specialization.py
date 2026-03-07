import pytest

from gateway.app.ml.specialization import IntegratedDomainSpecializer, Specialization


@pytest.fixture
def default_secrets():
    return {
        'key1': 'value1',
        'key2': 'value2'
    }


def test_happy_path(default_secrets):
    specialization = Specialization(secrets=default_secrets)
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)


def test_empty_secrets():
    specialization = Specialization(secrets={})
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)


def test_none_secrets(default_secrets):
    specialization = Specialization(secrets=None)
    assert specialization.specializer is not None
    assert isinstance(specialization.specializer, IntegratedDomainSpecializer)


def test_invalid_input():
    with pytest.raises(ValueError) as exc_info:
        Specialization(secrets='not a dict')
    assert "secrets must be a dictionary" in str(exc_info.value)