import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.automation.system_automation import SystemAutomation
from backend.agents.llm_orchestrator import LLMOrchestrator
from backend.automation.file_manager import FileManager
from backend.automation.clipboard_manager import ClipboardManager

class TestFridayPhase2Automation(unittest.TestCase):
    """Automated Unit & Integration Tests for Phase 2 Automation Layer."""

    def test_file_manager_create_and_search(self):
        """Test creating and searching a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            res_create = FileManager.create_file("test_phase2_doc.txt", "FRIDAY Phase 2 Content", directory=tmpdir)
            self.assertTrue(res_create.get("success"))
            self.assertTrue(os.path.exists(res_create.get("path")))

    def test_clipboard_manager_transform(self):
        """Test clipboard uppercase/lowercase transformations."""
        ClipboardManager.set_clipboard("friday test string")
        res_upper = ClipboardManager.transform_clipboard("upper")
        self.assertTrue(res_upper.get("success"))
        self.assertEqual(res_upper.get("transformed"), "FRIDAY TEST STRING")

        res_lower = ClipboardManager.transform_clipboard("lower")
        self.assertTrue(res_lower.get("success"))
        self.assertEqual(res_lower.get("transformed"), "friday test string")

    def test_orchestrator_spotify_play(self):
        """Test direct voice intent parsing for Spotify deep playback."""
        response = LLMOrchestrator.process_command("play Believer on Spotify")
        self.assertEqual(response.get("action_executed"), "spotify_play")
        self.assertIn("believer", response.get("parsed_params", {}).get("query", "").lower())

    def test_orchestrator_browser_search(self):
        """Test direct voice intent parsing for YouTube/Google browser search."""
        response = LLMOrchestrator.process_command("search on youtube quantum computing")
        self.assertEqual(response.get("action_executed"), "browser_search")
        self.assertEqual(response.get("parsed_params", {}).get("engine"), "youtube")

    def test_orchestrator_multi_step_workflows(self):
        """Test multi-step chained meeting and focus workflows."""
        res_meeting = LLMOrchestrator.process_command("start meeting mode")
        self.assertEqual(res_meeting.get("action_executed"), "execute_workflow")
        self.assertEqual(res_meeting.get("parsed_params", {}).get("workflow"), "meeting_mode")

        res_focus = LLMOrchestrator.process_command("start focus mode")
        self.assertEqual(res_focus.get("action_executed"), "execute_workflow")
        self.assertEqual(res_focus.get("parsed_params", {}).get("workflow"), "focus_mode")

    def test_orchestrator_file_search_intent(self):
        """Test search file voice intent."""
        response = LLMOrchestrator.process_command("find file resume.pdf")
        self.assertEqual(response.get("action_executed"), "search_file")
        self.assertEqual(response.get("parsed_params", {}).get("filename"), "resume.pdf")

if __name__ == "__main__":
    unittest.main()
