import pytest
from unittest.mock import patch, mock_open
import platform
import socket
import os

@pytest.fixture
def mock_platform():
    with patch('platform.system', return_value='Linux'), \
         patch('platform.release', return_value='5.4.0'), \
         patch('platform.machine', return_value='x86_64'):
        yield

@pytest.fixture
def mock_socket():
    with patch('socket.gethostname', return_value='localhost'):
        yield

@pytest.fixture
def mock_os_release():
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data='PRETTY_NAME="Ubuntu 20.04 LTS"')):
        yield

def test_get_os_info_happy_path(mock_platform, mock_socket, mock_os_release):
    from neural_engine.tools.basic_tools import get_os_info
    expected_output = (
        "### 🖥️ معلومات النظام\n"
        "**النظام:** Linux 5.4.0\n"
        "**المعمارية:** x86_64\n"
        "**الجهاز:** localhost\n"
        "**التوزيعة:** Ubuntu 20.04 LTS"
    )
    assert get_os_info() == expected_output

def test_get_os_info_no_os_release(mock_platform, mock_socket):
    with patch('os.path.exists', return_value=False):
        from neural_engine.tools.basic_tools import get_os_info
        expected_output = (
            "### 🖥️ معلومات النظام\n"
            "**النظام:** Linux 5.4.0\n"
            "**المعمارية:** x86_64\n"
            "**الجهاز:** localhost"
        )
        assert get_os_info() == expected_output

def test_get_os_info_error(mock_platform, mock_socket):
    with patch('os.path.exists', side_effect=Exception("Path error")):
        from neural_engine.tools.basic_tools import get_os_info
        assert "خطا" in get_os_info()

def test_get_os_info_empty_hostname(mock_platform):
    with patch('socket.gethostname', return_value=''):
        from neural_engine.tools.basic_tools import get_os_info
        expected_output = (
            "### 🖥️ معلومات النظام\n"
            "**النظام:** Linux 5.4.0\n"
            "**المعمارية:** x86_64\n"
            "**الجهاز:** \n"
        )
        assert get_os_info() == expected_output

def test_get_os_info_invalid_os_release(mock_platform, mock_socket):
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data='INVALID_DATA')):
        from neural_engine.tools.basic_tools import get_os_info
        expected_output = (
            "### 🖥️ معلومات النظام\n"
            "**النظام:** Linux 5.4.0\n"
            "**المعمارية:** x86_64\n"
            "**الجهاز:** localhost"
        )
        assert get_os_info() == expected_output