import pytest
from unittest.mock import patch

# Assuming _SAFE_IDENTIFIER is defined in the same module as a regex pattern
from re import compile as re_compile

# Mocking _SAFE_IDENTIFIER for testing purposes
_SAFE_IDENTIFIER = re_compile(r'^[a-zA-Z0-9_]+$')

@pytest.fixture(autouse=True)
def mock_safe_identifier():
    with patch('unified_core.db.graph_db._SAFE_IDENTIFIER', _SAFE_IDENTIFIER):
        yield

def test_sanitize_label_happy_path():
    assert _sanitize_label("ValidLabel") == "ValidLabel"
    assert _sanitize_label("Another_Valid_Label123") == "Another_Valid_Label123"

def test_sanitize_label_edge_cases():
    assert _sanitize_label("_") == "_"
    assert _sanitize_label("A") == "A"
    assert _sanitize_label("a_b_c_d_e_f_g_h_i_j_k_l_m_n_o_p_q_r_s_t_u_v_w_x_y_z") == "a_b_c_d_e_f_g_h_i_j_k_l_m_n_o_p_q_r_s_t_u_v_w_x_y_z"

def test_sanitize_label_invalid_inputs():
    with pytest.raises(ValueError, match="Invalid label 'Invalid-Label': must be alphanumeric with underscores"):
        _sanitize_label("Invalid-Label")
    with pytest.raises(ValueError, match="Invalid label '123': must be alphanumeric with underscores"):
        _sanitize_label("123")
    with pytest.raises(ValueError, match="Invalid label '!@#$%^&*()': must be alphanumeric with underscores"):
        _sanitize_label("!@#$%^&*()")

def test_sanitize_label_none_input():
    with pytest.raises(ValueError, match="Invalid label 'None': must be alphanumeric with underscores"):
        _sanitize_label(None)

def test_sanitize_label_empty_string():
    with pytest.raises(ValueError, match="Invalid label '': must be alphanumeric with underscores"):
        _sanitize_label("")