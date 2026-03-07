import pytest

from unified_core.config.ports import validate_no_conflicts, PORTS

def test_happy_path():
    """Test with normal inputs."""
    # Since we are testing the actual behavior of the function,
    # we don't need to mock or change the PORTS dictionary.
    assert validate_no_conflicts() is True

def test_empty_ports():
    """Test with an empty PORTS dictionary."""
    # Temporarily replace PORTS with an empty dictionary
    original_ports = dict(PORTS)
    PORTS.clear()
    try:
        assert validate_no_conflicts() is True
    finally:
        PORTS.update(original_ports)

def test_none_ports():
    """Test with None for PORTS."""
    # Temporarily set PORTS to None
    original_ports = PORTS
    PORTS = None
    try:
        assert validate_no_conflicts() is False
    finally:
        PORTS = original_ports

def test_boundary_conditions():
    """Test boundary conditions (e.g., very high, very low ports)."""
    # Add boundary port values to PORTS and then remove them
    original_ports = dict(PORTS)
    boundary_ports = [0, 65535] + list(range(1024, 1024 + 10))
    for port in boundary_ports:
        PORTS.add(port)
    try:
        assert validate_no_conflicts() is True
    finally:
        PORTS.update(original_ports)

def test_with_duplicates():
    """Test with duplicate ports."""
    # Add duplicate port values to PORTS
    original_ports = dict(PORTS)
    duplicate_port = 8080
    PORTS.add(duplicate_port)
    PORTS.add(duplicate_port)
    try:
        with pytest.raises(ValueError, match="Port conflict detected: {8080}"):
            validate_no_conflicts()
    finally:
        PORTS.update(original_ports)

def test_with_invalid_inputs():
    """Test with invalid inputs (e.g., non-integer ports)."""
    # Add a non-integer port value to PORTS
    original_ports = dict(PORTS)
    invalid_port = "not_a_port"
    PORTS.add(invalid_port)
    try:
        with pytest.raises(ValueError, match="Port conflict detected: {'not_a_port'}"):
            validate_no_conflicts()
    finally:
        PORTS.update(original_ports)

# Run these tests using pytest
if __name__ == "__main__":
    pytest.main(["-v", "-k test_validate_no_conflicts"])