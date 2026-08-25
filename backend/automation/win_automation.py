import sys
import os
import subprocess
import webbrowser

class WinAutomation:
    """Advanced automation adapter for Windows operations using PowerShell & CMD."""

    @staticmethod
    def is_windows() -> bool:
        return sys.platform == "win32"

    @classmethod
    def open_application(cls, app_name: str) -> dict:
        """Open an application on Windows using Start command."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            clean_name = app_name.strip()
            subprocess.run(["cmd.exe", "/c", f"start {clean_name}"], check=True, shell=True)
            return {"success": True, "message": f"Successfully launched {clean_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def close_application(cls, app_name: str) -> dict:
        """Close/terminate a running application on Windows using taskkill."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            clean_name = app_name.strip()
            if not clean_name.endswith(".exe"):
                clean_name += ".exe"
            subprocess.run(["taskkill", "/F", "/IM", clean_name], capture_output=True, text=True)
            return {"success": True, "message": f"Terminated process {clean_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def set_volume(cls, level_percent: int) -> dict:
        """Set system volume on Windows using PowerShell SendKeys."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            level = max(0, min(100, level_percent))
            ps_command = f"$wsh = New-Object -ComObject WScript.Shell; 1..50 | % {{ $wsh.SendKeys([char]174) }}; $steps = [math]::Round({level} / 2); 1..$steps | % {{ $wsh.SendKeys([char]175) }}"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": f"Volume set to {level}%"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def mute_sound(cls, mute: bool = True) -> dict:
        """Mute or unmute Windows master volume."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            ps_command = "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            action = "Muted" if mute else "Unmuted"
            return {"success": True, "message": f"Sound output {action.lower()}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def minimize_all(cls) -> dict:
        """Minimize all open windows on Windows."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            ps_command = "(New-Object -ComObject Shell.Application).MinimizeAll()"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": "Minimized all windows"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def media_control(cls, action: str) -> dict:
        """Control media playback on Windows via WScript SendKeys."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        # Virtual keycodes: Play/Pause = 179, Next = 176, Previous = 177
        char_code = 179
        if action in ["next", "next track"]:
            char_code = 176
        elif action in ["previous", "previous track"]:
            char_code = 177

        try:
            ps_command = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]{char_code})"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": f"Media command '{action}' executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def lock_screen(cls) -> dict:
        """Lock Windows workstation."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return {"success": True, "message": "Screen locked"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def sleep_system(cls) -> dict:
        """Put Windows to sleep/suspend state."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
            return {"success": True, "message": "System put to sleep"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def set_brightness(cls, level_percent: int) -> dict:
        """Set monitor brightness via Windows WMI."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            level = max(0, min(100, level_percent))
            ps_command = f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": f"Brightness set to {level}%"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def clipboard_get(cls) -> dict:
        """Read clipboard content on Windows."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            res = subprocess.run(["powershell", "-Command", "Get-Clipboard"], capture_output=True, text=True)
            return {"success": True, "content": res.stdout.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def clipboard_set(cls, text: str) -> dict:
        """Set clipboard text on Windows."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            ps_command = f"Set-Clipboard -Value '{text}'"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": "Copied text to clipboard"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def search_file(cls, filename: str) -> dict:
        """Search for file on Windows via PowerShell Get-ChildItem."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            ps_command = f"Get-ChildItem -Path $env:USERPROFILE -Recurse -Filter *{filename}* -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName"
            res = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            results = [line for line in res.stdout.strip().split("\r\n") if line]
            return {"success": True, "files": results}
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
    def take_screenshot(cls, output_path: str = "friday_screenshot.png") -> dict:
        """Capture screenshot on Windows using PowerShell Graphics API."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            abs_path = os.path.abspath(output_path)
            ps_command = f"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height; $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); $bmp.Save('{abs_path}'); $g.Dispose(); $bmp.Dispose()"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "path": abs_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
