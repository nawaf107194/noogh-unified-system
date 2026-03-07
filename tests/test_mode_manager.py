"""
Tests for ModeManager

Tests the dual-mode system (CHAT/CRAFT).
"""

import pytest
from neural_engine.neural_core.mode_manager import (
    ModeManager,
    AgentMode,
    create_chat_mode,
    create_craft_mode
)


class TestModeManager:
    """Test suite for ModeManager"""
    
    def test_initialization_default(self):
        """Test default initialization"""
        manager = ModeManager()
        
        assert manager.current_mode == AgentMode.CHAT
        assert len(manager.mode_history) == 1
    
    def test_initialization_craft_mode(self):
        """Test initialization in CRAFT mode"""
        manager = ModeManager(initial_mode=AgentMode.CRAFT)
        
        assert manager.current_mode == AgentMode.CRAFT
    
    def test_get_current_context(self):
        """Test getting current context"""
        manager = ModeManager()
        context = manager.get_current_context()
        
        assert context is not None
        assert context.current_mode == AgentMode.CHAT
        assert context.can_use_tools == True
        assert context.requires_approval == True
    
    def test_switch_to_craft(self):
        """Test switching to CRAFT mode"""
        manager = ModeManager()  # starts in CHAT
        
        context = manager.switch_to_craft()
        
        assert manager.current_mode == AgentMode.CRAFT
        assert context.requires_approval == False
        assert len(manager.mode_history) == 2
    
    def test_switch_to_chat(self):
        """Test switching to CHAT mode"""
        manager = ModeManager(initial_mode=AgentMode.CRAFT)
        
        context = manager.switch_to_chat()
        
        assert manager.current_mode == AgentMode.CHAT
        assert context.requires_approval == True
    
    def test_is_chat_mode(self):
        """Test chat mode check"""
        manager = ModeManager()
        
        assert manager.is_chat_mode() == True
        assert manager.is_craft_mode() == False
    
    def test_is_craft_mode(self):
        """Test craft mode check"""
        manager = ModeManager(initial_mode=AgentMode.CRAFT)
        
        assert manager.is_craft_mode() == True
        assert manager.is_chat_mode() == False
    
    def test_should_plan_first(self):
        """Test planning requirement"""
        manager = ModeManager()
        
        assert manager.should_plan_first() == True
        
        manager.switch_to_craft()
        assert manager.should_plan_first() == False
    
    def test_can_execute_directly(self):
        """Test direct execution capability"""
        manager = ModeManager()
        
        assert manager.can_execute_directly() == False
        
        manager.switch_to_craft()
        assert manager.can_execute_directly() == True
    
    def test_mode_history(self):
        """Test mode history tracking"""
        manager = ModeManager()
        
        manager.switch_to_craft()
        manager.switch_to_chat()
        manager.switch_to_craft()
        
        history = manager.get_mode_history()
        
        assert len(history) == 4
        assert history[0] == AgentMode.CHAT
        assert history[1] == AgentMode.CRAFT
        assert history[2] == AgentMode.CHAT
        assert history[3] == AgentMode.CRAFT
    
    def test_reset(self):
        """Test reset to default"""
        manager = ModeManager()
        manager.switch_to_craft()
        manager.switch_to_chat()
        
        manager.reset()
        
        assert manager.current_mode == AgentMode.CHAT
        assert len(manager.mode_history) == 1
    
    def test_get_mode_description(self):
        """Test mode description"""
        manager = ModeManager()
        
        desc = manager.get_mode_description()
        assert "تخطيط" in desc or "حوار" in desc
        
        manager.switch_to_craft()
        desc = manager.get_mode_description()
        assert "تنفيذ" in desc


class TestModeHelpers:
    """Test helper functions"""
    
    def test_create_chat_mode(self):
        """Test chat mode creation helper"""
        manager = create_chat_mode()
        
        assert manager.current_mode == AgentMode.CHAT
    
    def test_create_craft_mode(self):
        """Test craft mode creation helper"""
        manager = create_craft_mode()
        
        assert manager.current_mode == AgentMode.CRAFT


class TestModeWorkflow:
    """Test typical workflows"""
    
    def test_planning_workflow(self):
        """Test planning then executing workflow"""
        manager = ModeManager()
        
        # Start in CHAT for planning
        assert manager.should_plan_first()
        
        # Plan...
        # Then switch to execute
        manager.switch_to_craft()
        
        assert manager.can_execute_directly()
    
    def test_multiple_switches(self):
        """Test multiple mode switches"""
        manager = ModeManager()
        
        for _ in range(5):
            manager.switch_to_craft()
            assert manager.is_craft_mode()
            
            manager.switch_to_chat()
            assert manager.is_chat_mode()
        
        # History should track all switches
        assert len(manager.get_mode_history()) == 11  # 1 initial + 10 switches


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
