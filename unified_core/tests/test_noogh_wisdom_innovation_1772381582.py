import pytest
from typing import List, Dict

class NooghWisdom:
    @classmethod
    def body(cls, kline: Dict) -> float:
        return abs(kline["close"] - kline["open"])

    @classmethod
    def lower_shadow(cls, kline: Dict) -> float:
        return kline["low"] if kline["high"] != kline["low"] else 0.0001

    @classmethod
    def upper_shadow(cls, kline: Dict) -> float:
        return cls.body(kline)

    @classmethod
    def is_bullish(cls, kline: Dict) -> bool:
        return kline["close"] > kline["open"]

    @classmethod
    def is_bearish(cls, kline: Dict) -> bool:
        return kline["close"] < kline["open"]

def test_detect_happy_path():
    data = [
        {"high": 100, "low": 90, "open": 85, "close": 92},
        {"high": 105, "low": 95, "open": 93, "close": 97},
        {"high": 110, "low": 100, "open": 98, "close": 103}
    ]
    expected = ["Doji (تردد — إشارة انعكاس محتملة)", "Bullish Engulfing (ابتلاع صعودي — إشارة شراء قوية)"]
    assert NooghWisdom.detect(data) == expected

def test_detect_edge_cases_empty():
    assert NooghWisdom.detect([]) == ["لا يوجد نمط واضح"]

def test_detect_edge_cases_none():
    assert NooghWisdom.detect(None) == []

def test_detect_edge_cases_boundary():
    data = [
        {"high": 1, "low": 0.95, "open": 0.92, "close": 0.98}
    ]
    expected = ["Doji (تردد — إشارة انعكاس محتملة)", "Bullish Marubozu (شمعة صعودية كاملة — ضغط شراء قوي)"]
    assert NooghWisdom.detect(data) == expected

def test_detect_error_cases_invalid_input():
    with pytest.raises(TypeError):
        NooghWisdom.detect("invalid input")