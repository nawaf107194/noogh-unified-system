# gateway/test_base.py

import unittest

class BaseTest(unittest.TestCase):
    def setUp(self):
        # Common setup logic here
        pass

    def tearDown(self):
        # Common teardown logic here
        pass

    def _find_function_in_file(self, file_path, function_name):
        # Extracted common logic
        with open(file_path, 'r') as file:
            content = file.read()
            return function_name in content

# gateway/test_ws.py
from .test_base import BaseTest

class TestWS(BaseTest):
    def test_function_in_file(self):
        result = self._find_function_in_file('gateway/architecture_1771627526.py', 'some_function')
        self.assertTrue(result)

# gateway/test_base_1771984410.py
from .test_base import BaseTest

class TestBase(BaseTest):
    def test_configuration(self):
        # Use common logic from BaseTest
        pass

# Repeat similar pattern for other test files...