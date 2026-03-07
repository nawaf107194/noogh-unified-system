import pytest
import torch

class MockUnslothBCOTrainer:
    def __init__(self, min_density_ratio=0.1, max_density_ratio=1.0):
        self.args = type('Args', (), {'min_density_ratio': min_density_ratio, 'max_density_ratio': max_density_ratio})

    def _get_chosen_prob(self, rejected_embeddings):
        # Mock implementation for _get_chosen_prob
        return torch.rand_like(rejected_embeddings)

@pytest.fixture
def trainer():
    return MockUnslothBCOTrainer()

def test_get_udm_weight_happy_path(trainer):
    rejected_embeddings = torch.tensor([0.5, 0.3, 0.8])
    expected_output = (rejected_embeddings / (1 - rejected_embeddings + 1e-8)).clamp(min=trainer.args.min_density_ratio, max=trainer.args.max_density_ratio)
    output = trainer._get_udm_weight(rejected_embeddings)
    assert torch.allclose(output, expected_output)

def test_get_udm_weight_edge_case_empty_input(trainer):
    rejected_embeddings = torch.tensor([])
    output = trainer._get_udm_weight(rejected_embeddings)
    assert output is None or output.shape == ()

def test_get_udm_weight_edge_case_none_input(trainer):
    rejected_embeddings = None
    output = trainer._get_udm_weight(rejected_embeddings)
    assert output is None

def test_get_udm_weight_edge_case_boundary_min_ratio(trainer):
    trainer.args.min_density_ratio = 0.5
    rejected_embeddings = torch.tensor([1.0, 0.9])
    expected_output = (rejected_embeddings / (1 - rejected_embeddings + 1e-8)).clamp(min=trainer.args.min_density_ratio, max=trainer.args.max_density_ratio)
    output = trainer._get_udm_weight(rejected_embeddings)
    assert torch.allclose(output, expected_output)

def test_get_udm_weight_edge_case_boundary_max_ratio(trainer):
    trainer.args.max_density_ratio = 0.9
    rejected_embeddings = torch.tensor([0.1, 0.2])
    expected_output = (rejected_embeddings / (1 - rejected_embeddings + 1e-8)).clamp(min=trainer.args.min_density_ratio, max=trainer.args.max_density_ratio)
    output = trainer._get_udm_weight(rejected_embeddings)
    assert torch.allclose(output, expected_output)

def test_get_udm_weight_error_case_invalid_input(trainer):
    with pytest.raises(TypeError):
        trainer._get_udm_weight("not a tensor")