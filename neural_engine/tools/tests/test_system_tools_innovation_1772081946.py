import pytest
from typing import Dict, Any

def search_prompts(keyword: str = "") -> Dict[str, Any]:
    """
    Search prompt library by keyword.
    
    Args:
        keyword: Search keyword
        
    Returns:
        Dict with matching prompts
    """
    if not keyword:
        return {"success": False, "error": "يجب تحديد كلمة البحث", "summary_ar": "لم يتم تحديد كلمة البحث"}
    
    try:
        from neural_engine.specialized_systems.library import prompt_library
        results = prompt_library.search(keyword)
        
        prompts_list = [{"name": p.name, "description": p.description, "category": p.category.value} for p in results]
        
        return {
            "success": True,
            "results": prompts_list,
            "count": len(prompts_list),
            "summary_ar": f"تم العثور على {len(prompts_list)} قالب للبحث عن: {keyword}"
        }
    except Exception as e:
        logger.error(f"Search prompts failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل البحث: {str(e)}"}

# Mock the prompt_library.search function for testing
from unittest.mock import patch

@patch('neural_engine.specialized_systems.library.prompt_library.search')
def test_search_prompts_happy_path(mock_search):
    # Arrange
    mock_search.return_value = [
        {'name': 'prompt1', 'description': 'desc1', 'category': 'cat1'},
        {'name': 'prompt2', 'description': 'desc2', 'category': 'cat2'}
    ]
    
    keyword = "search_term"
    
    # Act
    result = search_prompts(keyword)
    
    # Assert
    assert result == {
        "success": True,
        "results": [
            {"name": "prompt1", "description": "desc1", "category": "cat1"},
            {"name": "prompt2", "description": "desc2", "category": "cat2"}
        ],
        "count": 2,
        "summary_ar": "تم العثور على 2 قالب للبحث عن: search_term"
    }

@patch('neural_engine.specialized_systems.library.prompt_library.search')
def test_search_prompts_empty_keyword(mock_search):
    # Arrange
    keyword = ""
    
    # Act
    result = search_prompts(keyword)
    
    # Assert
    assert result == {
        "success": False,
        "error": "يجب تحديد كلمة البحث",
        "summary_ar": "لم يتم تحديد كلمة البحث"
    }

@patch('neural_engine.specialized_systems.library.prompt_library.search')
def test_search_prompts_no_results(mock_search):
    # Arrange
    mock_search.return_value = []
    
    keyword = "search_term"
    
    # Act
    result = search_prompts(keyword)
    
    # Assert
    assert result == {
        "success": True,
        "results": [],
        "count": 0,
        "summary_ar": "تم العثور على 0 قالب للبحث عن: search_term"
    }

@patch('neural_engine.specialized_systems.library.prompt_library.search')
def test_search_prompts_exception(mock_search):
    # Arrange
    mock_search.side_effect = Exception("Search error")
    
    keyword = "search_term"
    
    # Act
    result = search_prompts(keyword)
    
    # Assert
    assert result == {
        "success": False,
        "error": "Search error",
        "summary_ar": "فشل البحث: Search error"
    }