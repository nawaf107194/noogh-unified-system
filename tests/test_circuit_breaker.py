#!/usr/bin/env python3
"""
Unit Tests for Daily Loss Circuit Breaker
==========================================
Tests the risk management features added to AutonomousTradingAgent:
- Daily PnL tracking
- Consecutive loss tracking
- Circuit breaker activation/deactivation
- Daily stats reset
"""

import unittest
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

from agents.autonomous_trading_agent import AutonomousTradingAgent, PaperTradingEngine


class TestCircuitBreaker(unittest.TestCase):
    """Test suite for circuit breaker functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create agent with paper trading mode (no real API calls)
        self.agent = AutonomousTradingAgent(mode='observe', testnet=True)

        # Set initial balance
        self.agent.paper_engine.balance = 10000.0

        # Reset circuit breaker state
        self.agent.daily_pnl = 0.0
        self.agent.consecutive_losses = 0
        self.agent.circuit_breaker_active = False
        self.agent.last_reset_date = datetime.now().date()

    def test_daily_stats_initialization(self):
        """Test that daily stats are initialized correctly"""
        self.assertEqual(self.agent.daily_pnl, 0.0)
        self.assertEqual(self.agent.consecutive_losses, 0)
        self.assertFalse(self.agent.circuit_breaker_active)
        self.assertEqual(self.agent.max_daily_loss_pct, 0.02)  # 2%
        self.assertEqual(self.agent.max_consecutive_losses, 3)

    def test_update_daily_stats_win(self):
        """Test daily stats update on winning trade"""
        # Simulate a win
        self.agent._update_daily_stats(100.0)

        self.assertEqual(self.agent.daily_pnl, 100.0)
        self.assertEqual(self.agent.consecutive_losses, 0)

    def test_update_daily_stats_loss(self):
        """Test daily stats update on losing trade"""
        # Simulate a loss
        self.agent._update_daily_stats(-50.0)

        self.assertEqual(self.agent.daily_pnl, -50.0)
        self.assertEqual(self.agent.consecutive_losses, 1)

    def test_consecutive_losses_increment(self):
        """Test consecutive losses increment correctly"""
        # Three consecutive losses
        self.agent._update_daily_stats(-30.0)
        self.assertEqual(self.agent.consecutive_losses, 1)

        self.agent._update_daily_stats(-40.0)
        self.assertEqual(self.agent.consecutive_losses, 2)

        self.agent._update_daily_stats(-50.0)
        self.assertEqual(self.agent.consecutive_losses, 3)

    def test_consecutive_losses_reset_on_win(self):
        """Test consecutive losses reset when a win occurs"""
        # Two losses
        self.agent._update_daily_stats(-30.0)
        self.agent._update_daily_stats(-40.0)
        self.assertEqual(self.agent.consecutive_losses, 2)

        # Win resets the counter
        self.agent._update_daily_stats(100.0)
        self.assertEqual(self.agent.consecutive_losses, 0)

    def test_circuit_breaker_activates_on_daily_loss(self):
        """Test circuit breaker activates when daily loss limit is exceeded"""
        # Set balance
        self.agent.paper_engine.balance = 10000.0

        # Max daily loss is 2% = $200
        # Simulate losses totaling $250
        self.agent._update_daily_stats(-150.0)
        self.agent._update_daily_stats(-100.0)

        # Circuit breaker should activate
        self.assertFalse(self.agent._check_circuit_breaker())
        self.assertTrue(self.agent.circuit_breaker_active)

    def test_circuit_breaker_activates_on_consecutive_losses(self):
        """Test circuit breaker activates after max consecutive losses"""
        # Three consecutive losses (matching max_consecutive_losses)
        self.agent._update_daily_stats(-30.0)
        self.agent._update_daily_stats(-40.0)
        self.agent._update_daily_stats(-50.0)

        # Circuit breaker should activate
        self.assertFalse(self.agent._check_circuit_breaker())
        self.assertTrue(self.agent.circuit_breaker_active)

    def test_circuit_breaker_allows_trading_within_limits(self):
        """Test circuit breaker allows trading when within limits"""
        # Small loss within limits
        self.agent._update_daily_stats(-50.0)

        # Should allow trading
        self.assertTrue(self.agent._check_circuit_breaker())
        self.assertFalse(self.agent.circuit_breaker_active)

    def test_daily_reset(self):
        """Test that daily stats reset on new trading day"""
        # Set some losses
        self.agent.daily_pnl = -150.0
        self.agent.consecutive_losses = 2
        self.agent.circuit_breaker_active = True

        # Simulate new day by changing last_reset_date
        self.agent.last_reset_date = (datetime.now() - timedelta(days=1)).date()

        # Reset should happen
        self.agent._reset_daily_stats()

        self.assertEqual(self.agent.daily_pnl, 0.0)
        self.assertEqual(self.agent.consecutive_losses, 0)
        self.assertFalse(self.agent.circuit_breaker_active)
        self.assertEqual(self.agent.last_reset_date, datetime.now().date())

    def test_daily_reset_not_triggered_same_day(self):
        """Test that daily stats don't reset on same day"""
        # Set some data
        self.agent.daily_pnl = -100.0
        self.agent.consecutive_losses = 1

        # Try to reset on same day
        self.agent._reset_daily_stats()

        # Should NOT reset
        self.assertEqual(self.agent.daily_pnl, -100.0)
        self.assertEqual(self.agent.consecutive_losses, 1)

    def test_circuit_breaker_clears_when_conditions_improve(self):
        """Test circuit breaker clears on new day after activation"""
        # Activate circuit breaker
        self.agent._update_daily_stats(-250.0)
        self.assertFalse(self.agent._check_circuit_breaker())
        self.assertTrue(self.agent.circuit_breaker_active)

        # Simulate new day
        self.agent.last_reset_date = (datetime.now() - timedelta(days=1)).date()

        # Check circuit breaker (should reset and clear)
        self.assertTrue(self.agent._check_circuit_breaker())
        self.assertFalse(self.agent.circuit_breaker_active)

    def test_mixed_wins_and_losses(self):
        """Test daily PnL with mixed wins and losses"""
        self.agent._update_daily_stats(100.0)   # Win
        self.agent._update_daily_stats(-30.0)   # Loss
        self.agent._update_daily_stats(50.0)    # Win
        self.agent._update_daily_stats(-20.0)   # Loss

        # Net PnL
        self.assertEqual(self.agent.daily_pnl, 100.0)

        # Consecutive losses should be 1 (last trade was loss)
        self.assertEqual(self.agent.consecutive_losses, 1)

        # Should still allow trading
        self.assertTrue(self.agent._check_circuit_breaker())

    def test_exact_daily_loss_limit(self):
        """Test behavior at exactly the daily loss limit"""
        self.agent.paper_engine.balance = 10000.0

        # Exactly 2% loss = $200
        self.agent._update_daily_stats(-200.0)

        # Should activate circuit breaker (>= limit)
        self.assertFalse(self.agent._check_circuit_breaker())
        self.assertTrue(self.agent.circuit_breaker_active)

    def test_one_less_than_max_consecutive_losses(self):
        """Test that circuit breaker doesn't activate at max-1 losses"""
        # Two consecutive losses (max is 3)
        self.agent._update_daily_stats(-30.0)
        self.agent._update_daily_stats(-40.0)

        # Should still allow trading
        self.assertTrue(self.agent._check_circuit_breaker())
        self.assertFalse(self.agent.circuit_breaker_active)


