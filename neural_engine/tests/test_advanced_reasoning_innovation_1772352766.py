import pytest

from neural_engine.advanced_reasoning import _detect_causal_relation, CausalRelation

@pytest.mark.parametrize("event1, event2, expected", [
    (
        {"action": "upload file", "success": True},
        {"action": "save file based on upload", "success": True},
        CausalRelation(
            cause="upload file",
            effect="save file based on upload",
            confidence=0.8,
            evidence=["Temporal proximity", "Logical dependency detected", "Both actions successful"],
            correlation_strength=0.7
        )
    ),
    (
        {"action": "delete file", "success": False},
        {"action": "backup file from deleted one", "success": False},
        CausalRelation(
            cause="delete file",
            effect="backup file from deleted one",
            confidence=0.65,
            evidence=["Temporal proximity", "Both actions failed (possible causal chain)"],
            correlation_strength=0.3
        )
    ),
    (
        {"action": "read document", "success": True},
        {"action": "highlight text in read document", "success": False},
        CausalRelation(
            cause="read document",
            effect="highlight text in read document",
            confidence=0.6,
            evidence=["Temporal proximity"],
            correlation_strength=0.3
        )
    ),
    (
        {"action": "", "success": True},
        {"action": "save file based on upload", "success": True},
        None
    ),
    (
        {"action": "upload file", "success": None},
        {"action": "save file based on upload", "success": True},
        None
    ),
    (
        None,
        {"action": "save file based on upload", "success": True},
        None
    ),
    (
        {"action": "upload file", "success": True},
        None,
        None
    )
])
def test_detect_causal_relation(event1, event2, expected):
    result = _detect_causal_relation(event1, event2)
    assert result == expected

@pytest.mark.parametrize("event1, event2", [
    ({"action": 123, "success": True}, {"action": "save file based on upload", "success": True}),
    ({"action": "upload file", "success": "True"}, {"action": "save file based on upload", "success": True})
])
def test_detect_causal_relation_invalid_inputs(event1, event2):
    result = _detect_causal_relation(event1, event2)
    assert result is None