import pytest

@pytest.mark.parametrize("data,expected_data", [
    (123, 123),
    ("test", "test"),
    ([1,2,3], [1,2,3]),
    ({"key": "value"}, {"key": "value"}),
    (True, True)
])
def test_init_happy_path(data, expected_data):
    instance = YourClass(data)
    assert instance.data == expected_data

@pytest.mark.parametrize("data", [
    "",
    [],
    {},
    None
])
def test_init_edge_cases(data):
    instance = YourClass(data)
    assert instance.data == data