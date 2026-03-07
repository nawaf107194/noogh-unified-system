import pytest
from pathlib import Path
from agents.continuous_training_loop import ContinuousTrainingLoop

class MockBrain:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model

class MockNeuronTester:
    pass

def test_init_happy_path():
    ctl = ContinuousTrainingLoop()
    assert isinstance(ctl.brain, RunPodBrain)
    assert ctl.brain.base_url == 'https://6gylw7ox0y2qzd-8000.proxy.runpod.net'
    assert ctl.brain.model == 'noogh-teacher'
    assert isinstance(ctl.neuron_tester, NeuronTester)
    assert ctl.paper_trader is None
    assert ctl.data_file == Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
    assert ctl.paper_trades_file == Path('/home/noogh/projects/noogh_unified_system/src/data/paper_trades_with_neurons.jsonl')
    assert ctl.training_log == Path('/home/noogh/projects/noogh_unified_system/src/data/training_log.jsonl')

def test_init_empty_data_files():
    ctl = ContinuousTrainingLoop(data_file='', paper_trades_file='', training_log='')
    assert isinstance(ctl.brain, RunPodBrain)
    assert ctl.brain.base_url == 'https://6gylw7ox0y2qzd-8000.proxy.runpod.net'
    assert ctl.brain.model == 'noogh-teacher'
    assert isinstance(ctl.neuron_tester, NeuronTester)
    assert ctl.paper_trader is None
    assert ctl.data_file == Path('')
    assert ctl.paper_trades_file == Path('')
    assert ctl.training_log == Path('')

def test_init_none_data_files():
    ctl = ContinuousTrainingLoop(data_file=None, paper_trades_file=None, training_log=None)
    assert isinstance(ctl.brain, RunPodBrain)
    assert ctl.brain.base_url == 'https://6gylw7ox0y2qzd-8000.proxy.runpod.net'
    assert ctl.brain.model == 'noogh-teacher'
    assert isinstance(ctl.neuron_tester, NeuronTester)
    assert ctl.paper_trader is None
    assert ctl.data_file is None
    assert ctl.paper_trades_file is None
    assert ctl.training_log is None

def test_init_invalid_data_files():
    with pytest.raises(TypeError):
        ContinuousTrainingLoop(data_file=123, paper_trades_file=True, training_log={})