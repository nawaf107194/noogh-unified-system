import pytest
from unittest.mock import Mock

class TestRateLimiter:

    @pytest.fixture
    def rate_limiter(self):
        from neural_engine.api.rate_limiter import RateLimiter
        return RateLimiter()

    def test_get_client_id_with_ip_address(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = Mock(host="192.168.1.1")
        mock_request.headers = {}
        assert rate_limiter._get_client_id(mock_request) == "ip:192.168.1.1"

    def test_get_client_id_with_api_key(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = None
        mock_request.headers = {"X-API-Key": "abcd1234"}
        assert rate_limiter._get_client_id(mock_request) == "key:abcd1234"

    def test_get_client_id_without_ip_or_api_key(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = None
        mock_request.headers = {}
        assert rate_limiter._get_client_id(mock_request) == "ip:unknown"

    def test_get_client_id_with_empty_headers(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = Mock(host="192.168.1.2")
        mock_request.headers = {}
        assert rate_limiter._get_client_id(mock_request) == "ip:192.168.1.2"

    def test_get_client_id_with_none_client(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = None
        mock_request.headers = {}
        assert rate_limiter._get_client_id(mock_request) == "ip:unknown"

    def test_get_client_id_with_invalid_ip_format(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = Mock(host="invalid_ip")
        mock_request.headers = {}
        assert rate_limiter._get_client_id(mock_request) == "ip:invalid_ip"

    def test_get_client_id_with_invalid_api_key_header_name(self, rate_limiter):
        mock_request = Mock()
        mock_request.client = None
        mock_request.headers = {"Invalid-Header": "abcd1234"}
        assert rate_limiter._get_client_id(mock_request) == "ip:unknown"