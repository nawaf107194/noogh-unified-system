import pytest

def test_print_health_section_happy_path():
    class HealthStatus:
        def __init__(self, overall_health, arabic_health, components=None, warnings=None):
            self.overall_health = overall_health
            self.arabic_health = arabic_health
            self.components = components or {}
            self.warnings = warnings or []
    
    health_data = HealthStatus(
        overall_health="healthy",
        arabic_health="صحة جيدة",
        components={"component1": "running", "component2": "stopped"},
        warnings=["warning1"]
    )
    
    expected_output = """\
💚 AGENT HEALTH | صحة الوكيل
--------------------------------------------------------------------------------
🟢 Overall: healthy | صحة جيدة
   Components:
      ✅ component1: running
      ❌ component2: stopped
   ⚠️  Warnings:
      • warning1"""
    
    captured_output = pytest.io.StringIO()
    with pytest.raises(SystemExit) as excinfo:
        print_health_section(health_data)
    
    assert excinfo.value.code is None
    assert captured_output.getvalue().strip() == expected_output

def test_print_health_section_empty_components():
    class HealthStatus:
        def __init__(self, overall_health, arabic_health, components=None, warnings=None):
            self.overall_health = overall_health
            self.arabic_health = arabic_health
            self.components = components or {}
            self.warnings = warnings or []
    
    health_data = HealthStatus(
        overall_health="healthy",
        arabic_health="صحة جيدة",
        components={},
        warnings=["warning1"]
    )
    
    expected_output = """\
💚 AGENT HEALTH | صحة الوكيل
--------------------------------------------------------------------------------
🟢 Overall: healthy | صحة جيدة
   ⚠️  Warnings:
      • warning1"""
    
    captured_output = pytest.io.StringIO()
    with pytest.raises(SystemExit) as excinfo:
        print_health_section(health_data)
    
    assert excinfo.value.code is None
    assert captured_output.getvalue().strip() == expected_output

def test_print_health_section_no_warnings():
    class HealthStatus:
        def __init__(self, overall_health, arabic_health, components=None, warnings=None):
            self.overall_health = overall_health
            self.arabic_health = arabic_health
            self.components = components or {}
            self.warnings = warnings or []
    
    health_data = HealthStatus(
        overall_health="healthy",
        arabic_health="صحة جيدة",
        components={"component1": "running", "component2": "stopped"},
        warnings=[]
    )
    
    expected_output = """\
💚 AGENT HEALTH | صحة الوكيل
--------------------------------------------------------------------------------
🟢 Overall: healthy | صحة جيدة
   Components:
      ✅ component1: running
      ❌ component2: stopped"""
    
    captured_output = pytest.io.StringIO()
    with pytest.raises(SystemExit) as excinfo:
        print_health_section(health_data)
    
    assert excinfo.value.code is None
    assert captured_output.getvalue().strip() == expected_output

def test_print_health_section_none_input():
    with pytest.raises(TypeError):
        print_health_section(None)

def test_print_health_section_invalid_components_type():
    class HealthStatus:
        def __init__(self, overall_health, arabic_health, components=None, warnings=None):
            self.overall_health = overall_health
            self.arabic_health = arabic_health
            self.components = components or {}
            self.warnings = warnings or []
    
    health_data = HealthStatus(
        overall_health="healthy",
        arabic_health="صحة جيدة",
        components="not a dictionary",
        warnings=["warning1"]
    )
    
    with pytest.raises(TypeError):
        print_health_section(health_data)

def test_print_health_section_invalid_warnings_type():
    class HealthStatus:
        def __init__(self, overall_health, arabic_health, components=None, warnings=None):
            self.overall_health = overall_health
            self.arabic_health = arabic_health
            self.components = components or {}
            self.warnings = warnings or []
    
    health_data = HealthStatus(
        overall_health="healthy",
        arabic_health="صحة جيدة",
        components={"component1": "running", "component2": "stopped"},
        warnings="not a list"
    )
    
    with pytest.raises(TypeError):
        print_health_section(health_data)