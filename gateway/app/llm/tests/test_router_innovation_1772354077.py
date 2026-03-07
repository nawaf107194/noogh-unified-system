import pytest

from gateway.app.llm.router import _needs_cloud_capabilities

def test_needs_cloud_capabilities_happy_path():
    assert _needs_cloud_capabilities("What is the latest news?") == True
    assert _needs_cloud_capabilities("I want to search web for information.") == True
    assert _needs_cloud_capabilities("Current events are happening now.") == True
    assert _needs_cloud_capabilities("Check the weather forecast.") == True

def test_needs_cloud_capabilities_empty_string():
    assert _needs_cloud_capabilities("") == False

def test_needs_cloud_capabilities_none_input():
    assert _needs_cloud_capabilities(None) == False

def test_needs_cloud_capabilities_boundary_keyword():
    assert _needs_cloud_capabilities("latest news") == True
    assert _needs_cloud_capabilities("search web") == True
    assert _needs_cloud_capabilities("current events") == True
    assert _needs_cloud_capabilities("weather") == True

def test_needs_cloud_capabilities_case_insensitivity():
    assert _needs_cloud_capabilities("LATEST NEWS") == True
    assert _needs_cloud_capabilities("Search Web") == True
    assert _needs_cloud_capabilities("CURRENT EVENTS") == True
    assert _needs_cloud_capabilities("Weather") == True

def test_needs_cloud_capabilities_no_keywords():
    assert _needs_cloud_capabilities("I need to go shopping.") == False