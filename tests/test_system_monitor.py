import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.automation.system_monitor import SystemMonitor
from backend.automation.system_automation import SystemAutomation
from backend.agents.llm_orchestrator import LLMOrchestrator

class TestFridaySystemMonitor(unittest.TestCase):

    def test_system_metrics(self):
        """Test retrieving live system CPU, RAM, Disk, and Battery telemetry."""
        result = SystemMonitor.get_metrics()
        self.assertTrue(result.get("success"))
        metrics = result.get("metrics", {})
        self.assertIn("cpu_percent", metrics)
        self.assertIn("ram_percent", metrics)
        self.assertIn("disk_percent", metrics)
        self.assertIn("battery", metrics)
        print(f"\n[Test Monitor Metrics]: {metrics}")

    def test_system_info_intent(self):
        """Test system info intent."""
        result = SystemAutomation.execute_intent("system_info", {})
        self.assertTrue(result.get("success"))

if __name__ == "__main__":
    unittest.main()
