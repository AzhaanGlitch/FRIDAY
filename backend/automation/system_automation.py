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
            app_name = params.get("app_name", "")
            if is_mac:
                return MacAutomation.open_application(app_name)
            elif is_win:
                return WinAutomation.open_application(app_name)
            return {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "set_volume":
            level = params.get("level", 50)
            if is_mac:
                return MacAutomation.set_volume(level)
            elif is_win:
                return WinAutomation.set_volume(level)
            return {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "take_screenshot":
            if is_mac:
                return MacAutomation.take_screenshot()
            elif is_win:
                return WinAutomation.take_screenshot()
            return {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "system_info":
            if is_mac:
                return MacAutomation.get_system_info()
            return {"success": True, "info": {"platform": sys.platform}}

        return {"success": False, "error": f"Unknown automation intent: {intent}"}
