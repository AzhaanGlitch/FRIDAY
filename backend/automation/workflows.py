import sys
import time
from backend.automation.mac_automation import MacAutomation
from backend.automation.win_automation import WinAutomation

class MultiStepWorkflows:
    """
    Chained multi-step automated workflows (Meeting Mode, Focus Mode, Presentation Mode).
    """

    @classmethod
    def execute_workflow(cls, workflow_name: str) -> dict:
        """Execute a coordinated multi-step routine."""
        name = workflow_name.lower().strip()
        is_mac = sys.platform == "darwin"
        is_win = sys.platform == "win32"

        # 1. Meeting Mode: Mute audio + open Zoom/Meet + tile Notes
        if "meeting" in name:
            if is_mac:
                MacAutomation.mute_sound(True)
                MacAutomation.open_application("zoom.us")
                MacAutomation.open_application("Notes")
                time.sleep(0.5)
                MacAutomation.tile_positions({"left": "zoom.us", "right": "Notes"})
            else:
                WinAutomation.mute_sound(True)
                WinAutomation.open_application("zoom")
                WinAutomation.open_application("notepad")
                time.sleep(0.5)
                WinAutomation.tile_positions({"left": "zoom", "right": "notepad"})
            return {
                "success": True,
                "workflow": "meeting_mode",
                "message": "Meeting mode activated. Mic muted, Meeting & Notes tiled."
            }

        # 2. Focus / Deep Work Mode: Close distracting apps + open VS Code + play Spotify
        elif "focus" in name or "deep work" in name:
            distractions = ["WhatsApp", "Telegram", "Discord", "Slack"]
            for d in distractions:
                if is_mac:
                    MacAutomation.close_application(d)
                else:
                    WinAutomation.close_application(d)

            if is_mac:
                MacAutomation.open_application("Code")
                MacAutomation.open_application("Spotify")
                MacAutomation.set_volume(35)
                time.sleep(0.5)
                MacAutomation.tile_windows(["Code", "Spotify"])
            else:
                WinAutomation.open_application("code")
                WinAutomation.open_application("spotify")
                WinAutomation.set_volume(35)
                time.sleep(0.5)
                WinAutomation.tile_windows(["Visual Studio Code", "Spotify"])

            return {
                "success": True,
                "workflow": "focus_mode",
                "message": "Focus mode initiated. Distractions closed, VS Code & Spotify tiled at 35% volume."
            }

        # 3. Clean Workspace Routine: Minimize all + return to clean slate
        elif "clean" in name or "reset" in name:
            if is_mac:
                MacAutomation.minimize_all()
            else:
                WinAutomation.minimize_all()
            return {
                "success": True,
                "workflow": "clean_workspace",
                "message": "Workspace cleared. Showing desktop."
            }

        return {"success": False, "error": f"Unknown workflow: {workflow_name}"}
