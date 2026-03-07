import pytest
from gateway.app.core.math_evaluator import extract_math_expression

@pytest.mark.parametrize("query, expected", [
    ("احسب 15 × 7 + 23", "15 * 7 + 23"),
    ("كم ناتج 100 ÷ 4 + 6", "100 / 4 + 6"),
    ("5 + 3 = ?", "5 + 3"),
])
def test_extract_math_expression_happy_path(query, expected):
    result = extract_math_expression(query)
    assert result == expected

@pytest.mark.parametrize("query, expected", [
    ("", None),
    (None, None),
    (" ", None),
    ("1234567890", "1234567890"),
])
def test_extract_math_expression_edge_cases(query, expected):
    result = extract_math_expression(query)
    assert result == expected

@pytest.mark.parametrize("query", [
    "احسب 15 × 7 +",
    "كم ناتج 100 ÷ 4 +",
    "5 + 3 ?",
    "احسب 15 × 7 + 23 اضافه",
    "احسب 15 × 7 + 23 رفع",
])
def test_extract_math_expression_error_cases(query):
    result = extract_math_expression(query)
    assert result is None

# Async behavior (if applicable)
# Since the function does not involve any async operations or I/O, this part is not applicable.