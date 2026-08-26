import sys
import os
import subprocess
import webbrowser
import glob
from difflib import SequenceMatcher

class WinAutomation:
    """Advanced automation adapter for Windows operations using PowerShell & CMD."""

    @staticmethod
    def is_windows() -> bool:
        return sys.platform == "win32"

    # Cache of discovered Start Menu shortcuts: {lowercase_name: full_path_to_lnk}
    _shortcut_cache = None

    # Built-in system apps that are always on PATH or have known locations
    _BUILTIN_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "wordpad": "wordpad.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "control panel": "control.exe",
        "snipping tool": "SnippingTool.exe",
        "regedit": "regedit.exe",
        "settings": "ms-settings:",
        "system settings": "ms-settings:",
        "store": "ms-windows-store:",
        "microsoft store": "ms-windows-store:",
    }

    # Alias map: alternate user names -> canonical shortcut name to search for
    _NAME_ALIASES = {
        "chrome": "google chrome",
        "firefox": "mozilla firefox",
        "edge": "microsoft edge",
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "code": "visual studio code",
        "terminal": "windows terminal",
        "word": "microsoft word",
        "excel": "microsoft excel",
        "powerpoint": "microsoft powerpoint",
        "outlook": "microsoft outlook",
        "teams": "microsoft teams",
        "obs": "obs studio",
    }

    @classmethod
    def _build_shortcut_cache(cls):
        """Scan Start Menu folders for .lnk files and build a name -> path cache."""
        cache = {}
        search_dirs = []

        # User Start Menu
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            search_dirs.append(os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"))

        # All Users Start Menu
        programdata = os.environ.get("ProgramData", "")
        if programdata:
            search_dirs.append(os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs"))

        for search_dir in search_dirs:
            if not os.path.isdir(search_dir):
                continue
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]  # strip .lnk
                        full_path = os.path.join(root, f)
                        cache[name.lower()] = full_path

        cls._shortcut_cache = cache
        return cache

    @classmethod
    def _get_shortcuts(cls):
        """Return the shortcut cache, building it if needed."""
        if cls._shortcut_cache is None:
            cls._build_shortcut_cache()
        return cls._shortcut_cache

    @classmethod
    def _fuzzy_match(cls, query: str, candidates: list, threshold: float = 0.45) -> str | None:
        """Find the best fuzzy match for query among candidates.
        Uses substring matching first, then falls back to SequenceMatcher."""
        query_lower = query.lower()

        # Priority 1: Exact match
        if query_lower in candidates:
            return query_lower

        # Priority 2: Candidate starts with query or query starts with candidate
        for c in candidates:
            if c.startswith(query_lower) or query_lower.startswith(c):
                return c

        # Priority 3: Query is a substring of candidate
        substring_matches = [c for c in candidates if query_lower in c]
        if substring_matches:
            # Return the shortest match (most specific)
            return min(substring_matches, key=len)

        # Priority 4: Candidate is a substring of query
        reverse_matches = [c for c in candidates if c in query_lower]
        if reverse_matches:
            return max(reverse_matches, key=len)

        # Priority 5: Fuzzy ratio matching
        best_match = None
        best_score = 0.0
        for c in candidates:
            score = SequenceMatcher(None, query_lower, c).ratio()
            if score > best_score:
                best_score = score
                best_match = c

        if best_score >= threshold:
            return best_match
        return None

    @classmethod
    def open_application(cls, app_name: str) -> dict:
        """Open an application on Windows using Start Menu shortcut discovery with fuzzy matching."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            clean_name = app_name.strip()
            lookup_key = clean_name.lower()

            # Step 1: Check built-in system apps (always available on PATH)
            builtin = cls._BUILTIN_APPS.get(lookup_key)
            if builtin:
                if builtin.endswith(":"):
                    # URI scheme (ms-settings:, ms-windows-store:, etc.)
                    os.startfile(builtin)
                else:
                    subprocess.Popen(builtin, shell=True)
                return {"success": True, "message": f"Successfully launched {clean_name}"}

            # Step 2: Resolve aliases to canonical names
            canonical = cls._NAME_ALIASES.get(lookup_key, lookup_key)

            # Step 3: Search Start Menu shortcuts with fuzzy matching
            shortcuts = cls._get_shortcuts()
            match = cls._fuzzy_match(canonical, list(shortcuts.keys()))

            if match:
                lnk_path = shortcuts[match]
                os.startfile(lnk_path)
                matched_name = match.title()
                return {"success": True, "message": f"Successfully launched {matched_name}"}

            # Step 4: If alias didn't help, try fuzzy matching on the original input too
            if canonical != lookup_key:
                match = cls._fuzzy_match(lookup_key, list(shortcuts.keys()))
                if match:
                    lnk_path = shortcuts[match]
                    os.startfile(lnk_path)
                    matched_name = match.title()
                    return {"success": True, "message": f"Successfully launched {matched_name}"}

            # Step 5: Rebuild cache and try once more (app might have been installed recently)
            cls._build_shortcut_cache()
            shortcuts = cls._shortcut_cache
            match = cls._fuzzy_match(canonical, list(shortcuts.keys()))
            if not match:
                match = cls._fuzzy_match(lookup_key, list(shortcuts.keys()))
            if match:
                lnk_path = shortcuts[match]
                os.startfile(lnk_path)
                matched_name = match.title()
                return {"success": True, "message": f"Successfully launched {matched_name}"}

            return {"success": False, "error": f"Application '{clean_name}' not found. Available apps can be found in your Start Menu."}
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

    @classmethod
    def tile_windows(cls, app_names: list[str]) -> dict:
        """Tile 1, 2, 3, or 4 windows on Windows desktop using PowerShell Win32 APIs."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            valid_apps = [a.strip() for a in app_names if a.strip()][:4]
            if not valid_apps:
                return {"success": False, "error": "No apps specified to tile"}

            # Launch any app if not running
            for app in valid_apps:
                cls.open_application(app)

            # PowerShell script to resize and position windows using SetWindowPos
            ps_script = f"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinPos {{
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$sw = $screen.Width
$sh = $screen.Height

$apps = @({", ".join([f"'{a}'" for a in valid_apps])})
$count = $apps.Count

for ($i = 0; $i -lt $count; $i++) {{
    $name = $apps[$i]
    $proc = Get-Process | Where-Object {{ $_.MainWindowTitle -and ($_.ProcessName -match $name -or $_.MainWindowTitle -match $name) }} | Select-Object -First 1
    if ($proc) {{
        $hwnd = $proc.MainWindowHandle
        [WinPos]::ShowWindow($hwnd, 9) # SW_RESTORE
        if ($count -eq 1) {{
            [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, 0, 0, $sw, $sh, 0x0040)
        }} elseif ($count -eq 2) {{
            $w = [int]($sw / 2)
            $x = $i * $w
            [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, $x, 0, $w, $sh, 0x0040)
        }} elseif ($count -eq 3) {{
            $halfW = [int]($sw / 2)
            $halfH = [int]($sh / 2)
            if ($i -eq 0) {{
                [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, 0, 0, $halfW, $sh, 0x0040)
            }} elseif ($i -eq 1) {{
                [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, $halfW, 0, $halfW, $halfH, 0x0040)
            }} else {{
                [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, $halfW, $halfH, $halfW, $halfH, 0x0040)
            }}
        }} elseif ($count -ge 4) {{
            $halfW = [int]($sw / 2)
            $halfH = [int]($sh / 2)
            $col = $i % 2
            $row = [Math]::Floor($i / 2)
            $x = $col * $halfW
            $y = $row * $halfH
            [WinPos]::SetWindowPos($hwnd, [IntPtr]::Zero, $x, $y, $halfW, $halfH, 0x0040)
        }}
    }}
}}
"""
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
            return {"success": True, "message": f"Tiled {len(valid_apps)} windows on Windows: {', '.join(valid_apps)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def tile_positions(cls, positions: dict) -> dict:
        """Tile specific named apps into designated positions on Windows screen."""
        if not cls.is_windows():
            return {"success": False, "error": "Not running on Windows"}
        try:
            for app in positions.values():
                if app:
                    cls.open_application(app)

            pos_json = json.dumps(positions)
            ps_script = f"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinPos2 {{
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$sw = $screen.Width
$sh = $screen.Height
$halfW = [int]($sw / 2)
$halfH = [int]($sh / 2)

$positions = ConvertFrom-Json '{pos_json}'

foreach ($prop in $positions.PSObject.Properties) {{
    $slot = $prop.Name
    $name = $prop.Value
    if ($name) {{
        $proc = Get-Process | Where-Object {{ $_.MainWindowTitle -and ($_.ProcessName -match $name -or $_.MainWindowTitle -match $name) }} | Select-Object -First 1
        if ($proc) {{
            $hwnd = $proc.MainWindowHandle
            [WinPos2]::ShowWindow($hwnd, 9)
            if ($slot -eq "left") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, 0, 0, $halfW, $sh, 0x0040)
            }} elseif ($slot -eq "right") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, $halfW, 0, $halfW, $sh, 0x0040)
            }} elseif ($slot -eq "top_left") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, 0, 0, $halfW, $halfH, 0x0040)
            }} elseif ($slot -eq "top_right") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, $halfW, 0, $halfW, $halfH, 0x0040)
            }} elseif ($slot -eq "bottom_left") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, 0, $halfH, $halfW, $halfH, 0x0040)
            }} elseif ($slot -eq "bottom_right") {{
                [WinPos2]::SetWindowPos($hwnd, [IntPtr]::Zero, $halfW, $halfH, $halfW, $halfH, 0x0040)
            }}
        }}
    }}
}}
"""
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
            return {"success": True, "message": "Positionally tiled windows on Windows"}
        except Exception as e:
            return {"success": False, "error": str(e)}


