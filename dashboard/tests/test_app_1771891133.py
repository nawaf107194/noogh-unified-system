import pytest

class TestFetchData:
    def setup_method(self):
        self.fetch_data = lambda query, params=None: None  # Mock fetch_data for testing

    @pytest.mark.parametrize("query, params", [
        ("SELECT * FROM users WHERE id = %s", (1,)),
        ("INSERT INTO logs (message) VALUES (%s)", ("error",)),
        ("UPDATE settings SET value = %s WHERE key = %s", ("new_value", "key")),
    ])
    def test_happy_path(self, query, params):
        result = self.fetch_data(query, params)
        assert result is not None

    @pytest.mark.parametrize("query, params", [
        (None, None),
        ("SELECT * FROM users WHERE id =", []),
        ("SELECT * FROM users LIMIT %s", (-1,)),
    ])
    def test_edge_cases(self, query, params):
        result = self.fetch_data(query, params)
        assert result is None

    @pytest.mark.parametrize("query, params", [
        (None, "not a tuple"),
        ({"invalid": "input"}, None),
    ])
    def test_invalid_inputs(self, query, params):
        result = self.fetch_data(query, params)
        assert result is None