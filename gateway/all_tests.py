# gateway/all_tests.py

import unittest

from gateway.test_ws import TestWS
from gateway.test_base import TestBase
from gateway.test_ws_final import TestWSFinal
from gateway.test_ws_8001 import TestWS8001
from gateway.test_ws_2 import TestWS2
from gateway.test_ws_light import TestWSLight

class AllTests(unittest.TestCase):
    def test_ws(self):
        suite = unittest.TestSuite()
        suite.addTest(TestWS())
        runner = unittest.TextTestRunner()
        runner.run(suite)

    def test_base(self):
        suite = unittest.TestSuite()
        suite.addTest(TestBase())
        runner = unittest.TextTestRunner()
        runner.run(suite)

    def test_ws_final(self):
        suite = unittest.TestSuite()
        suite.addTest(TestWSFinal())
        runner = unittest.TextTestRunner()
        runner.run(suite)

    def test_ws_8001(self):
        suite = unittest.TestSuite()
        suite.addTest(TestWS8001())
        runner = unittest.TextTestRunner()
        runner.run(suite)

    def test_ws_2(self):
        suite = unittest.TestSuite()
        suite.addTest(TestWS2())
        runner = unittest.TextTestRunner()
        runner.run(suite)

    def test_ws_light(self):
        suite = unittest.TestSuite()
        suite.addTest(TestWSLight())
        runner = unittest.TextTestRunner()
        runner.run(suite)

if __name__ == '__main__':
    unittest.main()