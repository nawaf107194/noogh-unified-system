# unified_core/intelligence/bayesian_belief_updater.py

import numpy as np
from scipy.stats import beta

class BayesianBeliefUpdater:
    """
    Updates agent's beliefs based on new evidence using Bayesian inference.
    This class maintains prior beliefs and updates them with new data to form posterior beliefs.
    """

    def __init__(self, alpha=1, beta=1):
        """
        Initialize the BayesianBeliefUpdater with a uniform prior by default.

        :param alpha: alpha parameter of the Beta distribution (default is 1)
        :param beta: beta parameter of the Beta distribution (default is 1)
        """
        self.prior_alpha = alpha
        self.prior_beta = beta

    def update_belief(self, evidence):
        """
        Update beliefs based on new evidence.

        :param evidence: A list of binary outcomes (0 or 1) representing new data.
        :return: The updated alpha and beta parameters of the Beta distribution.
        """
        successes = sum(evidence)
        failures = len(evidence) - successes

        # Update the posterior
        posterior_alpha = self.prior_alpha + successes
        posterior_beta = self.prior_beta + failures

        return posterior_alpha, posterior_beta

    def get_posterior_mean(self, alpha, beta):
        """
        Calculate the mean of the posterior Beta distribution.

        :param alpha: The updated alpha parameter.
        :param beta: The updated beta parameter.
        :return: The mean of the posterior distribution.
        """
        return alpha / (alpha + beta)

    def get_confidence_interval(self, alpha, beta, confidence=0.95):
        """
        Calculate the credible interval for the posterior Beta distribution.

        :param alpha: The updated alpha parameter.
        :param beta: The updated beta parameter.
        :param confidence: The desired confidence level (default is 0.95).
        :return: A tuple representing the lower and upper bounds of the credible interval.
        """
        low_bound = beta.ppf((1 - confidence) / 2, alpha, beta)
        high_bound = beta.ppf((1 + confidence) / 2, alpha, beta)
        return low_bound, high_bound

# Example usage
if __name__ == '__main__':
    # Initialize the belief updater with a uniform prior
    updater = BayesianBeliefUpdater()

    # Simulate receiving new evidence (e.g., outcomes of trials)
    new_evidence = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0]

    # Update beliefs based on the new evidence
    posterior_alpha, posterior_beta = updater.update_belief(new_evidence)

    # Calculate the mean of the updated belief distribution
    posterior_mean = updater.get_posterior_mean(posterior_alpha, posterior_beta)
    print(f"Posterior Mean: {posterior_mean}")

    # Calculate the 95% confidence interval for the updated belief
    credible_interval = updater.get_confidence_interval(posterior_alpha, posterior_beta)
    print(f"95% Credible Interval: {credible_interval}")