import pytest

from gateway.app.console.intent_classifier import classify_intent_deterministic, EXACT_PHRASES, INTENT_RULES, DEFAULT_MODE, DEFAULT_CONFIDENCE

@pytest.mark.parametrize("query, expected", [
    ("Turn on the lights", {
        "mode": "LIGHTS_ON",
        "confidence": 1.0,
        "summary": "exact phrase: turn on the lights",
        "matched_keyword": "turn on the lights",
        "priority": 200
    }),
    ("Set the temperature to 72 degrees", {
        "mode": "TEMPERATURE_SET",
        "confidence": 1.0,
        "summary": "exact phrase: set temperature to 72 degrees",
        "matched_keyword": "set temperature to 72 degrees",
        "priority": 200
    }),
    ("Query current weather", {
        "mode": "WEATHER_QUERY",
        "confidence": 1.0,
        "summary": "exact phrase: query current weather",
        "matched_keyword": "query current weather",
        "priority": 200
    }),
])
def test_exact_phrase_matches(query, expected):
    result = classify_intent_deterministic(query)
    assert result == expected

@pytest.mark.parametrize("query, expected", [
    ("Increase the volume", {
        "mode": "VOLUME_INCREASE",
        "confidence": 1.0,
        "summary": "matched 'increase' (priority=150)",
        "matched_keyword": "increase",
        "priority": 150
    }),
    ("Play some music", {
        "mode": "MUSIC_PLAY",
        "confidence": 1.0,
        "summary": "matched 'play' (priority=120)",
        "matched_keyword": "play",
        "priority": 120
    }),
])
def test_rule_based_matching(query, expected):
    result = classify_intent_deterministic(query)
    assert result == expected

@pytest.mark.parametrize("query, expected", [
    ("", {
        "mode": DEFAULT_MODE,
        "confidence": DEFAULT_CONFIDENCE,
        "summary": "no keywords matched, using default",
        "matched_keyword": None,
        "priority": 0
    }),
    (None, {
        "mode": DEFAULT_MODE,
        "confidence": DEFAULT_CONFIDENCE,
        "summary": "no keywords matched, using default",
        "matched_keyword": None,
        "priority": 0
    }),
])
def test_edge_cases(query, expected):
    result = classify_intent_deterministic(query)
    assert result == expected

@pytest.mark.parametrize("query", [
    "Invalid input!@#",
    "1234567890",
    "No match found here"
])
def test_error_handling(query):
    result = classify_intent_deterministic(query)
    assert result is None or "no keywords matched" in result.get("summary", "")

@pytest.mark.parametrize("query, expected", [
    ("Turn on the lights", {
        "mode": "LIGHTS_ON",
        "confidence": 1.0,
        "summary": "exact phrase: turn on the lights",
        "matched_keyword": "turn on the lights",
        "priority": 200
    }),
])
async def test_async_behavior(query, expected):
    # Since classify_intent_deterministic is synchronous, this will not actually be async behavior.
    # However, if we hypothetically had an async version, it would be tested similarly.
    result = classify_intent_deterministic(query)
    assert result == expected