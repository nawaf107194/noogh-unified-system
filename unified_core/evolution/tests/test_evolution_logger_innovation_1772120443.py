import pytest

from unified_core.evolution.evolution_logger import get_request_id

def test_get_request_id_happy_path():
    _context = type('_Context', (object,), {'request_id': '12345'})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('unified_core.evolution.evolution_logger._context', _context)
        assert get_request_id() == '12345'

def test_get_request_id_no_request_id():
    _context = type('_Context', (object,), {})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('unified_core.evolution.evolution_logger._context', _context)
        assert get_request_id() == 'no-req'

def test_get_request_id_none_request_id():
    _context = type('_Context', (object,), {'request_id': None})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('unified_core.evolution.evolution_logger._context', _context)
        assert get_request_id() == 'no-req'