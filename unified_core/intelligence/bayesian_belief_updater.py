import numpy as np

class BayesianBeliefUpdater:
    def __init__(self, prior_probabilities, likelihood_matrix):
        """
        Initialize the BayesianBeliefUpdater with prior probabilities and likelihood matrix.
        
        :param prior_probabilities: A dictionary mapping states to their prior probabilities.
        :param likelihood_matrix: A dictionary of dictionaries mapping states to outcomes and their likelihoods.
        """
        self.prior_probabilities = prior_probabilities
        self.likelihood_matrix = likelihood_matrix
        self.posterior_probabilities = prior_probabilities.copy()

    def update_beliefs(self, new_evidence):
        """
        Update beliefs based on new evidence.
        
        :param new_evidence: The observed outcome that serves as new evidence.
        """
        # Normalize the prior probabilities if they are not already normalized
        total_prior = sum(self.prior_probabilities.values())
        if total_prior != 1:
            self.prior_probabilities = {state: prob / total_prior for state, prob in self.prior_probabilities.items()}
        
        # Calculate the posterior probabilities
        for state in self.prior_probabilities.keys():
            likelihood = self.likelihood_matrix[state].get(new_evidence, 0)
            self.posterior_probabilities[state] = self.prior_probabilities[state] * likelihood
        
        # Normalize the posterior probabilities
        total_posterior = sum(self.posterior_probabilities.values())
        self.posterior_probabilities = {state: prob / total_posterior for state, prob in self.posterior_probabilities.items()}

    def get_current_beliefs(self):
        """
        Return the current posterior probabilities.
        
        :return: A dictionary mapping states to their updated posterior probabilities.
        """
        return self.posterior_probabilities

# Example usage
if __name__ == "__main__":
    prior_probabilities = {'bull': 0.6, 'bear': 0.4}
    likelihood_matrix = {
        'bull': {'up': 0.8, 'down': 0.2},
        'bear': {'up': 0.3, 'down': 0.7}
    }
    
    updater = BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)
    print("Initial beliefs:", updater.get_current_beliefs())
    
    # Simulate receiving new evidence
    new_evidence = 'up'
    updater.update_beliefs(new_evidence)
    print("Updated beliefs:", updater.get_current_beliefs())