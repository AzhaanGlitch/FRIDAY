import sys
import subprocess
import urllib.parse
from backend.automation.mac_automation import MacAutomation
from backend.automation.win_automation import WinAutomation

class BrowserController:
    """
    Application-Specific Deep Controller for Web Browsers (Chrome / Safari / Edge).
    Supports direct search on Google, YouTube, GitHub, StackOverflow, etc.
    """

    @classmethod
    def search(cls, engine: str, query: str) -> dict:
        """Search query directly in browser using specified engine."""
        encoded = urllib.parse.quote(query.strip())
        engine_urls = {
            "google": f"https://www.google.com/search?q={encoded}",
            "youtube": f"https://www.youtube.com/results?search_query={encoded}",
            "github": f"https://github.com/search?q={encoded}",
            "stackoverflow": f"https://stackoverflow.com/questions/tagged/{encoded}",
            "chatgpt": "https://chatgpt.com",
            "twitter": f"https://twitter.com/search?q={encoded}"
        }

        target_url = engine_urls.get(engine.lower().strip(), f"https://www.google.com/search?q={encoded}")
        is_mac = sys.platform == "darwin"

        if is_mac:
            return MacAutomation.open_url(target_url)
        else:
            return WinAutomation.open_url(target_url)
