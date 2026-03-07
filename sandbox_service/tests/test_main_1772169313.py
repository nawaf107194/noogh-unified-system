import pytest

# Parameterized data for testing sandbox function calls
test_data = [
    ("safe_function_call", {"input": 5}, 25),
    ("sqrt_transform", {"input": 16}, 4),
    # Add more test cases as needed
]

@pytest.mark.parametrize("function_name, input_params, expected_output", test_data)
def test_sandbox_functions(function_name, input_params, expected_output):
    # Assuming `sandbox_service.main` is the module where these functions are defined
    result = getattr(sandbox_service.main, function_name)(**input_params)
    assert result == expected_output