import pytest

def test_create_completion_message_happy_path():
    assert create_completion_message("translate") == "✅ تم translate بنجاح"
    assert create_completion_message("summarize", False) == "❌ فشل summarize"

def test_create_completion_message_edge_cases():
    assert create_completion_message("") == "✅ تم  بنجاح"
    assert create_completion_message(None) == "✅ تم  بنجاح"
    assert create_completion_message("unknown_tool") == "✅ تم unknown_tool بنجاح"

def test_create_completion_message_error_cases():
    with pytest.raises(TypeError):
        create_completion_message(123)