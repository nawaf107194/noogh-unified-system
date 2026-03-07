from typing import List, Dict
import numpy as np

class AdversarialThinkingModule:
    def __init__(self, risk_factors: List[str], impact_matrix: Dict[str, float]):
        """
        Initializes the AdversarialThinkingModule with a list of risk factors and their impact on the trade.
        
        :param risk_factors: List of risk factors that could affect the trade.
        :param impact_matrix: Dictionary mapping each risk factor to its impact score.
        """
        self.risk_factors = risk_factors
        self.impact_matrix = impact_matrix
        
    def assess_risks(self, trade_info: Dict) -> float:
        """
        Assesses the risks associated with a given trade by evaluating the impact of each risk factor.
        
        :param trade_info: Dictionary containing information about the trade, including potential risk factors.
        :return: A risk score indicating the overall risk level of the trade.
        """
        risk_score = 0.0
        for factor in self.risk_factors:
            if factor in trade_info:
                risk_score += self.impact_matrix.get(factor, 0.0) * trade_info[factor]
        return risk_score
    
    def evaluate_trade(self, trade_info: Dict) -> bool:
        """
        Evaluates whether the trade should be executed based on the assessed risk score.
        
        :param trade_info: Dictionary containing information about the trade, including potential risk factors.
        :return: True if the trade should be executed, False otherwise.
        """
        risk_score = self.assess_risks(trade_info)
        # Example threshold logic; this can be adjusted based on specific requirements
        if risk_score > 0.5:
            print(f"Trade rejected due to high risk ({risk_score}).")
            return False
        else:
            print(f"Trade approved with acceptable risk ({risk_score}).")
            return True

# Example usage
if __name__ == "__main__":
    risk_factors = ['economic_news', 'market_volatility', 'unexpected_events']
    impact_matrix = {'economic_news': 0.2, 'market_volatility': 0.3, 'unexpected_events': 0.5}
    
    module = AdversarialThinkingModule(risk_factors, impact_matrix)
    
    trade_info = {
        'economic_news': 0.4,
        'market_volatility': 0.6,
        'unexpected_events': 0.1,
    }
    
    should_execute = module.evaluate_trade(trade_info)
    print(f"Should execute trade: {should_execute}")