import os
import subprocess
import sys
import platform
import webbrowser
import ctypes
import time

class MacAutomation:
    """Advanced automation adapter for macOS operations."""

    @staticmethod
    def is_macos() -> bool:
        return sys.platform == "darwin"

    @classmethod
    def run_applescript(cls, script: str) -> dict:
        """Run arbitrary AppleScript code."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def open_application(cls, app_name: str) -> dict:
        """Open an application on macOS using `open -a`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            clean_name = app_name.strip()
            result = subprocess.run(["open", "-a", clean_name], capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "message": f"Successfully launched {clean_name}"}
            else:
                return {"success": False, "error": result.stderr or f"Application '{clean_name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def close_application(cls, app_name: str) -> dict:
        """Close/quit a running application on macOS."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        clean_name = app_name.strip()
        
        # 1. Try graceful AppleScript quit
        script = f'tell application "{clean_name}" to quit'
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Closed {clean_name}"}

        # 2. Fallback to pkill
        try:
            subprocess.run(["pkill", "-x", clean_name], capture_output=True)
            subprocess.run(["pkill", "-f", clean_name], capture_output=True)
            return {"success": True, "message": f"Terminated process {clean_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def tile_windows(cls, app_names: list[str]) -> dict:
        """
        Dynamically tile 1, 2, 3, or 4 specified applications on macOS screen:
        - 2 Apps: Side-by-side (50% Left | 50% Right)
        - 3 Apps: 1 Left (50%) + 2 Right (Top-Right 25%, Bottom-Right 25%)
        - 4 Apps: 2x2 Grid (Top-Left, Top-Right, Bottom-Left, Bottom-Right 25% each)
        """
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}

        # Filter and ensure apps are launched
        valid_apps = [a.strip() for a in app_names if a.strip()]
        if not valid_apps:
            return {"success": False, "error": "No apps provided to tile"}

        # Launch any app that isn't running yet
        for app in valid_apps:
            cls.open_application(app)

        time.sleep(0.6)  # Grace period for window handles to initialize

        # Map common friendly app names to macOS process names
        process_alias = {
            "visual studio code": "Code",
            "vs code": "Code",
            "code": "Code",
            "terminal": "Terminal",
            "google chrome": "Google Chrome",
            "chrome": "Google Chrome",
            "safari": "Safari",
            "spotify": "Spotify",
            "finder": "Finder",
            "calculator": "Calculator",
            "slack": "Slack",
            "discord": "Discord",
            "notion": "Notion",
            "notes": "Notes",
            "messages": "Messages"
        }

        resolved_processes = [process_alias.get(a.lower(), a) for a in valid_apps[:4]]
        count = len(resolved_processes)

        script = f'''
tell application "Finder"
    set screenBounds to bounds of window of desktop
    set screenWidth to item 3 of screenBounds
    set screenHeight to item 4 of screenBounds
end tell

set menuOffset to 25
set availHeight to screenHeight - menuOffset

tell application "System Events"
'''
        if count == 1:
            proc = resolved_processes[0]
            script += f'''
    if exists (process "{proc}") then
        tell process "{proc}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{0, menuOffset}}
                set size of window 1 to {{screenWidth, availHeight}}
            end if
        end tell
    end if
'''
        elif count == 2:
            proc1, proc2 = resolved_processes[0], resolved_processes[1]
            script += f'''
    set halfWidth to screenWidth / 2
    if exists (process "{proc1}") then
        tell process "{proc1}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{0, menuOffset}}
                set size of window 1 to {{halfWidth, availHeight}}
            end if
        end tell
    end if
    if exists (process "{proc2}") then
        tell process "{proc2}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{halfWidth, menuOffset}}
                set size of window 1 to {{halfWidth, availHeight}}
            end if
        end tell
    end if
'''
        elif count == 3:
            proc1, proc2, proc3 = resolved_processes[0], resolved_processes[1], resolved_processes[2]
            script += f'''
    set halfWidth to screenWidth / 2
    set halfHeight to availHeight / 2
    if exists (process "{proc1}") then
        tell process "{proc1}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{0, menuOffset}}
                set size of window 1 to {{halfWidth, availHeight}}
            end if
        end tell
    end if
    if exists (process "{proc2}") then
        tell process "{proc2}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{halfWidth, menuOffset}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
    if exists (process "{proc3}") then
        tell process "{proc3}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{halfWidth, menuOffset + halfHeight}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
'''
        elif count >= 4:
            p1, p2, p3, p4 = resolved_processes[0], resolved_processes[1], resolved_processes[2], resolved_processes[3]
            script += f'''
    set halfWidth to screenWidth / 2
    set halfHeight to availHeight / 2
    if exists (process "{p1}") then
        tell process "{p1}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{0, menuOffset}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
    if exists (process "{p2}") then
        tell process "{p2}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{halfWidth, menuOffset}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
    if exists (process "{p3}") then
        tell process "{p3}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{0, menuOffset + halfHeight}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
    if exists (process "{p4}") then
        tell process "{p4}"
            set frontmost to true
            if (count of windows) > 0 then
                set position of window 1 to {{halfWidth, menuOffset + halfHeight}}
                set size of window 1 to {{halfWidth, halfHeight}}
            end if
        end tell
    end if
'''

        script += "\nend tell"
        res = cls.run_applescript(script)
        return {"success": True, "message": f"Tiled {len(resolved_processes)} windows: {', '.join(valid_apps)}", "result": res}

    @classmethod
    def set_volume(cls, level_percent: int) -> dict:
        """Set macOS system master volume (0-100)."""
        valid_level = max(0, min(100, level_percent))
        script = f"set volume output volume {valid_level}"
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Volume set to {valid_level}%"}
        return res

    @classmethod
    def mute_sound(cls, mute: bool = True) -> dict:
        """Mute or unmute macOS system audio."""
        state = "true" if mute else "false"
        script = f"set volume output muted {state}"
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Audio {'muted' if mute else 'unmuted'}"}
        return res

    @classmethod
    def minimize_all(cls) -> dict:
        """Hide/minimize all applications and show desktop."""
        script = 'tell application "Finder" to set visible of every process whose visible is true and name is not "Finder" to false'
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": "Minimized all windows"}
        return res

    @classmethod
    def media_control(cls, action: str) -> dict:
        """Control media playback (play, pause, next, previous)."""
        if action in ["play", "pause", "next", "previous"]:
            spotify_script = f'tell application "Spotify" to {action}'
            res = cls.run_applescript(spotify_script)
            if res.get("success"):
                return {"success": True, "message": f"Media action '{action}' sent to Spotify"}

        key_map = {
            "play": "tell application \"System Events\" to key code 16 using {option, command}",
            "pause": "tell application \"System Events\" to key code 16 using {option, command}",
            "next": "tell application \"System Events\" to key code 19 using {option, command}",
            "previous": "tell application \"System Events\" to key code 18 using {option, command}"
        }
        script = key_map.get(action.lower(), f'tell application "System Events" to key code 16')
        res = cls.run_applescript(script)
        return {"success": True, "message": f"Executed media command: {action}"}

    @classmethod
    def lock_screen(cls) -> dict:
        """Lock macOS user screen."""
        script = 'tell application "System Events" to keystroke "q" using {control, command}'
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": "Screen locked"}
        return res

    @classmethod
    def sleep_system(cls) -> dict:
        """Put macOS to sleep."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            subprocess.run(["pmset", "sleepnow"], check=True)
            return {"success": True, "message": "System put to sleep"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def set_brightness(cls, level_percent: int) -> dict:
        """Set screen brightness (0-100) using native Apple CoreDisplay framework API."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}

        level = max(0.0, min(1.0, level_percent / 100.0))
        try:
            core_display = ctypes.CDLL('/System/Library/Frameworks/CoreDisplay.framework/CoreDisplay')
            core_display.CoreDisplay_Display_SetUserBrightness.argtypes = [ctypes.c_uint32, ctypes.c_double]
            core_display.CoreDisplay_Display_SetUserBrightness(1, float(level))
            return {"success": True, "message": f"Brightness set to {level_percent}%"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def clipboard_get(cls) -> dict:
        """Read current text from clipboard using `pbpaste`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True)
            return {"success": True, "content": res.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def clipboard_set(cls, text: str) -> dict:
        """Write text to clipboard using `pbcopy`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return {"success": True, "message": "Copied text to clipboard"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def search_files(cls, filename: str, search_path: str = None) -> dict:
        """Search files using macOS `mdfind` Spotlight indexing."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            cmd = ["mdfind", f"kMDItemFSName == '*{filename}*'c"]
            if search_path:
                cmd.extend(["-onlyin", search_path])
            res = subprocess.run(cmd, capture_output=True, text=True)
            files = [f for f in res.stdout.strip().split("\n") if f]
            return {"success": True, "files": files[:15]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def open_url(cls, url: str) -> dict:
        """Open a URL in user's default macOS browser."""
        clean_url = url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = f"https://{clean_url}"
        try:
            subprocess.run(["open", clean_url], capture_output=True)
            return {"success": True, "message": f"Opened {clean_url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def take_screenshot(cls, output_path: str = None) -> dict:
        """Take screenshot using macOS native `screencapture`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        if not output_path:
            import tempfile
            output_path = os.path.join(tempfile.gettempdir(), f"friday_screenshot_{int(time.time())}.png")
        try:
            subprocess.run(["screencapture", "-x", output_path], check=True)
            return {"success": True, "path": output_path, "message": f"Screenshot saved to {output_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
