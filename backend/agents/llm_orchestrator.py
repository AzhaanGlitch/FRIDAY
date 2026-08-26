import json
import re
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation
from backend.memory.database import MemoryDatabase

class LLMOrchestrator:
    """Orchestrates natural language intent parsing, fuzzy matching, and fast execution."""

    SYSTEM_PROMPT = """You are FRIDAY (Female Replacement Intelligent Digital Assistant Youth), Tony Stark's sharp, intelligent, and witty AI desktop assistant.
Rules:
1. If the user wants to control the computer or open/close apps/websites, output a JSON object: {"action": "<action_name>", "params": {...}, "spoken_reply": "<short reply to speak>"}.
2. Supported actions:
   - open_app: {"app_name": "Spotify" | "VSCode" | "Chrome" | "Terminal" | ...}
   - close_app: {"app_name": "Spotify" | ...}
   - open_url: {"url": "youtube.com" | "google.com" | "github.com" | ...}
   - set_volume: {"level": 0-100}
   - mute_sound: {"mute": true | false}
   - set_brightness: {"level": 0-100}
   - media_control: {"action": "play" | "pause" | "next" | "previous"}
   - lock_screen: {}
   - take_screenshot: {}
   - terminate_system: {}
3. If it's a general question or conversation, reply naturally in 1-2 quick sentences for voice synthesis.
"""

    @classmethod
    def _fuzzy_direct_match(cls, text_lower: str) -> dict | None:
        """
        Ultra-fast direct keyword & fuzzy regex matching (< 1ms).
        Immediately triggers common commands even with imperfect transcription.
        """
        # 1. Termination
        if any(w in text_lower for w in ["terminate the system", "terminate system", "shutdown system", "exit system", "goodbye friday"]):
            return {
                "action": "terminate_system",
                "params": {},
                "spoken_reply": "Terminating system. Goodbye sir."
            }

        # 2. Open App / Websites (Fuzzy matching)
        # Catches "open spotify", "open up spotify", "launch spotify", "can you open spotify", "spotify please", "start spotify"
        open_match = re.search(r'(?:open|launch|start|run|play on)\s+(?:up\s+)?([a-zA-Z0-9\.\s]+)', text_lower)
        if open_match or any(w in text_lower for w in ["spotify", "youtube", "chrome", "google", "vscode", "terminal", "calculator", "safari"]):
            target = open_match.group(1).strip() if open_match else text_lower
            target = target.replace("please", "").replace("for me", "").replace("the app", "").replace("app", "").strip()

            # Check websites
            web_domains = {
                "youtube": "youtube.com", "google": "google.com", "github": "github.com",
                "twitter": "twitter.com", "x": "x.com", "reddit": "reddit.com",
                "netflix": "netflix.com", "facebook": "facebook.com", "instagram": "instagram.com",
                "linkedin": "linkedin.com", "chatgpt": "chatgpt.com"
            }
            for key, domain in web_domains.items():
                if key in target or key == text_lower.strip():
                    return {
                        "action": "open_url",
                        "params": {"url": domain},
                        "spoken_reply": f"Opening {key.capitalize()} in your browser."
                    }

            if "." in target or target.startswith("http"):
                return {
                    "action": "open_url",
                    "params": {"url": target},
                    "spoken_reply": f"Opening {target}."
                }

            # Check Applications
            app_map = {
                "spotify": "Spotify", "calculator": "Calculator", "calc": "Calculator",
                "vscode": "Visual Studio Code", "code": "Visual Studio Code", "vs code": "Visual Studio Code",
                "finder": "Finder", "safari": "Safari", "chrome": "Google Chrome",
                "google chrome": "Google Chrome", "terminal": "Terminal", "notepad": "Notepad",
                "settings": "System Settings", "music": "Music", "mail": "Mail", "slack": "Slack"
            }
            for app_key, app_val in app_map.items():
                if app_key in target:
                    return {
                        "action": "open_app",
                        "params": {"app_name": app_val},
                        "spoken_reply": f"Opening {app_val}."
                    }

        # 3. Close App
        close_match = re.search(r'(?:close|quit|exit|kill|stop)\s+(?:up\s+)?([a-zA-Z0-9\.\s]+)', text_lower)
        if close_match:
            target = close_match.group(1).strip().replace("please", "").strip()
            return {
                "action": "close_app",
                "params": {"app_name": target.capitalize()},
                "spoken_reply": f"Closing {target.capitalize()}."
            }

        # 4. Volume Controls
        if "volume" in text_lower or "sound" in text_lower:
            if "mute" in text_lower:
                return {"action": "mute_sound", "params": {"mute": True}, "spoken_reply": "Muting system audio."}
            if "unmute" in text_lower:
                return {"action": "mute_sound", "params": {"mute": False}, "spoken_reply": "Unmuting system audio."}
            numbers = re.findall(r'\d+', text_lower)
            level = int(numbers[0]) if numbers else 50
            return {"action": "set_volume", "params": {"level": level}, "spoken_reply": f"Setting volume to {level}%."}

        # 5. Media Playback
        if any(w in text_lower for w in ["pause music", "pause song", "pause playback", "pause"]):
            return {"action": "media_control", "params": {"action": "pause"}, "spoken_reply": "Paused playback."}
        if any(w in text_lower for w in ["play music", "resume music", "play song", "resume"]):
            return {"action": "media_control", "params": {"action": "play"}, "spoken_reply": "Resumed playback."}
        if any(w in text_lower for w in ["next song", "next track", "skip song"]):
            return {"action": "media_control", "params": {"action": "next"}, "spoken_reply": "Skipping to next track."}

        # 6. Screenshot
        if "screenshot" in text_lower or "screen capture" in text_lower:
            return {"action": "take_screenshot", "params": {}, "spoken_reply": "Screenshot captured."}

        # 7. Lock screen
        if "lock screen" in text_lower or "lock mac" in text_lower:
            return {"action": "lock_screen", "params": {}, "spoken_reply": "Locking screen."}

        # 8. Coding mode
        if "coding mode" in text_lower or "start coding" in text_lower:
            return {"action": "coding_mode", "params": {}, "spoken_reply": "Coding mode initiated."}

        return None

    @classmethod
    def _call_groq_with_fallbacks(cls, user_text: str) -> str:
        """Call Groq API with fallback chain."""
        if not settings.GROQ_API_KEY:
            return ""

        fallback_list = [m.strip() for m in settings.GROQ_FALLBACK_MODELS.split(",") if m.strip()]
        models_to_try = [settings.GROQ_MODEL] + [m for m in fallback_list if m != settings.GROQ_MODEL]

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        for model_name in models_to_try:
            try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": cls.SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 120
                }
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=4
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
            except Exception as e:
                print(f"[Groq Error ({model_name})]: {e}")

        return ""

    @classmethod
    def process_command(cls, user_text: str) -> dict:
        """Process command with instant execution + parallel voice feedback."""
        text_lower = user_text.lower().strip()

        # Step 1: Instant Fuzzy / Intent Match (<1ms response time)
        matched_intent = cls._fuzzy_direct_match(text_lower)
        if matched_intent:
            action = matched_intent["action"]
            params = matched_intent.get("params", {})
            spoken_reply = matched_intent.get("spoken_reply", "")

            # Execute intent immediately
            if action == "coding_mode":
                res1 = SystemAutomation.execute_intent("open_app", {"app_name": "Visual Studio Code"})
                res2 = SystemAutomation.execute_intent("open_app", {"app_name": "Terminal"})
                res3 = SystemAutomation.execute_intent("open_url", {"url": "github.com"})
                action_res = {"vscode": res1, "terminal": res2, "browser": res3}
            elif action == "terminate_system":
                action_res = {"terminate": True}
            else:
                action_res = SystemAutomation.execute_intent(action, params)

            MemoryDatabase.save_message("user", user_text)
            MemoryDatabase.save_message("friday", spoken_reply, action=action)

            return {
                "text_response": spoken_reply,
                "action_executed": action,
                "result": action_res
            }

        # Step 2: Groq LLM Intelligent Processing
        llm_response = cls._call_groq_with_fallbacks(user_text)

        # Check if Groq returned a JSON action
        if llm_response.startswith("{") and "action" in llm_response:
            try:
                parsed = json.loads(llm_response)
                action = parsed.get("action", "none")
                params = parsed.get("params", {})
                spoken = parsed.get("spoken_reply", f"Executing {action}.")
                action_res = SystemAutomation.execute_intent(action, params)

                MemoryDatabase.save_message("user", user_text)
                MemoryDatabase.save_message("friday", spoken, action=action)
                return {
                    "text_response": spoken,
                    "action_executed": action,
                    "result": action_res
                }
            except Exception:
                pass

        if not llm_response:
            llm_response = f"Acknowledged: '{user_text}'. All systems operational."

        MemoryDatabase.save_message("user", user_text)
        MemoryDatabase.save_message("friday", llm_response, action="none")

        return {
            "text_response": llm_response,
            "action_executed": "none",
            "result": {}
        }
