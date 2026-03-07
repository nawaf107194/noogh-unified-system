import pytest
import numpy as np

class TestVolatilityAdjustedPositionSizing:

    class MockVolumeAdjuster:
        min_leverage = 1.0
        max_leverage = 5.0

        @staticmethod
        def adjust_position_size(volatility, current_price, max_expected_volatility=50.0):
            """
            Adjust the position size based on the calculated volatility.
            :param volatility: The calculated volatility.
            :param current_price: Current market price.
            :param max_expected_volatility: Assumed maximum volatility for normalization.
            :return: Adjusted leverage and position size.
            """
            # Normalize volatility to a range between min and max leverage
            # Higher volatility should lead to lower leverage (safer)
            normalized_volatility = np.interp(volatility, [0, max_expected_volatility], [1.0, 5.0])
            adjusted_leverage = np.clip(normalized_volatility, 1.0, 5.0)
            
            # Calculate position size based on adjusted leverage
            position_size = current_price * adjusted_leverage
            
            return adjusted_leverage, position_size

    @pytest.fixture
    def mock_adjuster(self):
        return self.MockVolumeAdjuster()

    def test_happy_path(self, mock_adjuster):
        volatility = 25.0
        current_price = 100.0
        max_expected_volatility = 50.0
        expected_leverage = 3.0
        expected_position_size = 300.0

        result = mock_adjuster.adjust_position_size(volatility, current_price, max_expected_volatility)
        
        assert result == (expected_leverage, expected_position_size)

    def test_edge_case_max_volatility(self, mock_adjuster):
        volatility = 50.0
        current_price = 100.0
        max_expected_volatility = 50.0
        expected_leverage = 1.0
        expected_position_size = 100.0

        result = mock_adjuster.adjust_position_size(volatility, current_price, max_expected_volatility)
        
        assert result == (expected_leverage, expected_position_size)

    def test_edge_case_min_volatility(self, mock_adjuster):
        volatility = 0.0
        current_price = 100.0
        max_expected_volatility = 50.0
        expected_leverage = 5.0
        expected_position_size = 500.0

        result = mock_adjuster.adjust_position_size(volatility, current_price, max_expected_volatility)
        
        assert result == (expected_leverage, expected_position_size)

    def test_boundary_max_leverage(self, mock_adjuster):
        volatility = 75.0
        current_price = 100.0
        max_expected_volatility = 50.0
        expected_leverage = 5.0
        expected_position_size = 500.0

        result = mock_adjuster.adjust_position_size(volatility, current_price, max_expected_volatility)
        
        assert result == (expected_leverage, expected_position_size)

    def test_boundary_min_leverage(self, mock_adjuster):
        volatility = -25.0
        current_price = 100.0
        max_expected_volatility = 50.0
        expected_leverage = 1.0
        expected_position_size = 100.0

        result = mock_adjuster.adjust_position_size(volatility, current_price, max_expected_volatility)
        
        assert result == (expected_leverage, expected_position_size)

    def test_invalid_inputs(self, mock_adjuster):
        with pytest.raises(ValueError):
            mock_adjuster.adjust_position_size(-10.0, 100.0, 50.0)
    
        with pytest.raises(ValueError):
            mock_adjuster.adjust_position_size(60.0, 100.0, 50.0)

        with pytest.raises(TypeError):
            mock_adjuster.adjust_position_size('a', 'b', 50.0)

        with pytest.raises(TypeError):
            mock_adjuster.adjust_position_size(None, None, None)
        
        with pytest.raises(ValueError):
            mock_adjuster.adjust_position_size(25.0, -100.0, 50.0)