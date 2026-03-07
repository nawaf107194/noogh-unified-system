import pytest

from shared.batch_processing_utility import BatchProcessingUtility

def test_batch_processing_utility_happy_path():
    batch_size = 1000
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == batch_size

def test_batch_processing_utility_empty_input():
    batch_size = ""
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1000

def test_batch_processing_utility_none_input():
    batch_size = None
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1000

def test_batch_processing_utility_boundary_values():
    batch_size = 1
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1

    batch_size = 1000
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1000

def test_batch_processing_utility_invalid_input():
    batch_size = "abc"
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1000

    batch_size = -1
    utility = BatchProcessingUtility(batch_size)
    assert utility.batch_size == 1000