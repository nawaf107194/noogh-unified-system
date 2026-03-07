from typing import Dict
from gateway.app.ml.specialization import Specializer, IntegratedDomainSpecializer

@pytest.mark.parametrize("secrets", [
    {"api_key": "12345", "secret_key": "abcde"},
    {},
    None,
])
def test_init(secrets: Dict[str, str]):
    # Happy path (normal inputs)
    if secrets is not None:
        specializer = Specializer(secrets=secrets)
        assert isinstance(specializer.specializer, IntegratedDomainSpecializer)

    # Edge cases (empty, None)
    else:
        specializer = Specializer(secrets=secrets)
        assert specializer.specializer is None