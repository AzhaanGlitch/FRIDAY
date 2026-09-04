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
        """Search Spotify and trigger playback directly via Spotify URI / deep-link."""
        encoded_query = urllib.parse.quote(query.strip())
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
                # Open Spotify search URI, navigate into results, press Return and explicitly verify play state
                script = f'''
                tell application "Spotify"
                    activate
                    open location "{spotify_uri}"
                    delay 1.0
                    tell application "System Events"
                        key code 36 -- Enter search
                        delay 0.5
                        key code 48 -- Tab into results
                        delay 0.3
                        key code 36 -- Enter on first result (Plays song)
                    end tell
                    delay 0.4
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
