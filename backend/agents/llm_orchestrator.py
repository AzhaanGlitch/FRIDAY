import json
import re
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation
from backend.memory.database import MemoryDatabase

class LLMOrchestrator:
    """Orchestrates natural language intent parsing, fuzzy matching, and fast execution."""

    SYSTEM_PROMPT = """You are FRIDAY (Female Replacement Intelligent Digital Assistant Youth), an ultra-smart, witty, and highly fluent AI desktop assistant like Tony Stark's FRIDAY.

Language & Tone Rules:
- If user speaks in Hindi or Hinglish, reply in fluent, natural conversational Hindi.
- If user speaks in English, reply in natural fluent English.
- Keep spoken replies concise, warm, and human-like (1-2 sentences).

Command Handling Rules:
1. If the user wants to execute any computer action (open apps, close apps, websites, volume, brightness, music, coding mode, screenshot, lock), output JSON:
   {"action": "<action_name>", "params": {...}, "spoken_reply": "<short reply to speak>"}
   Actions available: open_app, close_app, open_url, set_volume, mute_sound, set_brightness, media_control, lock_screen, take_screenshot, terminate_system, coding_mode.

2. If the user asks a question (knowledge, advice, conversation), reply conversationally in 1-2 natural sentences.
3. If the input is random chatter or not addressed to you, output EXACTLY: SILENT
"""

    @classmethod
    def _is_random_or_filler(cls, text_lower: str) -> bool:
        """Check if input is random chatter, background noise, or filler words."""
        cleaned = re.sub(r'[^\w\s]', '', text_lower).strip()
        fillers = {
            "oh", "okay", "ok", "its okay", "its ok", "oh its okay", "oh its ok",
            "umm", "um", "uh", "yeah", "yes", "no", "nah", "hmm", "hm",
            "are there eight seconds", "testing", "nothing", "nevermind"
        }
        return cleaned in fillers

    @classmethod
    def _fuzzy_direct_match(cls, text_lower: str) -> dict | None:
        """
        Ultra-fast direct keyword & fuzzy regex matching (< 1ms) in both English & Hindi/Hinglish.
        Ensures CLOSE actions take precedence over OPEN actions.
        """
        is_hindi = any(w in text_lower for w in ["khol", "kholo", "kholdo", "chalao", "band", "kar", "kardo", "kaise", "kya", "batao", "sun", "sunao", "aawaz", "gaana", "badhao", "ghatao", "chamak"])

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

        # 1. Termination (English & Hindi)
        if any(w in text_lower for w in ["terminate the system", "terminate system", "shutdown system", "exit system", "system band kardo", "band kar do", "alvida friday"]):
            reply = "System band kar rahi hoon. Alvida sir." if is_hindi else "Terminating system. Goodbye sir."
            return {
                "action": "terminate_system",
                "params": {},
                "spoken_reply": reply
            }

        # 2. CLOSE App Intent (Checked BEFORE Open to prevent "closing spotify" from triggering open!)
        is_close_intent = any(w in text_lower for w in ["close", "quit", "exit", "kill", "stop", "band", "hatao", "closing"])
        if is_close_intent:
            for app_key, app_val in app_map.items():
                if app_key in text_lower:
                    reply = f"{app_val} band kar diya." if is_hindi else f"Closing {app_val}."
                    return {
                        "action": "close_app",
                        "params": {"app_name": app_val},
                        "spoken_reply": reply
                    }

        # 3. Brightness Controls (English & Hindi)
        if "brightness" in text_lower or "chamak" in text_lower or "screen light" in text_lower:
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                level = int(numbers[0])
            elif any(w in text_lower for w in ["full", "max", "maximum", "poori", "100"]):
                level = 100
            elif any(w in text_lower for w in ["low", "kam", "min", "minimum", "dim"]):
                level = 30
            elif any(w in text_lower for w in ["badhao", "increase", "up"]):
                level = 85
            elif any(w in text_lower for w in ["ghatao", "decrease", "down"]):
                level = 40
            else:
                level = 100

            reply = f"Brightness {level} percent kar di hai." if is_hindi else f"Setting brightness to {level}%."
            return {
                "action": "set_brightness",
                "params": {"level": level},
                "spoken_reply": reply
            }

        # 4. OPEN App Intent (Checked after Close)
        for app_key, app_val in app_map.items():
            pattern = rf'(?:open|launch|start|run|play|khol|kholo|kholdo|chalao|khol do)?\s*(?:the\s+app\s+)?\b{re.escape(app_key)}\b\s*(?:khol\s*do|kholo|chalao|open\s*kardo)?'
            if re.search(pattern, text_lower):
                reply = f"{app_val} khol rahi hoon." if is_hindi else f"Opening {app_val}."
                return {
                    "action": "open_app",
                    "params": {"app_name": app_val},
                    "spoken_reply": reply
                }

        # 5. Web URL Open (English & Hindi)
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
                reply = f"{site_key.capitalize()} browser mein khol rahi hoon." if is_hindi else f"Opening {site_key.capitalize()} in your browser."
                return {
                    "action": "open_url",
                    "params": {"url": domain},
                    "spoken_reply": reply
                }

        if "." in text_lower and any(w in text_lower for w in [".com", ".org", ".io", ".dev", ".ai", "http"]):
            words = text_lower.split()
            url = next((w for w in words if "." in w or w.startswith("http")), words[-1])
            return {
                "action": "open_url",
                "params": {"url": url},
                "spoken_reply": f"Opening {url}."
            }

        # 6. Volume Controls
        if any(w in text_lower for w in ["volume", "sound", "aawaz", "awaaz"]):
            if any(w in text_lower for w in ["mute", "chup", "silent"]):
                reply = "Aawaz band kar di." if is_hindi else "Muting system audio."
                return {"action": "mute_sound", "params": {"mute": True}, "spoken_reply": reply}
            if any(w in text_lower for w in ["unmute", "chalu"]):
                reply = "Aawaz chalu kar di." if is_hindi else "Unmuting system audio."
                return {"action": "mute_sound", "params": {"mute": False}, "spoken_reply": reply}
            
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                level = int(numbers[0])
                reply = f"Volume {level} percent kar diya." if is_hindi else f"Setting volume to {level}%."
                return {"action": "set_volume", "params": {"level": level}, "spoken_reply": reply}
            elif "badhao" in text_lower or "increase" in text_lower:
                return {"action": "set_volume", "params": {"level": 80}, "spoken_reply": "Volume badha diya." if is_hindi else "Increasing volume."}
            elif "kam" in text_lower or "decrease" in text_lower:
                return {"action": "set_volume", "params": {"level": 30}, "spoken_reply": "Volume kam kar diya." if is_hindi else "Decreasing volume."}

        # 7. Media Playback
        if any(w in text_lower for w in ["pause music", "pause song", "pause", "gaana roko", "roko"]):
            return {"action": "media_control", "params": {"action": "pause"}, "spoken_reply": "Gaana rok diya." if is_hindi else "Paused playback."}
        if any(w in text_lower for w in ["play music", "resume music", "play song", "resume", "gaana chalao", "chalao"]):
            return {"action": "media_control", "params": {"action": "play"}, "spoken_reply": "Gaana shuru kar diya." if is_hindi else "Resumed playback."}
        if any(w in text_lower for w in ["next song", "next track", "skip song", "agla gaana", "next gaana"]):
            return {"action": "media_control", "params": {"action": "next"}, "spoken_reply": "Agla gaana play kar rahi hoon." if is_hindi else "Skipping to next track."}

        # 8. Screenshot
        if any(w in text_lower for w in ["screenshot", "screen capture", "screenshot lelo"]):
            return {"action": "take_screenshot", "params": {}, "spoken_reply": "Screenshot le liya." if is_hindi else "Screenshot captured."}

        # 9. Lock screen
        if any(w in text_lower for w in ["lock screen", "lock mac", "lock kardo", "screen lock"]):
            return {"action": "lock_screen", "params": {}, "spoken_reply": "Screen lock kar rahi hoon." if is_hindi else "Locking screen."}

        # 10. Coding mode
        if any(w in text_lower for w in ["coding mode", "start coding", "coding shuru"]):
            return {"action": "coding_mode", "params": {}, "spoken_reply": "Coding mode shuru kar diya hai." if is_hindi else "Coding mode initiated."}

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
                    "temperature": 0.4,
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
        """Process command: execute actions or reply in Hindi/English."""
        text_lower = user_text.lower().strip()

        # Step 1: Filter Fillers / Random Chatter
        if cls._is_random_or_filler(text_lower):
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

        # Conversational answer in Hindi/English
        MemoryDatabase.save_message("user", user_text)
        MemoryDatabase.save_message("friday", llm_response, action="none")

        return {
            "text_response": llm_response,
            "action_executed": "none",
            "result": {}
        }
