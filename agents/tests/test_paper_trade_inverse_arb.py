import pytest

from agents.paper_trade_inverse_arb import FuturesClient, get_funding_rate

class MockFuturesClient:
    def futures_funding_rate(self, symbol, limit):
        if symbol == "BTCUSDT":
            return [{"fundingRate": "0.001"}]
        elif symbol == "INVALID_SYMBOL":
            return []
        else:
            raise Exception("Unexpected symbol")

def test_get_funding_rate_happy_path():
    client = MockFuturesClient()
    arb_agent = FuturesClient(client, "BTCUSDT")
    assert get_funding_rate(arb_agent) == 0.001

def test_get_funding_rate_edge_case_empty_response():
    client = MockFuturesClient()
    arb_agent = FuturesClient(client, "INVALID_SYMBOL")
    assert get_funding_rate(arb_agent) is None

def test_get_funding_rate_error_case_invalid_symbol():
    client = MockFuturesClient()
    arb_agent = FuturesClient(client, "INVALID_SYMBOL")
    with pytest.raises(Exception) as exc_info:
        client.futures_funding_rate("INVALID_SYMBOL", 1)
    assert str(exc_info.value) == "Unexpected symbol"

def test_get_funding_rate_exception_handled():
    class ErrorHandlingFuturesClient(MockFuturesClient):
        def futures_funding_rate(self, *args, **kwargs):
            raise Exception("Test exception")

    client = ErrorHandlingFuturesClient()
    arb_agent = FuturesClient(client, "BTCUSDT")
    assert get_funding_rate(arb_agent) is None