import sys
import subprocess
import urllib.parse
from backend.automation.mac_automation import MacAutomation
from backend.automation.win_automation import WinAutomation

class SpotifyController:
    """
    Application-Specific Deep Controller for Spotify (macOS & Windows).
    Supports song searching, direct URI playback, and media state management.
    """

    @classmethod
    def search_and_play(cls, query: str) -> dict:
        # Resolve exact song and artist to guarantee Top Result matches a track (not podcast or repeat button)
        search_term = query.strip()
        try:
            import urllib.request
            import json
            meta_url = f"https://itunes.apple.com/search?term={urllib.parse.quote(search_term)}&entity=song&limit=1"
            req = urllib.request.Request(meta_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode())
                if data.get("results"):
                    item = data["results"][0]
                    t_name = item.get("trackName")
                    a_name = item.get("artistName")
                    if t_name and a_name:
                        search_term = f"{t_name} {a_name}"
        except Exception:
            pass

        encoded_query = urllib.parse.quote(search_term)
        is_mac = sys.platform == "darwin"
        is_win = sys.platform == "win32"

        # 1. Launch Spotify app
        if is_mac:
            MacAutomation.open_application("Spotify")
        else:
            WinAutomation.open_application("Spotify")

        # 2. Open Spotify Search URI and immediately trigger play
        spotify_uri = f"spotify:search:{encoded_query}"
        try:
            if is_mac:
                # Keystroke sequence:
                # 1. Escape (closes any open queue, flyout, or side panel)
                # 2. Cmd+F (explicitly focuses search field)
                # 3. Enter (commits search)
                # 4. Tab 1 & Tab 2 (navigates into top result track row)
                # 5. Enter (triggers track playback directly)
                script = f'''
                tell application "Spotify"
                    activate
                    open location "{spotify_uri}"
                end tell
                delay 1.0
                tell application "System Events"
                    tell process "Spotify"
                        key code 53 -- Escape
                        delay 0.3
                        keystroke "f" using command down -- Focus search
                        delay 0.3
                        key code 36 -- Enter
                        delay 0.5
                        key code 48 -- Tab 1
                        delay 0.2
                        key code 48 -- Tab 2
                        delay 0.2
                        key code 36 -- Enter on track
                    end tell
                end tell
                delay 0.5
                tell application "Spotify"
                    if player state is not playing then
                        play
                    end if
                end tell
                '''
                MacAutomation.run_applescript(script)
            elif is_win:
                subprocess.run(["cmd", "/c", f"start {spotify_uri}"], timeout=3)
                import time
                time.sleep(1.0)
                # On Windows, send Enter and Tab -> Enter to play top searched song
                ps_script = '''
                $wshell = New-Object -ComObject wscript.shell;
                $wshell.AppActivate('Spotify');
                Start-Sleep -Milliseconds 800;
                $wshell.SendKeys('{ENTER}');
                Start-Sleep -Milliseconds 400;
                $wshell.SendKeys('{TAB}');
                Start-Sleep -Milliseconds 300;
                $wshell.SendKeys('{ENTER}');
                '''
                subprocess.run(["powershell", "-c", ps_script], timeout=3)



            return {
                "success": True,
                "query": query,
                "message": f"Playing '{query}' on Spotify"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


    @classmethod
    def control(cls, action: str) -> dict:
        """Control Spotify playback directly (play, pause, next, prev)."""
        is_mac = sys.platform == "darwin"
        if is_mac:
            script_map = {
                "play": 'tell application "Spotify" to play',
                "pause": 'tell application "Spotify" to pause',
                "playpause": 'tell application "Spotify" to playpause',
                "next": 'tell application "Spotify" to next track',
                "previous": 'tell application "Spotify" to previous track'
            }
            script = script_map.get(action.lower(), 'tell application "Spotify" to playpause')
            return MacAutomation.run_applescript(script)
        else:
            return WinAutomation.media_control(action)
