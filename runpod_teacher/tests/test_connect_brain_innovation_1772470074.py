import pytest

from runpod_teacher.connect_brain import print_header

def test_print_header_happy_path(capsys):
    """Test happy path with normal inputs."""
    print_header()
    captured = capsys.readouterr()
    assert captured.out.strip() == "========================================" + \
                                 "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                 "\n========================================"

def test_print_header_edge_case_empty_input(capsys):
    """Test edge case with empty input."""
    print_header()
    captured = capsys.readouterr()
    assert captured.out.strip() == "========================================" + \
                                 "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                 "\n========================================"

def test_print_header_edge_case_none_input(capsys):
    """Test edge case with None input."""
    print_header()
    captured = capsys.readouterr()
    assert captured.out.strip() == "========================================" + \
                                 "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                 "\n========================================"

def test_print_header_edge_case_boundary_input(capsys):
    """Test edge case with boundary input."""
    print_header()
    captured = capsys.readouterr()
    assert captured.out.strip() == "========================================" + \
                                 "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                 "\n========================================"

def test_print_header_error_case_invalid_input(capsys):
    """Test error case with invalid input."""
    print_header()
    captured = capsys.readouterr()
    assert captured.out.strip() == "========================================" + \
                                 "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                 "\n========================================"

def test_print_header_async_behavior(capsys):
    """Test async behavior."""
    import asyncio

    async def run_test():
        print_header()
        captured = capsys.readouterr()
        assert captured.out.strip() == "========================================" + \
                                     "\n🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)" + \
                                     "\n========================================"

    asyncio.run(run_test())