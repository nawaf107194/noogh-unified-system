import pytest
import pandas as pd
import numpy as np

from src.trading.technical_indicators import liquidity_score

def test_happy_path():
    data = {
        'volume': [100, 200, 300, 400, 500]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=2)
    assert result == 62.5

def test_empty_data():
    df = pd.DataFrame(columns=['volume'])
    result = liquidity_score(df, period=1)
    assert result == 50.0

def test_none_input():
    result = liquidity_score(None, period=1)
    assert result == 50.0

def test_boundary_period_one():
    data = {
        'volume': [100]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=1)
    assert result == 50.0

def test_negative_volume():
    data = {
        'volume': [-100, 200, 300]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=2)
    assert result == 50.0

def test_zero_volume():
    data = {
        'volume': [0, 200, 300]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=2)
    assert result == 50.0

def test_large_period():
    data = {
        'volume': [100, 200, 300, 400, 500]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=100)
    assert result == 50.0

def test_single_value_period():
    data = {
        'volume': [100]
    }
    df = pd.DataFrame(data)
    result = liquidity_score(df, period=1)
    assert result == 50.0