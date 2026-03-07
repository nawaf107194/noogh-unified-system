import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Mocking imports
from unittest.mock import patch
from agents.download_multi_symbol import main, download_historical_data, logger

# Mock the logger to capture output
@pytest.fixture
def mock_logger():
    with patch.object(logger, 'info') as mock_info:
        yield mock_info

@patch('agents.download_multi_symbol.download_historical_data')
def test_main_happy_path(mock_download_historical_data, mock_logger):
    symbols = ["BTCUSDT", "ETHUSDT"]
    mock_download_historical_data.side_effect = lambda symbol, interval, start_str, end_str: f"DataFrame for {symbol} with interval {interval}"

    main()

    assert mock_logger.call_count == 10
    assert mock_logger.call_args_list[0] == pytest.call("="*70)
    assert mock_logger.call_args_list[1] == pytest.call("🏛️ MULTI-SYMBOL DATA DOWNLOAD")
    assert mock_logger.call_args_list[2] == pytest.call("="*70)
    assert mock_logger.call_args_list[3] == pytest.call(f"Symbols: {', '.join(symbols)}")
    assert mock_logger.call_args_list[4] == pytest.call(f"Period: 1 Jan 1970 00:00:00 → 5 Dec 2023 00:00:00")
    assert mock_logger.call_args_list[5] == pytest.call("="*70)
    assert mock_logger.call_args_list[6] == pytest.call("\n" + "="*70)
    assert mock_logger.call_args_list[7] == pytest.call("📊 BTCUSDT")
    assert mock_logger.call_args_list[8] == pytest.call("\n" + "="*70)
    assert mock_logger.call_args_list[9] == pytest.call("   💾 BTCUSDT_5m_12M.parquet (4,380 rows)")

@patch('agents.download_multi_symbol.download_historical_data')
def test_main_empty_symbols(mock_download_historical_data, mock_logger):
    symbols = []
    
    main()

    assert mock_logger.call_count == 3
    assert mock_logger.call_args_list[0] == pytest.call("="*70)
    assert mock_logger.call_args_list[1] == pytest.call("🏛️ MULTI-SYMBOL DATA DOWNLOAD")
    assert mock_logger.call_args_list[2] == pytest.call("="*70)

@patch('agents.download_multi_symbol.download_historical_data')
def test_main_invalid_symbols(mock_download_historical_data, mock_logger):
    symbols = ["BTCUSDT", "INVALIDSYMBOL"]
    
    main()

    assert mock_logger.call_count == 6
    assert mock_logger.call_args_list[3] == pytest.call("\n" + "="*70)
    assert mock_logger.call_args_list[4] == pytest.call("📊 INVALIDSYMBOL")
    assert mock_logger.call_args_list[5] == pytest.call("\n" + "="*70)

@patch('agents.download_multi_symbol.download_historical_data')
def test_main_error_in_download(mock_download_historical_data, mock_logger):
    symbols = ["BTCUSDT"]
    mock_download_historical_data.side_effect = lambda symbol, interval, start_str, end_str: None

    main()

    assert mock_logger.call_count == 3
    assert mock_logger.call_args_list[1] == pytest.call("🏛️ MULTI-SYMBOL DATA DOWNLOAD")
    assert mock_logger.call_args_list[2] == pytest.call("="*70)