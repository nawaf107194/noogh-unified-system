import pytest
from typing import Dict, Optional
from unified_core.evolution.evolution_dreamer import EvolutionDreamer, EvolutionDream

def test_happy_path():
    dreamer = EvolutionDreamer()
    response = "TITLE: Improve User Interface\nTYPE: Optimization\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: 0.9"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is not None
    assert result.title == "Improve User Interface"
    assert result.dream_type == "optimization"
    assert result.goal_alignment == True
    assert result.confidence == 0.9

def test_edge_case_empty_response():
    dreamer = EvolutionDreamer()
    response = ""
    context = {}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is None

def test_edge_case_none_response():
    dreamer = EvolutionDreamer()
    response = None
    context = {}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is None

def test_edge_case_missing_title():
    dreamer = EvolutionDreamer()
    response = "TYPE: Optimization\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: 0.9"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is None

def test_edge_case_boundary_confidence():
    dreamer = EvolutionDreamer()
    response = "TITLE: Improve User Interface\nTYPE: Optimization\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: 0.95"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is not None
    assert result.confidence == 0.95

def test_error_case_invalid_confidence():
    dreamer = EvolutionDreamer()
    response = "TITLE: Improve User Interface\nTYPE: Optimization\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: invalid"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is not None
    assert result.confidence == 0.5

def test_edge_case_lowercase_type():
    dreamer = EvolutionDreamer()
    response = "TITLE: Improve User Interface\nTYPE: optimization\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: 0.9"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is not None
    assert result.dream_type == "optimization"

def test_edge_case_unrecognized_type():
    dreamer = EvolutionDreamer()
    response = "TITLE: Improve User Interface\nTYPE: Experiment\nTARGET: Home Page\nDESCRIPTION: Increase user satisfaction by streamlining the interface.\nRATIONALE: Simplified design leads to better user experience.\nCONFIDENCE: 0.9"
    context = {"active_goals": ["User Experience", "Simplicity"]}
    
    result = dreamer._parse_dream(response, context)
    
    assert result is not None
    assert result.dream_type == "optimization"