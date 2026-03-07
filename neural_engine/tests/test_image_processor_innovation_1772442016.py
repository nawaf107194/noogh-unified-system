import pytest
from unittest.mock import patch, MagicMock
from neural_engine.image_processor import image_processor
from PIL import Image
import torch

@pytest.fixture
def processor():
    return image_processor()

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
@patch("torch.no_grad")
def test_search_by_text_happy_path(mock_no_grad, mock_ensure, processor):
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    query = "cat"
    top_k = 2
    expected_results = [
        {"path": "path/to/image1.jpg", "score": 0.9},
        {"path": "path/to/image2.jpg", "score": 0.8}
    ]
    
    # Mock the model output
    mock_clip_model = MagicMock()
    mock_clip_model.logits_per_text = torch.tensor([[0.9, 0.8]])
    mock_no_grad.return_value.__enter__.return_value = mock_clip_model
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == expected_results

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
@patch("torch.no_grad")
def test_search_by_text_empty_query(mock_no_grad, mock_ensure, processor):
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    query = ""
    top_k = 2
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == []

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
@patch("torch.no_grad")
def test_search_by_text_none_query(mock_no_grad, mock_ensure, processor):
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    query = None
    top_k = 2
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == []

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
def test_search_by_text_empty_image_paths(mock_ensure, processor):
    image_paths = []
    query = "cat"
    top_k = 2
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == []

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
def test_search_by_text_none_image_paths(mock_ensure, processor):
    image_paths = None
    query = "cat"
    top_k = 2
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == []

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
@patch("torch.no_grad")
def test_search_by_text_invalid_query_type(mock_no_grad, mock_ensure, processor):
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    query = 123
    top_k = 2
    
    results = processor.search_by_text(image_paths, query, top_k)
    
    assert results == []

@patch("neural_engine.image_processor.image_processor._ensure_models_loaded")
def test_search_by_text_clip_model_error(mock_ensure, processor):
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    query = "cat"
    top_k = 2
    
    with patch("neural_engine.image_processor.image_processor.clip_model") as mock_clip_model:
        mock_clip_model.side_effect = Exception("Error in CLIP model")
        
        results = processor.search_by_text(image_paths, query, top_k)
        
        assert results == []