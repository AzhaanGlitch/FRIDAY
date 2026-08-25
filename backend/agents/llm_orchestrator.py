import json
import re
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation
from backend.memory.database import MemoryDatabase

class LLMOrchestrator:

    """Orchestrates natural language intent parsing and response generation."""

    SYSTEM_PROMPT = """You are FRIDAY, an intelligent computer AI assistant.
You can execute commands on the user's computer or respond conversationally.
If the command requires system action, output JSON with 'action' and 'params'.

Supported actions:
- open_app (params: {"app_name": "Spotify" | "Calculator" | "VSCode" | ...})
- close_app (params: {"app_name": "Spotify" | "Calculator" | ...})
- set_volume (params: {"level": 0 to 100})
- mute_sound (params: {"mute": true | false})
- minimize_all (params: {})
- media_control (params: {"action": "play" | "pause" | "next" | "previous"})
- lock_screen (params: {})
- sleep_system (params: {})
- set_brightness (params: {"level": 0 to 100})
- clipboard_get (params: {})
- clipboard_set (params: {"text": "<text>"})
- search_file (params: {"filename": "<file_name>"})
- open_url (params: {"url": "<url>"})
- take_screenshot (params: {})
- system_info (params: {})
- coding_mode (params: {})
"""

    @classmethod
    def process_command(cls, user_text: str) -> dict:
        """Process natural language user command."""
        text_lower = user_text.lower().strip()

        # Clear History Intent
        if "clear history" in text_lower or "forget history" in text_lower or "delete conversation" in text_lower:
            res = MemoryDatabase.clear_history()
            return {"text_response": "Cleared all conversation history from local database.", "action_executed": "clear_history", "result": res}

        # Terminate System Intent (Shutdown app & loop)
        elif "terminate the system" in text_lower or "terminate system" in text_lower or "shutdown system" in text_lower:
            MemoryDatabase.save_message("user", user_text)
            MemoryDatabase.save_message("friday", "Terminating system. Goodbye sir.", action="terminate_system")
            return {
                "text_response": "Terminating system. Goodbye sir.",
                "action_executed": "terminate_system",
                "result": {"terminate": True}
            }


        # Multi-Step Workflow: Coding Mode
        if "coding mode" in text_lower or "start coding" in text_lower:
            res1 = SystemAutomation.execute_intent("open_app", {"app_name": "Visual Studio Code"})
            res2 = SystemAutomation.execute_intent("open_app", {"app_name": "Terminal"})
            res3 = SystemAutomation.execute_intent("open_url", {"url": "github.com"})
            res4 = SystemAutomation.execute_intent("set_volume", {"level": 35})
            output_msg = "Initiating coding mode. Opened VS Code, Terminal, GitHub, and set volume to 35%."
            MemoryDatabase.save_message("user", user_text)
            MemoryDatabase.save_message("friday", output_msg, action="coding_mode")
            return {
                "text_response": output_msg,
                "action_executed": "coding_mode",
                "result": {"vscode": res1, "terminal": res2, "browser": res3, "volume": res4}
            }


        # Close App
        elif text_lower.startswith("close ") or text_lower.startswith("quit ") or text_lower.startswith("exit "):
            app = text_lower.replace("close ", "").replace("quit ", "").replace("exit ", "").replace("please", "").strip()
            action_res = SystemAutomation.execute_intent("close_app", {"app_name": app})
            return {
                "text_response": f"Closing {app}." if action_res.get("success") else f"Failed to close {app}: {action_res.get('error')}",
                "action_executed": "close_app",
                "result": action_res
            }

        # Open App
        elif text_lower.startswith("open ") or text_lower.startswith("launch "):
            target = text_lower.replace("open ", "").replace("launch ", "").replace("please", "").strip()
            # If target looks like a website domain
            if "." in target or target.startswith("http") or target in ["google", "youtube", "github", "twitter"]:
                url = target if "." in target else f"{target}.com"
                action_res = SystemAutomation.execute_intent("open_url", {"url": url})
                return {
                    "text_response": f"Opening {url} in your browser.",
                    "action_executed": "open_url",
                    "result": action_res
                }
            
            app_map = {
                "spotify": "Spotify", "calculator": "Calculator", "vscode": "Visual Studio Code",
                "code": "Visual Studio Code", "finder": "Finder", "safari": "Safari",
                "chrome": "Google Chrome", "terminal": "Terminal", "notepad": "Notepad"
            }
            app_target = app_map.get(target, target.capitalize())
            action_res = SystemAutomation.execute_intent("open_app", {"app_name": app_target})
            return {
                "text_response": f"Opening {app_target} for you." if action_res.get("success") else f"Could not launch {app_target}: {action_res.get('error')}",
                "action_executed": "open_app",
                "result": action_res
            }

        # Mute / Unmute Sound
        elif "unmute sound" in text_lower or "unmute" in text_lower:
            action_res = SystemAutomation.execute_intent("mute_sound", {"mute": False})
            return {"text_response": "Unmuted system audio.", "action_executed": "mute_sound", "result": action_res}

        elif "mute sound" in text_lower or "mute" in text_lower:
            action_res = SystemAutomation.execute_intent("mute_sound", {"mute": True})
            return {"text_response": "Muted system audio.", "action_executed": "mute_sound", "result": action_res}

        # Volume
        elif "volume" in text_lower:
            numbers = re.findall(r'\d+', text_lower)
            level = int(numbers[0]) if numbers else 50
            action_res = SystemAutomation.execute_intent("set_volume", {"level": level})
            return {"text_response": f"Setting volume to {level} percent.", "action_executed": "set_volume", "result": action_res}

        # Brightness
        elif "brightness" in text_lower:
            numbers = re.findall(r'\d+', text_lower)
            level = int(numbers[0]) if numbers else 80
            action_res = SystemAutomation.execute_intent("set_brightness", {"level": level})
            return {"text_response": f"Adjusted screen brightness to {level} percent.", "action_executed": "set_brightness", "result": action_res}

        # Minimize All / Show Desktop
        elif "minimize all" in text_lower or "show desktop" in text_lower or "hide windows" in text_lower:
            action_res = SystemAutomation.execute_intent("minimize_all", {})
            return {"text_response": "Minimized all windows.", "action_executed": "minimize_all", "result": action_res}

        # Media controls (pause/play/next/previous)
        elif "pause music" in text_lower or "pause video" in text_lower or text_lower == "pause":
            action_res = SystemAutomation.execute_intent("media_control", {"action": "pause"})
            return {"text_response": "Paused media playback.", "action_executed": "media_control", "result": action_res}

        elif "play music" in text_lower or "resume music" in text_lower or text_lower == "play":
            action_res = SystemAutomation.execute_intent("media_control", {"action": "play"})
            return {"text_response": "Resumed media playback.", "action_executed": "media_control", "result": action_res}

        elif "next song" in text_lower or "next track" in text_lower:
            action_res = SystemAutomation.execute_intent("media_control", {"action": "next"})
            return {"text_response": "Skipped to next track.", "action_executed": "media_control", "result": action_res}

        # Lock / Sleep
        elif "lock screen" in text_lower or "lock pc" in text_lower or "lock computer" in text_lower or "lock mac" in text_lower:
            action_res = SystemAutomation.execute_intent("lock_screen", {})
            return {"text_response": "Locking screen.", "action_executed": "lock_screen", "result": action_res}

        elif "sleep system" in text_lower or "sleep computer" in text_lower or "put laptop to sleep" in text_lower:
            action_res = SystemAutomation.execute_intent("sleep_system", {})
            return {"text_response": "Putting system to sleep.", "action_executed": "sleep_system", "result": action_res}

        # Clipboard Operations
        elif "read clipboard" in text_lower or "what's in clipboard" in text_lower or "get clipboard" in text_lower:
            action_res = SystemAutomation.execute_intent("clipboard_get", {})
            content = action_res.get("content", "")
            return {
                "text_response": f"Clipboard contents: '{content}'" if content else "Clipboard is empty.",
                "action_executed": "clipboard_get",
                "result": action_res
            }

        elif text_lower.startswith("copy ") or text_lower.startswith("set clipboard "):
            text_to_copy = text_lower.replace("copy ", "").replace("set clipboard ", "").strip()
            action_res = SystemAutomation.execute_intent("clipboard_set", {"text": text_to_copy})
            return {"text_response": f"Copied '{text_to_copy}' to clipboard.", "action_executed": "clipboard_set", "result": action_res}

        # Search File
        elif "find file" in text_lower or "search file" in text_lower or "find document" in text_lower:
            filename = text_lower.replace("find file", "").replace("search file", "").replace("find document", "").strip()
            action_res = SystemAutomation.execute_intent("search_file", {"filename": filename})
            files = action_res.get("files", [])
            return {
                "text_response": f"Found {len(files)} matching file(s): {', '.join(files[:3])}" if files else f"No files matching '{filename}' found.",
                "action_executed": "search_file",
                "result": action_res
            }

        # Screenshot
        elif "screenshot" in text_lower or "capture screen" in text_lower:
            action_res = SystemAutomation.execute_intent("take_screenshot", {})
            return {"text_response": "Captured screenshot.", "action_executed": "take_screenshot", "result": action_res}

        # System Info
        elif "system info" in text_lower or "status" in text_lower:
            action_res = SystemAutomation.execute_intent("system_info", {})
            info = action_res.get("info", {})
            return {
                "text_response": f"Running on {info.get('platform', 'macOS')} (Python {info.get('python_version')}). All systems operational.",
                "action_executed": "system_info",
                "result": action_res
            }

        # Fallback to Ollama or Default Conversational AI
        text_resp = f"I heard: '{user_text}'. All FRIDAY automation drivers online."
        try:
            if settings.LLM_PROVIDER == "ollama":
                res = requests.post(
                    f"{settings.OLLAMA_HOST}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": f"{cls.SYSTEM_PROMPT}\nUser: {user_text}\nAssistant:", "stream": False},
                    timeout=5
                )
                if res.status_code == 200:
                    data = res.json()
                    text_resp = data.get("response", "I am online and ready.")
        except Exception:
            pass

        MemoryDatabase.save_message("user", user_text)
        MemoryDatabase.save_message("friday", text_resp, action="none")

        return {
            "text_response": text_resp,
            "action_executed": "none"
        }

