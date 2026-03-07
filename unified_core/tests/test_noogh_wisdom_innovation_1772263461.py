import pytest

from unified_core.noogh_wisdom import Icon, Direction

class TestIcon:

    def test_happy_path(self):
        icon_long = Icon(Direction.LONG)
        assert icon_long.icon() == "🟢📈"

        icon_short = Icon(Direction.SHORT)
        assert icon_short.icon() == "🔴📉"

    def test_edge_cases(self):
        # Edge cases are not applicable for this function as it only accepts valid Direction enums
        pass

    def test_error_cases(self):
        # This function does not raise any exceptions, so no error cases to test
        pass

    def test_async_behavior(self):
        # This function is synchronous and does not involve any async behavior, so no tests needed here
        pass