import pytest

class TestMessaging1771681690:
    def test_happy_path(self):
        from unified_core.messaging_1771681690 import MessagingStrategy, Messaging1771681690
        
        strategy = MessagingStrategy()
        messaging = Messaging1771681690(strategy)
        
        assert messaging._strategy == strategy

    def test_none_input(self):
        from unified_core.messaging_1771681690 import MessagingStrategy, Messaging1771681690
        
        messaging = Messaging1771681690(None)
        
        assert messaging._strategy is None
        
    @pytest.mark.parametrize("invalid_strategy", [123, "string", [], {}, lambda x: x])
    def test_invalid_inputs(self, invalid_strategy):
        from unified_core.messaging_1771681690 import Messaging1771681690
        
        with pytest.raises(TypeError):
            Messaging1771681690(invalid_strategy)