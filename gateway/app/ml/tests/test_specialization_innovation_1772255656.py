import pytest
from gateway.app.ml.specialization import Specialization

class MockDistillationService:
    def __init__(self, secrets):
        pass

class MockDatasetExpander:
    def __init__(self):
        pass

class MockCrossDomainEvaluator:
    def __init__(self):
        pass

class MockHFDataManager:
    def __init__(self):
        pass

class MockDataAdapter:
    def __init__(self):
        pass

@pytest.fixture
def specialization():
    return Specialization

@pytest.fixture
def mock_distillation_service(mocker):
    return mocker.patch('gateway.app.ml.specialization.DistillationService', new=MockDistillationService)

@pytest.fixture
def mock_dataset_expander(mocker):
    return mocker.patch('gateway.app.ml.specialization.DatasetExpander', new=MockDatasetExpander)

@pytest.fixture
def mock_cross_domain_evaluator(mocker):
    return mocker.patch('gateway.app.ml.specialization.CrossDomainEvaluator', new=MockCrossDomainEvaluator)

@pytest.fixture
def mock_hf_data_manager(mocker):
    return mocker.patch('gateway.app.ml.specialization.HFDataManager', new=MockHFDataManager)

@pytest.fixture
def mock_data_adapter(mocker):
    return mocker.patch('gateway.app.ml.specialization.DataAdapter', new=MockDataAdapter)

def test_init_with_normal_inputs(specialization, mock_distillation_service, mock_dataset_expander, mock_cross_domain_evaluator, mock_hf_data_manager, mock_data_adapter):
    secrets = {'key': 'value'}
    instance = specialization(secrets)
    assert instance.secrets == secrets
    assert isinstance(instance.distiller, MockDistillationService)
    assert isinstance(instance.expander, MockDatasetExpander)
    assert isinstance(instance.cross_evaluator, MockCrossDomainEvaluator)
    assert isinstance(instance.data_manager, MockHFDataManager)
    assert isinstance(instance.adapter, MockDataAdapter)
    assert instance.active_tasks == {}

def test_init_with_empty_secrets(specialization, mock_distillation_service, mock_dataset_expander, mock_cross_domain_evaluator, mock_hf_data_manager, mock_data_adapter):
    secrets = {}
    instance = specialization(secrets)
    assert instance.secrets == {}
    assert isinstance(instance.distiller, MockDistillationService)
    assert isinstance(instance.expander, MockDatasetExpander)
    assert isinstance(instance.cross_evaluator, MockCrossDomainEvaluator)
    assert isinstance(instance.data_manager, MockHFDataManager)
    assert isinstance(instance.adapter, MockDataAdapter)
    assert instance.active_tasks == {}

def test_init_with_none_secrets(specialization, mock_distillation_service, mock_dataset_expander, mock_cross_domain_evaluator, mock_hf_data_manager, mock_data_adapter):
    secrets = None
    instance = specialization(secrets)
    assert instance.secrets == {}
    assert isinstance(instance.distiller, MockDistillationService)
    assert isinstance(instance.expander, MockDatasetExpander)
    assert isinstance(instance.cross_evaluator, MockCrossDomainEvaluator)
    assert isinstance(instance.data_manager, MockHFDataManager)
    assert isinstance(instance.adapter, MockDataAdapter)
    assert instance.active_tasks == {}

def test_init_with_invalid_secrets(specialization, mock_distillation_service, mock_dataset_expander, mock_cross_domain_evaluator, mock_hf_data_manager, mock_data_adapter):
    secrets = 'not a dictionary'
    with pytest.raises(TypeError) as e:
        specialization(secrets)
    assert str(e.value) == "secrets must be a dictionary"