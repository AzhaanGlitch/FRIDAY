import os
import subprocess
import sys
import platform

class MacAutomation:
    """Automation adapter for macOS operations."""

    @staticmethod
    def is_macos() -> bool:
        return sys.platform == "darwin"

    @classmethod
    def open_application(cls, app_name: str) -> dict:
        """Open an application on macOS using `open -a`."""
        if not cls.is_macos():
            return {"success": False, "error": "Not running on macOS"}
        try:
            # Clean app name
            clean_name = app_name.strip()
            result = subprocess.run(["open", "-a", clean_name], capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "message": f"Successfully launched {clean_name}"}
            else:
                return {"success": False, "error": result.stderr or f"Application '{clean_name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
    def set_volume(cls, level_percent: int) -> dict:
        """Set system volume (0-100)."""
        level = max(0, min(100, level_percent))
        script = f"set volume output volume {level}"
        res = cls.run_applescript(script)
        if res.get("success"):
            return {"success": True, "message": f"Volume set to {level}%"}
        return res

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
                "error": res.stderr.strip() or "Screen recording permission required in macOS System Settings > Privacy & Security > Screen Recording."
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

