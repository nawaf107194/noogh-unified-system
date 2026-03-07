import pytest
from shared.batch_processing_utility import BatchProcessingUtility

def mock_processor_function(batch):
    return batch * 2

@pytest.fixture
def utility():
    return BatchProcessingUtility(batch_size=10)

def test_happy_path(utility, tmpdir):
    file_path = str(tmpdir.join("test_data.csv"))
    data = "col1,col2\n1,2\n3,4\n5,6"
    with open(file_path, 'w') as f:
        f.write(data)
    
    result_batches = []
    def processor_function(batch):
        result_batches.append(processor_function(batch))
    
    utility.process_batches(file_path, processor_function)
    
    assert len(result_batches) == 3
    for i in range(3):
        assert result_batches[i] == [[1, 2], [3, 4], [5, 6]]

def test_edge_case_empty_file(utility, tmpdir):
    file_path = str(tmpdir.join("test_data.csv"))
    with open(file_path, 'w') as f:
        pass
    
    with pytest.raises(FileNotFoundError) as exc_info:
        utility.process_batches(file_path, mock_processor_function)
    
    assert "The file" in str(exc_info.value)

def test_edge_case_none_file_path(utility):
    with pytest.raises(TypeError) as exc_info:
        utility.process_batches(None, mock_processor_function)
    
    assert "file_path" in str(exc_info.value)

def test_async_behavior(utility, tmpdir):
    import asyncio
    
    async def async_mock_processor_function(batch):
        return asyncio.sleep(0.1)
    
    file_path = str(tmpdir.join("test_data.csv"))
    data = "col1,col2\n1,2\n3,4\n5,6"
    with open(file_path, 'w') as f:
        f.write(data)
    
    async def main():
        utility.process_batches(file_path, async_mock_processor_function)
    
    asyncio.run(main())