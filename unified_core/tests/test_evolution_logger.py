"""Tests for evolution_logger — request ID injection and logging setup."""
import logging
import pytest
from unified_core.evolution.evolution_logger import (
    set_request_id,
    get_request_id,
    clear_request_id,
    RequestIdFilter,
    setup_evolution_logging,
)


class TestRequestIdContext:
    def test_default_is_no_req(self):
        clear_request_id()
        assert get_request_id() == "no-req"

    def test_set_and_get(self):
        rid = set_request_id("test-123")
        assert rid == "test-123"
        assert get_request_id() == "test-123"
        clear_request_id()

    def test_auto_generate_id(self):
        rid = set_request_id()
        assert len(rid) == 12  # hex[:12]
        assert get_request_id() == rid
        clear_request_id()

    def test_clear_resets(self):
        set_request_id("abc")
        clear_request_id()
        assert get_request_id() == "no-req"


class TestRequestIdFilter:
    def test_injects_request_id(self):
        set_request_id("filter-test")
        filt = RequestIdFilter(component="test")
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        filt.filter(record)
        assert record.request_id == "filter-test"
        assert record.component == "test"
        clear_request_id()

    def test_default_component(self):
        filt = RequestIdFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        filt.filter(record)
        assert record.component == "evolution"

    def test_filter_always_returns_true(self):
        filt = RequestIdFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        assert filt.filter(record) is True


class TestSetupEvolutionLogging:
    def test_returns_logger(self):
        logger = setup_evolution_logging(level=logging.DEBUG)
        assert logger is not None
        assert logger.name == "unified_core.evolution"

    def test_adds_handler_if_none(self):
        logger = logging.getLogger("unified_core.evolution")
        # Clear existing handlers for clean test
        original_handlers = logger.handlers[:]
        logger.handlers.clear()
        try:
            setup_evolution_logging()
            assert len(logger.handlers) >= 1
        finally:
            logger.handlers = original_handlers

    def test_idempotent(self):
        setup_evolution_logging()
        handler_count = len(logging.getLogger("unified_core.evolution").handlers)
        setup_evolution_logging()  # Call again
        # Should not add duplicate handlers
        assert len(logging.getLogger("unified_core.evolution").handlers) == handler_count
