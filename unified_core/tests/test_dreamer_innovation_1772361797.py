import pytest

class TestDreamerSetGravityWell:
    def test_happy_path(self):
        from unified_core.dreamer import Dreamer, GravityWell
        
        dreamer = Dreamer()
        gravity_well = GravityWell()

        dreamer.set_gravity_well(gravity_well)
        assert dreamer._gravity_well == gravity_well

    def test_edge_case_none_input(self):
        from unified_core.dreamer import Dreamer
        
        dreamer = Dreamer()
        
        dreamer.set_gravity_well(None)
        assert dreamer._gravity_well is None

    def test_edge_case_empty_input(self):
        from unified_core.dreamer import Dreamer
        
        dreamer = Dreamer()
        
        dreamer.set_gravity_well({})
        assert dreamer._gravity_well == {}

    def test_error_case_invalid_type_input(self):
        from unified_core.dreamer import Dreamer
        
        dreamer = Dreamer()
        
        with pytest.raises(TypeError) as exc_info:
            dreamer.set_gravity_well("not a GravityWell")
        
        exception_msg = str(exc_info.value)
        assert "set_gravity_well" in exception_msg
        assert "must be an instance of GravityWell or None" in exception_msg

    def test_async_behavior(self):
        from unified_core.dreamer import Dreamer, GravityWell
        
        dreamer = Dreamer()
        gravity_well = GravityWell()

        async def set_gravity_well_async():
            await dreamer.set_gravity_well(gravity_well)
            assert dreamer._gravity_well == gravity_well

        pytest.run_coroutine(set_gravity_well_async())