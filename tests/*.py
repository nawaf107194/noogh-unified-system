import pytest
from tests.test_phase8_signing import test_signing_function
from tests.test_model_integration import test_model_integration_function
from tests.test_deletion_survival import test_deletion_function

@pytest.mark.parametrize("test_func", [
    test_signing_function,
    test_model_integration_function,
    test_deletion_function
])
def test_functions(test_func):
    test_func()

# Repeat for other test functions in different files