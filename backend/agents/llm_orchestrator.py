import json
import re
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation

class LLMOrchestrator:
    """Orchestrates natural language intent parsing and response generation."""

    SYSTEM_PROMPT = """You are FRIDAY, an intelligent computer AI assistant.
You can execute commands on the user's computer or respond conversationally.
If the command requires system action, output JSON with 'action' and 'params'.

Supported actions:
- open_app (params: {"app_name": "Spotify" | "Calculator" | "VSCode" | ...})
- set_volume (params: {"level": 0 to 100})
- take_screenshot (params: {})
- system_info (params: {})

Format response:
If executing action:
{"action": "<action_name>", "params": {...}, "response": "<Natural response to speak to user>"}

If purely conversational:
{"action": "none", "params": {}, "response": "<Conversational response>"}
"""

    @classmethod
    def process_command(cls, user_text: str) -> dict:
        """Process natural language user command."""
        text_lower = user_text.lower().strip()

        # Rule-based fast intent matching for MVP reliability
        if "open " in text_lower or "launch " in text_lower:
            app = text_lower.replace("open ", "").replace("launch ", "").replace("please", "").strip()
            # Clean app name capitalizations
            app_map = {
                "spotify": "Spotify",
                "calculator": "Calculator",
                "vscode": "Visual Studio Code",
                "code": "Visual Studio Code",
                "finder": "Finder",
                "safari": "Safari",
                "chrome": "Google Chrome",
                "terminal": "Terminal"
            }
            app_target = app_map.get(app, app.capitalize())
            action_res = SystemAutomation.execute_intent("open_app", {"app_name": app_target})
            if action_res.get("success"):
                return {
                    "text_response": f"Opening {app_target} for you.",
                    "action_executed": "open_app",
                    "result": action_res
                }
            else:
                return {
                    "text_response": f"I tried to open {app_target}, but ran into an error: {action_res.get('error')}",
                    "action_executed": "open_app",
                    "result": action_res
                }

        elif "volume" in text_lower:
            # Extract number
            numbers = re.findall(r'\d+', text_lower)
            level = int(numbers[0]) if numbers else 50
            action_res = SystemAutomation.execute_intent("set_volume", {"level": level})
            return {
                "text_response": f"Setting volume to {level} percent.",
                "action_executed": "set_volume",
                "result": action_res
            }

        elif "screenshot" in text_lower:
            action_res = SystemAutomation.execute_intent("take_screenshot", {})
            return {
                "text_response": "Captured screen screenshot.",
                "action_executed": "take_screenshot",
                "result": action_res
            }

        elif "system info" in text_lower or "status" in text_lower:
            action_res = SystemAutomation.execute_intent("system_info", {})
            info = action_res.get("info", {})
            return {
                "text_response": f"Running on {info.get('platform', 'macOS')} (Python {info.get('python_version')}). All systems operational.",
                "action_executed": "system_info",
                "result": action_res
            }

        # Fallback to Ollama or Default Conversational AI
        try:
            if settings.LLM_PROVIDER == "ollama":
                res = requests.post(
                    f"{settings.OLLAMA_HOST}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": f"{cls.SYSTEM_PROMPT}\nUser: {user_text}\nAssistant:", "stream": False},
                    timeout=5
                )
                if res.status_code == 200:
                    data = res.json()
                    return {"text_response": data.get("response", "I am online and ready."), "action_executed": "none"}
        except Exception:
            pass

        # Conversational fallback response
        return {
            "text_response": f"I heard: '{user_text}'. I am online and ready to help you control your system.",
            "action_executed": "none"
        }
