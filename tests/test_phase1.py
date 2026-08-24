import unittest
import sys
import os

# Add root directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.automation.system_automation import SystemAutomation
from backend.agents.llm_orchestrator import LLMOrchestrator

class TestFridayPhase1(unittest.TestCase):

    def test_system_info_intent(self):
        """Test system info automation routing."""
        result = SystemAutomation.execute_intent("system_info", {})
        self.assertTrue(result.get("success"))
        print(f"\n[Test] System Info Result: {result}")

    def test_orchestrator_open_app(self):
        """Test command orchestrator parsing 'open calculator'."""
        response = LLMOrchestrator.process_command("open calculator")
        self.assertEqual(response.get("action_executed"), "open_app")
        print(f"[Test] Orchestrator Open App Result: {response}")

    def test_orchestrator_set_volume(self):
        """Test command orchestrator parsing volume command."""
        response = LLMOrchestrator.process_command("set volume to 30")
        self.assertEqual(response.get("action_executed"), "set_volume")
        print(f"[Test] Orchestrator Volume Result: {response}")

    def test_orchestrator_screenshot(self):
        """Test screenshot intent parsing."""
        response = LLMOrchestrator.process_command("take a screenshot")
        self.assertEqual(response.get("action_executed"), "take_screenshot")
        print(f"[Test] Orchestrator Screenshot Result: {response}")

if __name__ == "__main__":
    unittest.main()
