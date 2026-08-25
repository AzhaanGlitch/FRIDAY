import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.automation.system_automation import SystemAutomation
from backend.agents.llm_orchestrator import LLMOrchestrator

class TestFridayAdvancedPhase1(unittest.TestCase):

    def test_system_info_intent(self):
        """Test system info automation routing."""
        result = SystemAutomation.execute_intent("system_info", {})
        self.assertTrue(result.get("success"))

    def test_orchestrator_open_app(self):
        """Test command orchestrator parsing 'open calculator'."""
        response = LLMOrchestrator.process_command("open calculator")
        self.assertEqual(response.get("action_executed"), "open_app")

    def test_orchestrator_close_app(self):
        """Test command orchestrator parsing 'close calculator'."""
        response = LLMOrchestrator.process_command("close calculator")
        self.assertEqual(response.get("action_executed"), "close_app")

    def test_orchestrator_set_volume(self):
        """Test command orchestrator parsing volume command."""
        response = LLMOrchestrator.process_command("set volume to 30")
        self.assertEqual(response.get("action_executed"), "set_volume")

    def test_orchestrator_mute_unmute(self):
        """Test mute & unmute intents."""
        res_mute = LLMOrchestrator.process_command("mute sound")
        self.assertEqual(res_mute.get("action_executed"), "mute_sound")
        res_unmute = LLMOrchestrator.process_command("unmute sound")
        self.assertEqual(res_unmute.get("action_executed"), "mute_sound")

    def test_orchestrator_clipboard(self):
        """Test clipboard set and get intents."""
        res_set = LLMOrchestrator.process_command("copy Hello FRIDAY")
        self.assertEqual(res_set.get("action_executed"), "clipboard_set")
        res_get = LLMOrchestrator.process_command("read clipboard")
        self.assertEqual(res_get.get("action_executed"), "clipboard_get")

    def test_orchestrator_open_url(self):
        """Test opening web URL intent."""
        response = LLMOrchestrator.process_command("open github.com")
        self.assertEqual(response.get("action_executed"), "open_url")

    def test_orchestrator_coding_mode(self):
        """Test multi-step coding mode intent."""
        response = LLMOrchestrator.process_command("start coding mode")
        self.assertEqual(response.get("action_executed"), "coding_mode")

    def test_orchestrator_screenshot(self):
        """Test screenshot intent parsing."""
        response = LLMOrchestrator.process_command("take a screenshot")
        self.assertEqual(response.get("action_executed"), "take_screenshot")

if __name__ == "__main__":
    unittest.main()
