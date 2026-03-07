import pandas as pd
from bayes_python.bayesian_inference import BayesianInference

class BayesianAdversarialUpdater:
    def __init__(self):
        self.belief_updater = BayesianInference()

    def update_beliefs(self, current_state, actions, likelihoods):
        """
        Update the agent's beliefs about the likelihood of each action based on the current state.
        
        :param current_state: Current state of the environment
        :param actions: List of possible actions to take
        :param likelihoods: Dictionary mapping actions to their likelihood of success or failure given the current state
        """
        for action, likelihood in likelihoods.items():
            self.belief_updater.update(action, likelihood)

    def get_best_action(self):
        """
        Get the action with the highest updated belief.
        
        :return: The best action based on updated beliefs
        """
        return self.belief_updater.get_most_likely_action()

if __name__ == '__main__':
    # Example usage
    updater = BayesianAdversarialUpdater()
    
    current_state = "Market is bullish"
    actions = ["Buy", "Sell", "Hold"]
    likelihoods = {
        "Buy": 0.7,
        "Sell": 0.2,
        "Hold": 0.1
    }
    
    updater.update_beliefs(current_state, actions, likelihoods)
    best_action = updater.get_best_action()
    print(f"The most likely action given the current state is: {best_action}")