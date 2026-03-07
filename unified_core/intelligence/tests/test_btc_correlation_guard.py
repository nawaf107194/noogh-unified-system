import pytest
import pandas as pd

from unified_core.intelligence.btc_correlation_guard import BtcCorrelationGuard

@pytest.fixture
def btc_correlation_guard():
    return BtcCorrelationGuard()

@pytest.fixture
def sample_btc_df():
    data = {
        "close": [100, 102, 101, 103, 104]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_altcoin_df():
    data = {
        "close": [150, 152, 151, 153, 154]
    }
    return pd.DataFrame(data)

def test_calculate_correlation_happy_path(btc_correlation_guard, sample_btc_df, sample_altcoin_df):
    result = btc_correlation_guard.calculate_correlation(sample_btc_df, "ETH")
    assert isinstance(result, float)
    assert -1 <= result <= 1

def test_calculate_correlation_empty_data(btc_correlation_guard, sample_btc_df):
    empty_df = pd.DataFrame()
    result = btc_correlation_guard.calculate_correlation(empty_df, "ETH")
    assert result == 0.0

def test_calculate_correlation_missing_column(btc_correlation_guard, sample_btc_df):
    sample_btc_df.drop(columns=["close"], inplace=True)
    result = btc_correlation_guard.calculate_correlation(sample_btc_df, "ETH")
    assert result == 0.0

def test_calculate_correlation_none_input(btc_correlation_guard):
    result = btc_correlation_guard.calculate_correlation(None, "ETH")
    assert result == 0.0