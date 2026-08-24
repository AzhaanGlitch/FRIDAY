import sys
import os
import subprocess

class WinAutomation:
    """Automation adapter for Windows operations using PowerShell & native tools."""

    @staticmethod
    def is_windows() -> bool:
        return sys.platform == "win32"

    @classmethod
    def open_application(cls, app_name: str) -> dict:
        """Open an application on Windows using Start command or PowerShell."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            clean_name = app_name.strip()
            # Try launching app directly via start shell
            subprocess.run(["cmd.exe", "/c", f"start {clean_name}"], check=True, shell=True)
            return {"success": True, "message": f"Successfully launched {clean_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def set_volume(cls, level_percent: int) -> dict:
        """Set system volume on Windows using PowerShell Audio device API."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            level = max(0, min(100, level_percent))
            # PowerShell command using nircmd fallback or SendKeys audio control
            ps_command = f"$wsh = New-Object -ComObject WScript.Shell; 1..50 | % {{ $wsh.SendKeys([char]174) }}; $steps = [math]::Round({level} / 2); 1..$steps | % {{ $wsh.SendKeys([char]175) }}"
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            return {"success": True, "message": f"Volume adjusted toward {level}%"}
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