class TestPaperTradingEngine(unittest.TestCase):
    """Test paper trading engine PnL calculations"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = PaperTradingEngine(initial_balance=10000.0)

    def test_long_position_profit(self):
        """Test long position profit calculation"""
        analysis = {
            'symbol': 'BTCUSDT',
            'signal': 'LONG',
            'entry_price': 50000.0,
            'quantity': 0.1,
            'stop_loss': 49000.0,
            'take_profit': 51000.0,
            'strength': 80
        }

        position = self.engine.open_position(analysis)
        result = self.engine.close_position(position, 51000.0, 'TAKE_PROFIT')

        # Profit should be (51000 - 50000) * 0.1 = 100
        self.assertEqual(result['pnl'], 100.0)
        self.assertGreater(result['pnl_pct'], 0)
        self.assertEqual(self.engine.balance, 10100.0)

    def test_long_position_loss(self):
        """Test long position loss calculation"""
        analysis = {
            'symbol': 'BTCUSDT',
            'signal': 'LONG',
            'entry_price': 50000.0,
            'quantity': 0.1,
            'stop_loss': 49000.0,
            'take_profit': 51000.0,
            'strength': 80
        }

        position = self.engine.open_position(analysis)
        result = self.engine.close_position(position, 49000.0, 'STOP_LOSS')

        # Loss should be (49000 - 50000) * 0.1 = -100
        self.assertEqual(result['pnl'], -100.0)
        self.assertLess(result['pnl_pct'], 0)
        self.assertEqual(self.engine.balance, 9900.0)

    def test_short_position_profit(self):
        """Test short position profit calculation"""
        analysis = {
            'symbol': 'BTCUSDT',
            'signal': 'SHORT',
            'entry_price': 50000.0,
            'quantity': 0.1,
            'stop_loss': 51000.0,
            'take_profit': 49000.0,
            'strength': 80
        }

        position = self.engine.open_position(analysis)
        result = self.engine.close_position(position, 49000.0, 'TAKE_PROFIT')

        # Profit should be (50000 - 49000) * 0.1 = 100
        self.assertEqual(result['pnl'], 100.0)
        self.assertGreater(result['pnl_pct'], 0)
        self.assertEqual(self.engine.balance, 10100.0)

    def test_short_position_loss(self):
        """Test short position loss calculation"""
        analysis = {
            'symbol': 'BTCUSDT',
            'signal': 'SHORT',
            'entry_price': 50000.0,
            'quantity': 0.1,
            'stop_loss': 51000.0,
            'take_profit': 49000.0,
            'strength': 80
        }

        position = self.engine.open_position(analysis)
        result = self.engine.close_position(position, 51000.0, 'STOP_LOSS')

        # Loss should be (50000 - 51000) * 0.1 = -100
        self.assertEqual(result['pnl'], -100.0)
        self.assertLess(result['pnl_pct'], 0)
        self.assertEqual(self.engine.balance, 9900.0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
