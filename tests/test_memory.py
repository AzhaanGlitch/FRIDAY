import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.memory.database import MemoryDatabase
from backend.agents.llm_orchestrator import LLMOrchestrator

class TestFridayMemoryDB(unittest.TestCase):

    def setUp(self):
        MemoryDatabase.init_db()

    def test_save_and_retrieve_message(self):
        """Test saving and loading messages from SQLite."""
        MemoryDatabase.clear_history()
        res = MemoryDatabase.save_message("user", "Open Spotify")
        self.assertTrue(res.get("success"))

        res_reply = MemoryDatabase.save_message("friday", "Opening Spotify for you.", action="open_app")
        self.assertTrue(res_reply.get("success"))

        history = MemoryDatabase.get_recent_history(limit=10)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["text"], "Open Spotify")
        self.assertEqual(history[1]["action"], "open_app")

    def test_clear_history(self):
        """Test clearing conversation database."""
        MemoryDatabase.save_message("user", "Test message")
        res = MemoryDatabase.clear_history()
        self.assertTrue(res.get("success"))
        history = MemoryDatabase.get_recent_history()
        self.assertEqual(len(history), 0)

    def test_clear_history_intent(self):
        """Test 'clear history' intent parsing in LLMOrchestrator."""
        response = LLMOrchestrator.process_command("clear history")
        self.assertEqual(response.get("action_executed"), "clear_history")

if __name__ == "__main__":
    unittest.main()
