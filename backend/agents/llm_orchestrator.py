import json
import re
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation
from backend.memory.database import MemoryDatabase

class LLMOrchestrator:
    """Orchestrates natural language intent parsing, fuzzy matching, and fast execution."""

    SYSTEM_PROMPT = """You are FRIDAY, an advanced AI desktop assistant.
Analyze the user's spoken input:

1. If the user is giving an actionable computer command or asking a direct question:
   - For system commands, return JSON: {"action": "<action_name>", "params": {...}, "spoken_reply": "<short reply to speak>"}
   - Supported actions: open_app, close_app, open_url, set_volume, mute_sound, set_brightness, media_control, lock_screen, take_screenshot, terminate_system, coding_mode.
   - For direct questions (e.g., "what time is it", "who is Tony Stark"), reply in 1 short sentence.

2. If the user's input is background chatter, random talking, filler words (e.g. "oh it's okay", "are there eight seconds", "umm", "yeah so"), or not addressing the assistant:
   - Output EXACTLY: SILENT
"""

    @classmethod
    def _is_random_or_filler(cls, text_lower: str) -> bool:
        """Check if input is random chatter, background noise, or filler words."""
        # Clean punctuation
        cleaned = re.sub(r'[^\w\s]', '', text_lower).strip()
        
        # Single short words or common fillers
        fillers = {
            "oh", "okay", "ok", "its okay", "its ok", "oh its okay", "oh its ok",
            "umm", "um", "uh", "yeah", "yes", "no", "nah", "hmm", "hm",
            "thank you", "thanks", "are there eight seconds", "testing",
            "hello", "hi", "hey", "nothing", "nevermind", "never mind"
        }
        if cleaned in fillers:
            return True
            
        return False

    @classmethod
    def _fuzzy_direct_match(cls, text_lower: str) -> dict | None:
        """
        Ultra-fast direct keyword & fuzzy regex matching (< 1ms).
        Prioritizes native installed macOS applications first before web fallback.
        """
        # 1. Termination
        if any(w in text_lower for w in ["terminate the system", "terminate system", "shutdown system", "exit system", "goodbye friday"]):
            return {
                "action": "terminate_system",
                "params": {},
                "spoken_reply": "Terminating system. Goodbye sir."
            }

        # 2. Open App (Prioritize Native Desktop Apps!)
        app_map = {
            "spotify": "Spotify",
            "calculator": "Calculator",
            "calc": "Calculator",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "code": "Visual Studio Code",
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "safari": "Safari",
            "terminal": "Terminal",
            "finder": "Finder",
            "music": "Music",
            "apple music": "Music",
            "notes": "Notes",
            "mail": "Mail",
            "messages": "Messages",
            "slack": "Slack",
            "discord": "Discord",
            "settings": "System Settings",
            "system settings": "System Settings",
            "photos": "Photos",
            "calendar": "Calendar",
            "facetime": "FaceTime",
            "whatsapp": "WhatsApp",
            "telegram": "Telegram",
            "zoom": "zoom.us",
            "figma": "Figma",
            "notion": "Notion"
        }

        for app_key, app_val in app_map.items():
            pattern = rf'(?:open|launch|start|run|play)?\s*(?:the\s+app\s+)?\b{re.escape(app_key)}\b'
            if re.search(pattern, text_lower):
                return {
                    "action": "open_app",
                    "params": {"app_name": app_val},
                    "spoken_reply": f"Opening {app_val}."
                }

        # 3. Web URL Open
        web_domains = {
            "youtube": "youtube.com",
            "google": "google.com",
            "github": "github.com",
            "twitter": "twitter.com",
            "x.com": "x.com",
            "reddit": "reddit.com",
            "netflix": "netflix.com",
            "chatgpt": "chatgpt.com",
            "linkedin": "linkedin.com",
            "instagram": "instagram.com",
            "facebook": "facebook.com",
            "amazon": "amazon.com"
        }
        for site_key, domain in web_domains.items():
            if site_key in text_lower:
                return {
                    "action": "open_url",
                    "params": {"url": domain},
                    "spoken_reply": f"Opening {site_key.capitalize()} in your browser."
                }

        if "." in text_lower and any(w in text_lower for w in [".com", ".org", ".io", ".dev", ".ai", "http"]):
            words = text_lower.split()
            url = next((w for w in words if "." in w or w.startswith("http")), words[-1])
            return {
                "action": "open_url",
                "params": {"url": url},
                "spoken_reply": f"Opening {url}."
            }

        # 4. Close App
        close_match = re.search(r'(?:close|quit|exit|kill|stop)\s+(?:up\s+)?([a-zA-Z0-9\.\s]+)', text_lower)
        if close_match:
            target = close_match.group(1).strip().replace("please", "").strip()
            app_target = app_map.get(target.lower(), target.capitalize())
            return {
                "action": "close_app",
                "params": {"app_name": app_target},
                "spoken_reply": f"Closing {app_target}."
            }

        # 5. Volume Controls
        if "volume" in text_lower or "sound" in text_lower:
            if "mute" in text_lower:
                return {"action": "mute_sound", "params": {"mute": True}, "spoken_reply": "Muting system audio."}
            if "unmute" in text_lower:
                return {"action": "mute_sound", "params": {"mute": False}, "spoken_reply": "Unmuting system audio."}
            numbers = re.findall(r'\d+', text_lower)
            level = int(numbers[0]) if numbers else 50
            return {"action": "set_volume", "params": {"level": level}, "spoken_reply": f"Setting volume to {level}%."}

        # 6. Media Playback
        if any(w in text_lower for w in ["pause music", "pause song", "pause playback", "pause"]):
            return {"action": "media_control", "params": {"action": "pause"}, "spoken_reply": "Paused playback."}
        if any(w in text_lower for w in ["play music", "resume music", "play song", "resume"]):
            return {"action": "media_control", "params": {"action": "play"}, "spoken_reply": "Resumed playback."}
        if any(w in text_lower for w in ["next song", "next track", "skip song"]):
            return {"action": "media_control", "params": {"action": "next"}, "spoken_reply": "Skipping to next track."}

        # 7. Screenshot
        if "screenshot" in text_lower or "screen capture" in text_lower:
            return {"action": "take_screenshot", "params": {}, "spoken_reply": "Screenshot captured."}

        # 8. Lock screen
        if "lock screen" in text_lower or "lock mac" in text_lower:
            return {"action": "lock_screen", "params": {}, "spoken_reply": "Locking screen."}

        # 9. Coding mode
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
                    "temperature": 0.3,
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
        """Process command: execute actions or stay silent if random talk."""
        text_lower = user_text.lower().strip()

        # Step 1: Instant Filter for Fillers / Random Chatter (Remain completely silent)
        if cls._is_random_or_filler(text_lower):
            print(f"[LLM Filter]: Ignored random background speech: '{user_text}'")
            return {
                "text_response": "",
                "action_executed": "none",
                "result": {"ignored": True}
            }

        # Step 2: Instant Fuzzy / Intent Match (<1ms response time)
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
            if spoken_reply:
                MemoryDatabase.save_message("friday", spoken_reply, action=action)

            return {
                "text_response": spoken_reply,
                "action_executed": action,
                "result": action_res
            }

        # Step 3: Groq LLM Intelligent Processing
        llm_response = cls._call_groq_with_fallbacks(user_text)

        # If LLM classified this as random chatter
        if not llm_response or llm_response.strip().upper() == "SILENT":
            print(f"[LLM Intent]: Classified as random chatter — remaining silent.")
            return {
                "text_response": "",
                "action_executed": "none",
                "result": {"ignored": True}
            }

        # Check if Groq returned a JSON action
        if llm_response.startswith("{") and "action" in llm_response:
            try:
                parsed = json.loads(llm_response)
                action = parsed.get("action", "none")
                params = parsed.get("params", {})
                spoken = parsed.get("spoken_reply", "")
                action_res = SystemAutomation.execute_intent(action, params)

                MemoryDatabase.save_message("user", user_text)
                if spoken:
                    MemoryDatabase.save_message("friday", spoken, action=action)
                return {
                    "text_response": spoken,
                    "action_executed": action,
                    "result": action_res
                }
            except Exception:
                pass

        # Only speak for genuine conversational answers
        MemoryDatabase.save_message("user", user_text)
        MemoryDatabase.save_message("friday", llm_response, action="none")

        return {
            "text_response": llm_response,
            "action_executed": "none",
            "result": {}
        }
