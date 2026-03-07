import pytest

from monitor_agent import print_metrics_section

def test_print_metrics_section_happy_path():
    metrics = {
        'system': {
            'cpu_percent': 35.4,
            'memory_percent': 78.9,
            'memory_used_gb': 16.2,
            'memory_total_gb': 20.0,
            'disk_percent': 45.6
        },
        'agent': {
            'cpu_percent': 23.4,
            'memory_mb': 800,
            'num_threads': 10
        }
    }
    
    expected_output = (
        "\n📈 SYSTEM METRICS | مقاييس النظام\n"
        "--------------------------------------------------------------------------------\n"
        "   CPU: 35.4%\n"
        "   Memory: 78.9% (16.2GB / 20.0GB)\n"
        "   Disk: 45.6%\n\n"
        "   Agent Process:\n"
        "      CPU: 23.4%\n"
        "      Memory: 800 MB\n"
        "      Threads: 10"
    )
    
    with pytest.raises(SystemExit) as exc_info:
        captured_output = io.StringIO()
        sys.stdout = captured_output
        print_metrics_section(metrics)
        sys.stdout = sys.__stdout__
        
    assert captured_output.getvalue().strip() == expected_output.strip()

def test_print_metrics_section_empty_metrics():
    metrics = {}
    
    expected_output = (
        "\n📈 SYSTEM METRICS | مقاييس النظام\n"
        "--------------------------------------------------------------------------------\n"
        "   CPU: 0.0%\n"
        "   Memory: 0.0% (0.0GB / 0.0GB)\n"
        "   Disk: 0.0%"
    )
    
    with pytest.raises(SystemExit) as exc_info:
        captured_output = io.StringIO()
        sys.stdout = captured_output
        print_metrics_section(metrics)
        sys.stdout = sys.__stdout__
        
    assert captured_output.getvalue().strip() == expected_output.strip()

def test_print_metrics_section_none_metrics():
    metrics = None
    
    with pytest.raises(SystemExit) as exc_info:
        captured_output = io.StringIO()
        sys.stdout = captured_output
        print_metrics_section(metrics)
        sys.stdout = sys.__stdout__
        
    assert captured_output.getvalue().strip() == (
        "\n📈 SYSTEM METRICS | مقاييس النظام\n"
        "--------------------------------------------------------------------------------\n"
        "   CPU: 0.0%\n"
        "   Memory: 0.0% (0.0GB / 0.0GB)\n"
        "   Disk: 0.0%"
    )

def test_print_metrics_section_missing_agent():
    metrics = {
        'system': {
            'cpu_percent': 35.4,
            'memory_percent': 78.9,
            'memory_used_gb': 16.2,
            'memory_total_gb': 20.0,
            'disk_percent': 45.6
        }
    }
    
    expected_output = (
        "\n📈 SYSTEM METRICS | مقاييس النظام\n"
        "--------------------------------------------------------------------------------\n"
        "   CPU: 35.4%\n"
        "   Memory: 78.9% (16.2GB / 20.0GB)\n"
        "   Disk: 45.6%"
    )
    
    with pytest.raises(SystemExit) as exc_info:
        captured_output = io.StringIO()
        sys.stdout = captured_output
        print_metrics_section(metrics)
        sys.stdout = sys.__stdout__
        
    assert captured_output.getvalue().strip() == expected_output.strip()

def test_print_metrics_section_invalid_input():
    metrics = "not a dictionary"
    
    with pytest.raises(SystemExit) as exc_info:
        captured_output = io.StringIO()
        sys.stdout = captured_output
        print_metrics_section(metrics)
        sys.stdout = sys.__stdout__
        
    assert captured_output.getvalue().strip() == (
        "\n📈 SYSTEM METRICS | مقاييس النظام\n"
        "--------------------------------------------------------------------------------\n"
        "   CPU: 0.0%\n"
        "   Memory: 0.0% (0.0GB / 0.0GB)\n"
        "   Disk: 0.0%"
    )