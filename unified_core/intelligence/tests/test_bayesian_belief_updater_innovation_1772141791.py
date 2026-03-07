import pytest

from unified_core.intelligence.bayesian_belief_updater import BayesianBeliefUpdater

def test_init_happy_path():
    prior_probabilities = {'A': 0.5, 'B': 0.5}
    likelihood_matrix = {
        'A': {'X': 0.2, 'Y': 0.8},
        'B': {'X': 0.7, 'Y': 0.3}
    }
    
    updater = BayesianBeliefUpdater(prior_probabilities, likelihood_matrix)
    
    assert updater.prior_probabilities == prior_probabilities
    assert updater.likelihood_matrix == likelihood_matrix
    assert updater.posterior_probabilities == prior_probabilities

def test_init_empty_prior_probabilities():
    prior_probabilities = {}
    with pytest.raises(ValueError) as exc_info:
        BayesianBeliefUpdater(prior_probabilities, {})
    
    assert "Prior probabilities must not be empty" in str(exc_info.value)

def test_init_none_prior_probabilities():
    with pytest.raises(TypeError) as exc_info:
        BayesianBeliefUpdater(None, {})

def test_init_invalid_priors_sum():
    prior_probabilities = {'A': 0.6, 'B': 0.4}
    with pytest.raises(ValueError) as exc_info:
        BayesianBeliefUpdater(prior_probabilities, {})
    
    assert "Prior probabilities must sum to 1" in str(exc_info.value)

def test_init_empty_likelihood_matrix():
    likelihood_matrix = {}
    with pytest.raises(ValueError) as exc_info:
        BayesianBeliefUpdater({'A': 0.5}, likelihood_matrix)
    
    assert "Likelihood matrix must not be empty" in str(exc_info.value)

def test_init_none_likelihood_matrix():
    with pytest.raises(TypeError) as exc_info:
        BayesianBeliefUpdater({'A': 0.5}, None)