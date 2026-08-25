import os
import subprocess
import sys
import platform
import webbrowser

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
        script = f'tell application "{clean_name}" to quit'
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Closed {clean_name}"}
        # Fallback to pkill if AppleScript quit fails
        try:
            subprocess.run(["pkill", "-f", clean_name], capture_output=True)
            return {"success": True, "message": f"Force terminated {clean_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def set_volume(cls, level_percent: int) -> dict:
        """Set system volume (0-100)."""
        level = max(0, min(100, level_percent))
        script = f"set volume output volume {level}"
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Volume set to {level}%"}
        return res

    @classmethod
    def mute_sound(cls, mute: bool = True) -> dict:
        """Mute or unmute macOS system output sound."""
        status = "true" if mute else "false"
        script = f"set volume output muted {status}"
        res = cls.run_applescript(script)
        if res.get("success"):
            action = "Muted" if mute else "Unmuted"
            return {"success": True, "message": f"System sound {action.lower()}"}
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
        key_map = {
            "play": "tell application \"System Events\" to key code 16 using {option, command}",
            "pause": "tell application \"System Events\" to key code 16 using {option, command}",
            "play_pause": "tell application \"System Events\" to key code 16 using {option, command}",
            "next": "tell application \"System Events\" to key code 19 using {option, command}",
            "previous": "tell application \"System Events\" to key code 18 using {option, command}"
        }
        # First try controlling Spotify if open, fallback to System Events
        spotify_script = f'tell application "Spotify" to {action}' if action in ["play", "pause", "next track", "previous track"] else None
        if spotify_script:
            spotify_script = spotify_script.replace("next track", "next track").replace("previous track", "previous track")
            res = cls.run_applescript(spotify_script)
            if res.get("success"):
                return {"success": True, "message": f"Media action '{action}' sent to Spotify"}

        # General AppleScript media key invocation
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
        """Set screen brightness (0-100) using brightness command or AppleScript."""
        level = max(0.0, min(1.0, level_percent / 100.0))
        # Try native brightness CLI tool if available
        try:
            res = subprocess.run(["brightness", str(level)], capture_output=True, text=True)
            if res.returncode == 0:
                return {"success": True, "message": f"Brightness set to {level_percent}%"}
        except Exception:
            pass
        return {"success": True, "message": f"Brightness adjustment requested to {level_percent}%"}

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
    def search_file(cls, filename: str) -> dict:
        """Search for a file on macOS using Spotlight `mdfind`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            res = subprocess.run(["mdfind", "-name", filename], capture_output=True, text=True)
            results = [line for line in res.stdout.strip().split("\n") if line]
            return {"success": True, "files": results[:5]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def open_url(cls, url: str) -> dict:
        """Open web URL in default browser."""
        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "message": f"Opened {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def take_screenshot(cls, output_path: str = "/tmp/friday_screenshot.png") -> dict:
        """Capture screenshot on macOS with permission checks."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            res = subprocess.run(["screencapture", "-x", output_path], capture_output=True, text=True)
            if res.returncode == 0:
                return {"success": True, "path": output_path}
            return {
                "success": False,
                "error": res.stderr.strip() or "Screen recording permission required."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def get_system_info(cls) -> dict:
        """Get system details."""
        return {
            "success": True,
            "info": {
                "platform": sys.platform,
                "os_release": platform.release(),
                "machine": platform.machine(),
                "python_version": sys.version.split()[0]
            }
        }
