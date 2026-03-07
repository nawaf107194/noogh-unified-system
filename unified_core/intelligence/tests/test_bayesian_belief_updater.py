import pytest

from unified_core.intelligence.bayesian_belief_updater import BayesianBeliefUpdater

def test_happy_path():
    prior_probabilities = {'A': 0.3, 'B': 0.7}
    likelihood_matrix = {
        'A': {'X': 0.2, 'Y': 0.8},
        'B': {'X': 0.6, 'Y': 0.4}
    }
    updater = BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)
    assert updater.prior_probabilities == prior_probabilities
    assert updater.likelihood_matrix == likelihood_matrix
    assert updater.posterior_probabilities == prior_probabilities

def test_edge_case_empty_inputs():
    prior_probabilities = {}
    likelihood_matrix = {}
    updater = BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)
    assert updater.prior_probabilities == prior_probabilities
    assert updater.likelihood_matrix == likelihood_matrix
    assert updater.posterior_probabilities == prior_probabilities

def test_edge_case_none_inputs():
    with pytest.raises(TypeError):
        BayesianBeliefUpdater(None, None)

def test_error_case_invalid_prior_probabilities():
    prior_probabilities = {'A': 0.6, 'B': 0.4}  # Sum should be 1
    likelihood_matrix = {
        'A': {'X': 0.2, 'Y': 0.8},
        'B': {'X': 0.6, 'Y': 0.4}
    }
    with pytest.raises(ValueError):
        BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)

def test_error_case_invalid_likelihood_matrix():
    prior_probabilities = {'A': 0.3, 'B': 0.7}
    likelihood_matrix = {
        'A': {'X': 0.2},  # Missing outcome Y
        'B': {'X': 0.6, 'Y': 0.4}
    }
    with pytest.raises(ValueError):
        BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)