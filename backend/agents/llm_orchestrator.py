import json
import re
import sys
import requests
from backend.config.config import settings
from backend.automation.system_automation import SystemAutomation
from backend.memory.database import MemoryDatabase


class LLMOrchestrator:
    """Orchestrates natural language intent parsing, phonetic auto-correction, and direct voice execution."""

    SYSTEM_PROMPT = """You are FRIDAY, an ultra-smart and witty AI desktop assistant like Tony Stark's FRIDAY.

RULES:
1. Speech Auto-Correction: The user input comes from speech-to-text and may contain phonetic errors (e.g. "SIDAY" means "FRIDAY", "kon kon se" means "kaun kaun se"). Auto-correct and understand the intent.
2. Direct Spoken Response ONLY:
   - Output ONLY the concise final spoken sentence.
   - If user says "FRIDAY" or calls your name, say: "Yes sir, I am online and listening."
   - Never output internal thinking, analysis, steps, or markdown asterisks.
3. Language:
   - If user speaks in Hindi/Hinglish, reply in natural conversational Hindi.
   - If user speaks in English, reply in fluent English.
4. OS Actions:
   - If user wants an OS action, output valid JSON: {"action": "<action_name>", "params": {...}, "spoken_reply": "<short reply to speak>"}
   - Supported actions: 
     * Apps: open_app, close_app, coding_mode
     * System: set_volume, mute_sound, set_brightness, lock_screen, take_screenshot, system_info, terminate_system
     * Window Tiling: tile_windows, tile_positions
     * Media & Spotify: media_control, spotify_play (params: {"query": "song name"})
     * Web Search: open_url, browser_search (params: {"engine": "google"|"youtube"|"github", "query": "search query"})
     * File Management: search_file (params: {"filename": "..."}), create_file (params: {"filename": "...", "content": "..."}), create_folder (params: {"folder_name": "..."}), recent_downloads
     * Clipboard: clipboard_get, clipboard_set (params: {"text": "..."}), clipboard_transform (params: {"transformation": "upper"|"lower"|"title"|"strip"|"extract_urls"})
     * Workflows: execute_workflow (params: {"workflow": "meeting_mode"|"focus_mode"|"clean_workspace"})
5. If background noise or random talk, output EXACTLY: SILENT
"""



    @classmethod
    def _is_random_or_filler(cls, text_lower: str) -> bool:
        """Check if input is random chatter, background noise, or filler words."""
        cleaned = re.sub(r'[^\w\s]', '', text_lower).strip()
        fillers = {
            "oh", "okay", "ok", "its okay", "its ok", "oh its okay", "oh its ok",
            "umm", "um", "uh", "yeah", "yes", "no", "nah", "hmm", "hm",
            "are there eight seconds", "testing", "nothing", "nevermind", "nay", "set"
        }
        return cleaned in fillers

    @classmethod
    def _fuzzy_direct_match(cls, text_lower: str) -> dict | None:
        """
        Ultra-fast direct keyword & fuzzy regex matching (< 1ms) in both English & Hindi/Hinglish.
        Ensures CLOSE & TILE actions take precedence over plain OPEN actions.
        """
        is_hindi = any(w in text_lower for w in ["khol", "kholo", "kholdo", "chalao", "band", "kar", "kardo", "kaise", "kya", "batao", "sun", "sunao", "aawaz", "gaana", "badhao", "ghatao", "chamak", "jodo", "sath"])

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
            "notion": "Notion",
            # Devanagari Hindi app names
            "स्पॉटिफाई": "Spotify", "स्पोटिफाई": "Spotify",
            "फोटोस": "Photos", "फ़ोटो": "Photos", "फोटो": "Photos",
            "अप स्टोर": "App Store", "एप स्टोर": "App Store", "ऐप स्टोर": "App Store",
            "नोटेशन": "Notion", "नोशन": "Notion",
            "क्रोम": "Google Chrome", "गूगल क्रोम": "Google Chrome",
            "वीएस कोड": "Visual Studio Code", "कोड": "Visual Studio Code",
            "टर्मिनल": "Terminal", "सफारी": "Safari", "कैलकुलेटर": "Calculator"
        }

        # 1. Termination & Memory Clear (English & Hindi)
        if any(w in text_lower for w in ["terminate the system", "terminate system", "shutdown system", "exit system", "system band kardo", "band kar do", "alvida friday", "terminate", "सिस्टम बंद"]):
            reply = "System band kar rahi hoon. Alvida sir." if is_hindi else "Terminating system. Goodbye sir."
            return {
                "action": "terminate_system",
                "params": {},
                "spoken_reply": reply
            }

        if any(w in text_lower for w in ["clear history", "clear memory", "delete history", "memory clear kardo", "history saaf kardo", "forget history"]):
            return {
                "action": "clear_history",
                "params": {},
                "spoken_reply": "Saari purani history aur memory clear kar di hai." if is_hindi else "Cleared all conversation history and memory."
            }


        # 2. Positional Tiling Intent (e.g. "chrome left me dalo, vs code top right me, terminal bottom right me")
        has_pos_keyword = any(w in text_lower for w in [
            "top right", "top left", "bottom right", "bottom left", "left me", "right me", "left side", "right side", "upar", "neeche",
            "टॉप लेफ्ट", "टॉप राइट", "टॉप राईट", "बॉटम लेफ्ट", "बॉटम राइट", "बॉटम राईट", "लेफ्ट में", "राइट में", "ऊपर", "नीचे", "डालो", "टाइल"
        ])
        if has_pos_keyword:
            slots = {}
            for app_key, app_val in app_map.items():
                if app_key in text_lower:
                    idx = text_lower.find(app_key)
                    # Look at context around the app name
                    context = text_lower[max(0, idx - 30):min(len(text_lower), idx + len(app_key) + 30)]
                    if any(k in context for k in ["top right", "top right me", "upar right", "टॉप राइट", "टॉप राईट", "ऊपर राइट"]):
                        slots["top_right"] = app_val
                    elif any(k in context for k in ["top left", "top left me", "upar left", "टॉप लेफ्ट", "ऊपर लेफ्ट"]):
                        slots["top_left"] = app_val
                    elif any(k in context for k in ["bottom right", "bottom right me", "neeche right", "बॉटम राइट", "बॉटम राईट", "नीचे राइट"]):
                        slots["bottom_right"] = app_val
                    elif any(k in context for k in ["bottom left", "bottom left me", "neeche left", "बॉटम लेफ्ट", "नीचे लेफ्ट"]):
                        slots["bottom_left"] = app_val
                    elif any(k in context for k in ["left", "bayein", "लेफ्ट", "बाएं"]):
                        slots["left"] = app_val
                    elif any(k in context for k in ["right", "dayein", "राइट", "दाईं"]):
                        slots["right"] = app_val

            if slots and len(slots) >= 2:
                spoken = "Aapke bataye hisaab se windows tile kar diye hain." if is_hindi else "Positionally tiled your applications."
                return {
                    "action": "tile_positions",
                    "params": {"positions": slots},
                    "spoken_reply": spoken
                }


        # 3. Plain Multi-App Tiling (e.g. "tile chrome and vs code", "tile terminal spotify chrome", "split screen vs code and terminal")
        if any(w in text_lower for w in ["tile", "split screen", "side by side", "tile karo", "screen split", "arrange windows"]):
            found_apps = []
            for app_key, app_val in app_map.items():
                if app_key in text_lower:
                    if app_val not in found_apps:
                        found_apps.append(app_val)

            if found_apps:
                selected_apps = found_apps[:4]
                app_names_str = ", ".join(selected_apps)
                reply = f"{app_names_str} ko screen par tile kar diya hai." if is_hindi else f"Tiling {app_names_str} on your screen."
                return {
                    "action": "tile_windows",
                    "params": {"apps": selected_apps},
                    "spoken_reply": reply
                }


        # 3. CLOSE App Intent (Checked BEFORE Open)
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

        # 4. Volume & Mute/Unmute Controls (English & Hindi)
        if any(w in text_lower for w in ["volume", "sound", "aawaz", "awaaz", "mute", "unmute"]):
            if any(w in text_lower for w in ["unmute", "chalu"]):
                reply = "Aawaz chalu kar di." if is_hindi else "Unmuting system audio."
                return {"action": "mute_sound", "params": {"mute": False}, "spoken_reply": reply}
            if any(w in text_lower for w in ["mute", "chup", "silent"]):
                reply = "Aawaz band kar di." if is_hindi else "Muting system audio."
                return {"action": "mute_sound", "params": {"mute": True}, "spoken_reply": reply}
            
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                level = int(numbers[0])
                reply = f"Volume {level} percent kar diya." if is_hindi else f"Setting volume to {level}%."
                return {"action": "set_volume", "params": {"level": level}, "spoken_reply": reply}
            elif "badhao" in text_lower or "increase" in text_lower:
                return {"action": "set_volume", "params": {"level": 80}, "spoken_reply": "Volume badha diya." if is_hindi else "Increasing volume."}
            elif "kam" in text_lower or "decrease" in text_lower:
                return {"action": "set_volume", "params": {"level": 30}, "spoken_reply": "Volume kam kar diya." if is_hindi else "Decreasing volume."}


        # 4. Multi-Step Chained Workflows
        if any(w in text_lower for w in ["meeting mode", "meeting routine", "start meeting"]):
            return {
                "action": "execute_workflow",
                "params": {"workflow": "meeting_mode"},
                "spoken_reply": "Meeting mode activate kar diya. Mic mute aur meeting windows tile kar diye hain." if is_hindi else "Meeting mode activated. Mic muted and workspace prepared."
            }

        if any(w in text_lower for w in ["focus mode", "deep work", "study mode", "padhai mode"]):
            return {
                "action": "execute_workflow",
                "params": {"workflow": "focus_mode"},
                "spoken_reply": "Focus mode shuru ho gaya. Distractions band aur workspace ready hai." if is_hindi else "Focus mode initiated. Distractions closed and deep work workspace ready."
            }

        # 5. File & Folder Management (Checked before media/open verbs)
        if any(text_lower.startswith(p) for p in ["create folder ", "make folder ", "folder banao ", "naya folder banao "]):
            folder_name = re.sub(r'^(create folder|make folder|folder banao|naya folder banao)\s*', '', text_lower).strip()
            folder_name = folder_name.replace("named", "").replace("naam se", "").strip() or "New Folder"
            return {
                "action": "create_folder",
                "params": {"folder_name": folder_name},
                "spoken_reply": f"Desktop par '{folder_name}' folder bana diya hai." if is_hindi else f"Created folder '{folder_name}' on Desktop."
            }

        if any(text_lower.startswith(p) for p in ["create file ", "make file ", "file banao ", "naya file banao "]):
            fname = re.sub(r'^(create file|make file|file banao|naya file banao)\s*', '', text_lower).strip()
            fname = fname.replace("named", "").replace("naam se", "").strip() or "new_file.txt"
            if not "." in fname:
                fname += ".txt"
            return {
                "action": "create_file",
                "params": {"filename": fname, "content": ""},
                "spoken_reply": f"Desktop par '{fname}' file bana di hai." if is_hindi else f"Created file '{fname}' on Desktop."
            }

        if any(text_lower.startswith(p) for p in ["delete file ", "remove file ", "file delete kardo ", "file hatao "]):
            fname = re.sub(r'^(delete file|remove file|file delete kardo|file hatao)\s*', '', text_lower).strip()
            if fname:
                return {
                    "action": "delete_file",
                    "params": {"filename": fname},
                    "spoken_reply": f"'{fname}' ko safe trash me daal diya hai." if is_hindi else f"Safely moved '{fname}' to Trash."
                }

        if any(w in text_lower for w in ["organize downloads", "clean downloads", "downloads organize kardo", "organize my files"]):
            return {
                "action": "organize_downloads",
                "params": {},
                "spoken_reply": "Downloads folder ko categories me organize kar diya hai." if is_hindi else "Organized files in Downloads into categories."
            }

        if any(text_lower.startswith(p) for p in ["search file", "find file", "file dhundo", "file search"]):
            fname = re.sub(r'^(search file|find file|file dhundo|file search)\s*', '', text_lower).strip()
            if fname:
                return {
                    "action": "search_file",
                    "params": {"filename": fname},
                    "spoken_reply": f"'{fname}' file search kar rahi hoon." if is_hindi else f"Searching for file '{fname}'."
                }

        if any(w in text_lower for w in ["recent downloads", "latest downloads", "downloads dikhao"]):
            return {
                "action": "recent_downloads",
                "params": {"count": 5},
                "spoken_reply": "Recent downloads list kar rahi hoon." if is_hindi else "Listing recent downloads."
            }



        # 6. Deep App Playback & Search (Spotify, YouTube, Google)
        if any(text_lower.startswith(p) for p in ["play ", "spotify play ", "spotify par bajao ", "gaana bajao "]):
            song_name = re.sub(r'^(play|spotify play|spotify par bajao|gaana bajao)\s+', '', text_lower).strip()
            song_name = re.sub(r'\b(on spotify|spotify par)\b', '', song_name).strip()
            if song_name and song_name not in ["music", "song", "video"]:
                return {
                    "action": "spotify_play",
                    "params": {"query": song_name},
                    "spoken_reply": f"Spotify par '{song_name}' play kar rahi hoon." if is_hindi else f"Playing '{song_name}' on Spotify."
                }

        if "search on youtube" in text_lower or "youtube par search" in text_lower or text_lower.startswith("youtube search "):
            query = re.sub(r'.*(search on youtube|youtube par search|youtube search)\s*', '', text_lower).strip()
            if query:
                return {
                    "action": "browser_search",
                    "params": {"engine": "youtube", "query": query},
                    "spoken_reply": f"YouTube par '{query}' search kar rahi hoon." if is_hindi else f"Searching for '{query}' on YouTube."
                }

        if "search on google" in text_lower or "google search" in text_lower or text_lower.startswith("google search "):
            query = re.sub(r'.*(search on google|google search)\s*', '', text_lower).strip()
            if query:
                return {
                    "action": "browser_search",
                    "params": {"engine": "google", "query": query},
                    "spoken_reply": f"Google par '{query}' search kar rahi hoon." if is_hindi else f"Searching for '{query}' on Google."
                }

        # 7. Brightness Controls (English & Hindi)
        if any(w in text_lower for w in ["brightness", "riteness", "chamak", "screen light", "light"]):
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

        # 8. OPEN App Intent (Requires explicit open verb or standalone app name)
        open_verbs = ["open", "launch", "start", "run", "khol", "kholo", "kholdo", "chalao", "khol do"]
        has_open_verb = any(v in text_lower for v in open_verbs)
        for app_key, app_val in app_map.items():
            if has_open_verb:
                if re.search(rf'\b{re.escape(app_key)}\b', text_lower):
                    reply = f"{app_val} khol rahi hoon." if is_hindi else f"Opening {app_val}."
                    return {
                        "action": "open_app",
                        "params": {"app_name": app_val},
                        "spoken_reply": reply
                    }
            elif text_lower.strip() in [app_key, f"the {app_key}", f"{app_key} app"]:
                reply = f"{app_val} khol rahi hoon." if is_hindi else f"Opening {app_val}."
                return {
                    "action": "open_app",
                    "params": {"app_name": app_val},
                    "spoken_reply": reply
                }


        # 9. Web URL Open
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
            if site_key in text_lower and not ("search on" in text_lower or "search" in text_lower):
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

        # 7. Volume Controls
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

        # 8. Media Playback
        if any(w in text_lower for w in ["pause music", "pause song", "pause", "gaana roko", "roko"]):
            return {"action": "media_control", "params": {"action": "pause"}, "spoken_reply": "Gaana rok diya." if is_hindi else "Paused playback."}
        if any(w in text_lower for w in ["play music", "resume music", "play song", "resume", "gaana chalao", "chalao"]):
            return {"action": "media_control", "params": {"action": "play"}, "spoken_reply": "Gaana shuru kar diya." if is_hindi else "Resumed playback."}
        if any(w in text_lower for w in ["next song", "next track", "skip song", "agla gaana", "next gaana"]):
            return {"action": "media_control", "params": {"action": "next"}, "spoken_reply": "Agla gaana play kar rahi hoon." if is_hindi else "Skipping to next track."}

        # 9. Screenshot
        if any(w in text_lower for w in ["screenshot", "screen capture", "screenshot lelo"]):
            return {"action": "take_screenshot", "params": {}, "spoken_reply": "Screenshot le liya." if is_hindi else "Screenshot captured."}

        # 10. Lock screen
        if any(w in text_lower for w in ["lock screen", "lock mac", "lock kardo", "screen lock"]):
            return {"action": "lock_screen", "params": {}, "spoken_reply": "Screen lock kar rahi hoon." if is_hindi else "Locking screen."}

        # 11. Coding mode (Left 50%: VS Code | Top-Right 25%: Terminal | Bottom-Right 25%: GitHub Browser)
        if any(w in text_lower for w in ["coding mode", "start coding", "coding shuru", "coding", "code mode"]):
            return {
                "action": "coding_mode",
                "params": {},
                "spoken_reply": "Coding mode shuru kar diya hai. VS Code left me, Terminal top right me, aur GitHub bottom right me tile kar diye hain." if is_hindi else "Coding mode initiated. VS Code on left, Terminal top-right, and GitHub bottom-right tiled."
            }

        # 12. Clipboard operations
        if text_lower.startswith("copy ") or text_lower.startswith("clipboard copy "):
            clip_text = text_lower.split(" ", 1)[1].strip() if " " in text_lower else ""
            return {
                "action": "clipboard_set",
                "params": {"text": clip_text},
                "spoken_reply": f"'{clip_text}' clipboard par copy kar diya." if is_hindi else f"Copied '{clip_text}' to clipboard."
            }

        if any(w in text_lower for w in ["read clipboard", "clipboard read", "what is on clipboard", "paste", "clipboard par kya hai"]):
            return {
                "action": "clipboard_get",
                "params": {},
                "spoken_reply": "Clipboard content padh rahi hoon." if is_hindi else "Reading clipboard content."
            }

        if any(w in text_lower for w in ["make clipboard uppercase", "clipboard uppercase", "clipboard bada kardo", "uppercase clipboard"]):
            return {
                "action": "clipboard_transform",
                "params": {"transformation": "upper"},
                "spoken_reply": "Clipboard text uppercase kar diya." if is_hindi else "Converted clipboard text to uppercase."
            }

        if any(w in text_lower for w in ["make clipboard lowercase", "clipboard lowercase", "lowercase clipboard"]):
            return {
                "action": "clipboard_transform",
                "params": {"transformation": "lower"},
                "spoken_reply": "Clipboard text lowercase kar diya." if is_hindi else "Converted clipboard text to lowercase."
            }

        # 13. Deep App Playback & Search (Spotify, YouTube, Google)
        if any(text_lower.startswith(p) for p in ["play ", "spotify play ", "spotify par bajao ", "gaana bajao "]):
            song_name = re.sub(r'^(play|spotify play|spotify par bajao|gaana bajao)\s+', '', text_lower).strip()
            song_name = re.sub(r'\b(on spotify|spotify par)\b', '', song_name).strip()
            if song_name:
                return {
                    "action": "spotify_play",
                    "params": {"query": song_name},
                    "spoken_reply": f"Spotify par '{song_name}' play kar rahi hoon." if is_hindi else f"Playing '{song_name}' on Spotify."
                }

        if "search on youtube" in text_lower or "youtube par search" in text_lower:
            query = re.sub(r'.*(search on youtube|youtube par search)\s*', '', text_lower).strip()
            if query:
                return {
                    "action": "browser_search",
                    "params": {"engine": "youtube", "query": query},
                    "spoken_reply": f"YouTube par '{query}' search kar rahi hoon." if is_hindi else f"Searching for '{query}' on YouTube."
                }

        if "search on google" in text_lower or "google search" in text_lower:
            query = re.sub(r'.*(search on google|google search|search)\s*', '', text_lower).strip()
            if query:
                return {
                    "action": "browser_search",
                    "params": {"engine": "google", "query": query},
                    "spoken_reply": f"Google par '{query}' search kar rahi hoon." if is_hindi else f"Searching for '{query}' on Google."
                }

        # 14. Multi-Step Chained Workflows
        if any(w in text_lower for w in ["meeting mode", "meeting routine", "start meeting"]):
            return {
                "action": "execute_workflow",
                "params": {"workflow": "meeting_mode"},
                "spoken_reply": "Meeting mode activate kar diya. Mic mute aur meeting windows tile kar diye hain." if is_hindi else "Meeting mode activated. Mic muted and workspace prepared."
            }

        if any(w in text_lower for w in ["focus mode", "deep work", "study mode", "padhai mode"]):
            return {
                "action": "execute_workflow",
                "params": {"workflow": "focus_mode"},
                "spoken_reply": "Focus mode shuru ho gaya. Distractions band aur workspace ready hai." if is_hindi else "Focus mode initiated. Distractions closed and deep work workspace ready."
            }

        # 15. File Management
        if any(text_lower.startswith(p) for p in ["search file", "find file", "file dhundo", "file search"]):
            fname = re.sub(r'^(search file|find file|file dhundo|file search)\s*', '', text_lower).strip()
            if fname:
                return {
                    "action": "search_file",
                    "params": {"filename": fname},
                    "spoken_reply": f"'{fname}' file search kar rahi hoon." if is_hindi else f"Searching for file '{fname}'."
                }

        if any(w in text_lower for w in ["recent downloads", "latest downloads", "downloads dikhao"]):
            return {
                "action": "recent_downloads",
                "params": {"count": 5},
                "spoken_reply": "Recent downloads list kar rahi hoon." if is_hindi else "Listing recent downloads."
            }

        return None



    @classmethod
    def _call_groq_with_fallbacks(cls, user_text: str) -> str:
        """Call Groq API and cleanly strip any model thought artifacts (<think>...</think>)."""
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
                    "max_tokens": 150
                }
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    
                    # Robust filter: strip any <think> tags (closed or open)
                    if "<think>" in content:
                        if "</think>" in content:
                            content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                        else:
                            content = re.sub(r'<think>[\s\S]*', '', content).strip()
                    
                    # Clean out markdown formatting
                    content = content.replace("**", "").replace("`", "").replace("#", "").strip()

                    if content:
                        print(f"[LLM Groq ({model_name}) Answer]: '{content}'")
                        return content
            except Exception as e:
                print(f"[Groq Error ({model_name})]: {e}")

        return ""

    @classmethod
    def process_command(cls, user_text: str) -> dict:
        """Process command: execute actions or reply with direct, clean answers in Hindi/English."""
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
                # 1. Open GitHub URL in Browser
                SystemAutomation.execute_intent("open_url", {"url": "github.com"})
                # 2. Tile: [1] VS Code (Left 50%), [2] Terminal (Top-Right 25%), [3] Browser/Chrome/Safari (Bottom-Right 25%)
                browser_app = "Google Chrome" if sys.platform == "darwin" else "chrome"
                action_res = SystemAutomation.execute_intent("tile_windows", {"apps": ["Visual Studio Code", "Terminal", browser_app]})
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
                "parsed_params": params,
                "result": action_res
            }

        # Step 3: Groq LLM Intelligent Processing (With speech auto-correction & direct answers)
        llm_response = cls._call_groq_with_fallbacks(user_text)

        # If LLM classified this as random chatter
        if not llm_response or llm_response.strip().upper() == "SILENT":
            return {
                "text_response": "",
                "action_executed": "none",
                "parsed_params": {},
                "result": {"ignored": True}
            }

        # Check if Groq returned a JSON action
        if llm_response.startswith("{") and "action" in llm_response:
            try:
                parsed = json.loads(llm_response)
                action = parsed.get("action", "none")
                params = parsed.get("params", {})
                spoken = parsed.get("spoken_reply", "")

                if action == "coding_mode":
                    action_res = SystemAutomation.execute_intent("tile_windows", {"apps": ["Visual Studio Code", "Terminal"]})
                else:
                    action_res = SystemAutomation.execute_intent(action, params)

                MemoryDatabase.save_message("user", user_text)
                if spoken:
                    MemoryDatabase.save_message("friday", spoken, action=action)
                return {
                    "text_response": spoken,
                    "action_executed": action,
                    "parsed_params": params,
                    "result": action_res
                }
            except Exception:
                pass

        # Conversational direct answer in Hindi/English
        MemoryDatabase.save_message("user", user_text)
        MemoryDatabase.save_message("friday", llm_response, action="none")

        return {
            "text_response": llm_response,
            "action_executed": "none",
            "parsed_params": {},
            "result": {}
        }

