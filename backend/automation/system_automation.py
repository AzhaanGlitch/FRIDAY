import sys
from backend.automation.mac_automation import MacAutomation
from backend.automation.win_automation import WinAutomation

class SystemAutomation:
    """Unified system automation interface supporting macOS and Windows."""

    @classmethod
    def execute_intent(cls, intent: str, params: dict) -> dict:
        """Route automation intents to platform adapter."""
        is_mac = sys.platform == "darwin"
        is_win = sys.platform == "win32"

        if intent == "open_app":
            app_name = params.get("app_name") or params.get("app") or params.get("name") or params.get("application") or ""
            return MacAutomation.open_application(app_name) if is_mac else WinAutomation.open_application(app_name) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "close_app":
            app_name = params.get("app_name") or params.get("app") or params.get("name") or params.get("application") or ""
            return MacAutomation.close_application(app_name) if is_mac else WinAutomation.close_application(app_name) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}


        elif intent == "set_volume":
            level = params.get("level", 50)
            return MacAutomation.set_volume(level) if is_mac else WinAutomation.set_volume(level) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "mute_sound":
            mute = params.get("mute", True)
            return MacAutomation.mute_sound(mute) if is_mac else WinAutomation.mute_sound(mute) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "minimize_all":
            return MacAutomation.minimize_all() if is_mac else WinAutomation.minimize_all() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "media_control":
            action = params.get("action", "play_pause")
            return MacAutomation.media_control(action) if is_mac else WinAutomation.media_control(action) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "lock_screen":
            return MacAutomation.lock_screen() if is_mac else WinAutomation.lock_screen() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "sleep_system":
            return MacAutomation.sleep_system() if is_mac else WinAutomation.sleep_system() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "set_brightness":
            level = params.get("level", 80)
            return MacAutomation.set_brightness(level) if is_mac else WinAutomation.set_brightness(level) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "clipboard_get":
            return MacAutomation.clipboard_get() if is_mac else WinAutomation.clipboard_get() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "clipboard_set":
            text = params.get("text", "")
            return MacAutomation.clipboard_set(text) if is_mac else WinAutomation.clipboard_set(text) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "search_file":
            filename = params.get("filename", "")
            return MacAutomation.search_file(filename) if is_mac else WinAutomation.search_file(filename) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "open_url":
            url = params.get("url", "")
            return MacAutomation.open_url(url) if is_mac else WinAutomation.open_url(url) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "tile_windows":
            apps = params.get("apps", [])
            return MacAutomation.tile_windows(apps) if is_mac else WinAutomation.tile_windows(apps) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "tile_positions":
            positions = params.get("positions", params)
            return MacAutomation.tile_positions(positions) if is_mac else WinAutomation.tile_positions(positions) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}



        elif intent == "take_screenshot":
            return MacAutomation.take_screenshot() if is_mac else WinAutomation.take_screenshot() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "system_info":
            from backend.automation.system_monitor import SystemMonitor
            return SystemMonitor.get_metrics()

        return {"success": False, "error": f"Unknown automation intent: {intent}"}

