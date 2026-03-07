import pytest
from trading.trade_tracker import get_trade_tracker, DailyTracker

def test_get_trade_tracker_happy_path():
    """Test normal operation - getting existing tracker instance"""
    tracker1 = get_trade_tracker()
    tracker2 = get_trade_tracker()
    
    # Should return same instance
    assert tracker1 is tracker2
    
    # Should be instance of DailyTracker
    assert isinstance(tracker1, DailyTracker)
    assert isinstance(tracker2, DailyTracker)

def test_get_trade_tracker_edge_case():
    """Test edge case - tracker not initialized"""
    global _tracker
    _tracker = None
    
    tracker = get_trade_tracker()
    
    # Should create new instance
    assert isinstance(tracker, DailyTracker)