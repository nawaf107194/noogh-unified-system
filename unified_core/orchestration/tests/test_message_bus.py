import pytest
from unittest.mock import Mock

from unified_core.orchestration.message_bus import MessageBus, logger

class TestMessageBus:
    def setup_method(self):
        self.message_bus = MessageBus()

    def test_subscribe_happy_path(self):
        callback = Mock()
        topic = "agent:code_executor"
        
        result = self.message_bus.subscribe(topic, callback)
        
        assert result is None
        assert len(self.message_bus._subscribers[topic]) == 1
        assert callback in self.message_bus._subscribers[topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {topic}")

    def test_subscribe_edge_cases_empty_topic(self):
        callback = Mock()
        empty_topic = ""
        
        result = self.message_bus.subscribe(empty_topic, callback)
        
        assert result is None
        assert len(self.message_bus._subscribers[empty_topic]) == 1
        assert callback in self.message_bus._subscribers[empty_topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {empty_topic}")

    def test_subscribe_edge_cases_none_topic(self):
        callback = Mock()
        none_topic = None
        
        result = self.message_bus.subscribe(none_topic, callback)
        
        assert result is None
        assert len(self.message_bus._subscribers[none_topic]) == 1
        assert callback in self.message_bus._subscribers[none_topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {none_topic}")

    def test_subscribe_edge_cases_none_callback(self):
        topic = "agent:code_executor"
        
        result = self.message_bus.subscribe(topic, None)
        
        assert result is None
        assert len(self.message_bus._subscribers[topic]) == 1
        assert None in self.message_bus._subscribers[topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {topic}")

    def test_subscribe_error_cases_invalid_topic_type(self):
        callback = Mock()
        invalid_topic = 123
        
        result = self.message_bus.subscribe(invalid_topic, callback)
        
        assert result is None
        assert len(self.message_bus._subscribers[invalid_topic]) == 1
        assert callback in self.message_bus._subscribers[invalid_topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {invalid_topic}")

    def test_subscribe_error_cases_invalid_callback_type(self):
        topic = "agent:code_executor"
        
        result = self.message_bus.subscribe(topic, 123)
        
        assert result is None
        assert len(self.message_bus._subscribers[topic]) == 1
        assert 123 in self.message_bus._subscribers[topic]
        logger.info.assert_called_once_with(f"Subscribed to topic: {topic}")