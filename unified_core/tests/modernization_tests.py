#!/usr/bin/env python3
"""
Modernization Verification Suite (MVS)
Verifies system integrity after autonomous upgrades.
"""

import sys
import unittest
import requests
import json
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mvs")

class TestSystemIntegrity(unittest.TestCase):
    BASE_URL = "http://localhost:8000/agent"

    def test_01_daemon_status(self):
        """Verify the agent daemon is running."""
        try:
            response = requests.get(f"{self.BASE_URL}/status", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data.get("state"), "running")
            logger.info("✅ Daemon status verified: RUNNING")
        except Exception as e:
            self.fail(f"Daemon health check failed: {e}")

    def test_02_ai_core_health(self):
        """Verify AI core components (WorldModel, GravityWell) are active."""
        try:
            response = requests.get(f"{self.BASE_URL}/ai/status", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data.get("ai_core_active"))
            
            components = data.get("components", {})
            self.assertTrue(components.get("world_model", {}).get("initialized"))
            self.assertTrue(components.get("gravity_well", {}).get("initialized"))
            logger.info("✅ AI Core components verified: ACTIVE")
        except Exception as e:
            self.fail(f"AI Core health check failed: {e}")

    def test_03_belief_integrity(self):
        """Verify WorldModel is still maintaining beliefs."""
        try:
            response = requests.get(f"{self.BASE_URL}/ai/beliefs", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertGreater(data.get("total_beliefs", 0), 0)
            logger.info(f"✅ Belief integrity verified: {data.get('total_beliefs')} beliefs found")
        except Exception as e:
            self.fail(f"Belief integrity check failed: {e}")

    def test_04_critical_imports(self):
        """Verify that core libraries are still importable."""
        libraries = ["setuptools", "requests", "fastapi", "psutil", "torch"]
        for lib in libraries:
            try:
                __import__(lib)
                logger.info(f"✅ Library import verified: {lib}")
            except ImportError:
                self.fail(f"CRITICAL: Library {lib} is no longer importable after modernization!")

if __name__ == "__main__":
    unittest.main()
