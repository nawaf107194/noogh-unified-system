import pytest

class TestHedgingMechanismModule:

    def test_apply_hedging_happy_path(self):
        # Setup
        trade_details = {
            'position_size': 100,
            'risk_assessment_score': 70
        }
        
        expected_hedge_position_size = 30
        expected_result = {
            'position_size': 100,
            'hedged_position_size': expected_hedge_position_size,
            'risk_assessment_score': 70
        }
        
        # Execute
        hedging_module = HedgingMechanismModule()
        result = hedging_module.apply_hedging(trade_details)
        
        # Assert
        assert result == expected_result

    def test_apply_hedging_edge_case_empty_trade_details(self):
        # Setup
        trade_details = {}
        
        expected_result = None
        
        # Execute
        hedging_module = HedgingMechanismModule()
        with pytest.raises(ValueError):
            result = hedging_module.apply_hedging(trade_details)
        
    def test_apply_hedging_edge_case_none_trade_details(self):
        # Setup
        trade_details = None
        
        expected_result = None
        
        # Execute
        hedging_module = HedgingMechanismModule()
        with pytest.raises(ValueError):
            result = hedging_module.apply_hedging(trade_details)
        
    def test_apply_hedging_edge_case_boundary_risk_assessment(self):
        # Setup
        trade_details = {
            'position_size': 100,
            'risk_assessment_score': 50
        }
        
        expected_hedge_position_size = 30
        expected_result = {
            'position_size': 100,
            'hedged_position_size': expected_hedge_position_size,
            'risk_assessment_score': 50
        }
        
        # Execute
        hedging_module = HedgingMechanismModule()
        result = hedging_module.apply_hedging(trade_details)
        
        # Assert
        assert result == expected_result

    def test_apply_hedging_error_case_invalid_position_size(self):
        # Setup
        trade_details = {
            'position_size': None,
            'risk_assessment_score': 70
        }
        
        expected_result = None
        
        # Execute
        hedging_module = HedgingMechanismModule()
        with pytest.raises(ValueError):
            result = hedging_module.apply_hedging(trade_details)

    def test_apply_hedging_error_case_invalid_risk_assessment(self):
        # Setup
        trade_details = {
            'position_size': 100,
            'risk_assessment_score': None
        }
        
        expected_result = None
        
        # Execute
        hedging_module = HedgingMechanismModule()
        with pytest.raises(ValueError):
            result = hedging_module.apply_hedging(trade_details)

class HedgingMechanismModule:
    def calculate_hedge_position(self, current_position_size, risk_assessment_score):
        if current_position_size is None or risk_assessment_score is None:
            raise ValueError("Invalid input")
        
        return int(current_position_size * (risk_assessment_score / 100))

    def apply_hedging(self, trade_details):
        """
        Apply hedging based on risk assessment and trade details.
        
        :param trade_details: Dictionary containing trade information including position size and risk score
        :return: Updated trade details with potential hedge positions added
        """
        current_position_size = trade_details.get('position_size')
        risk_assessment_score = trade_details.get('risk_assessment_score', 50)
        
        # Calculate the hedge position size
        hedge_position_size = self.calculate_hedge_position(current_position_size, risk_assessment_score)
        
        # Apply hedging
        updated_trade_details = {
            'position_size': current_position_size,
            'hedged_position_size': hedge_position_size,
            **trade_details  # Keep other details intact
        }
        
        return updated_trade_details