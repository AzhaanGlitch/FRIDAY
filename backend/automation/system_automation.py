import sys
from backend.automation.mac_automation import MacAutomation
from backend.automation.win_automation import WinAutomation
from backend.automation.file_manager import FileManager
from backend.automation.clipboard_manager import ClipboardManager
from backend.automation.apps.spotify_controller import SpotifyController
from backend.automation.apps.browser_controller import BrowserController
from backend.automation.workflows import MultiStepWorkflows
from backend.automation.system_monitor import SystemMonitor

class SystemAutomation:
    """Unified system automation interface supporting macOS and Windows."""

    @classmethod
    def execute_intent(cls, intent: str, params: dict) -> dict:
        """Route automation intents to platform adapter or specialized controller."""
        is_mac = sys.platform == "darwin"
        is_win = sys.platform == "win32"

        # 1. Application Launch & Close
        if intent == "open_app":
            app_name = params.get("app_name") or params.get("app") or params.get("name") or params.get("application") or ""
            return MacAutomation.open_application(app_name) if is_mac else WinAutomation.open_application(app_name) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "close_app":
            app_name = params.get("app_name") or params.get("app") or params.get("name") or params.get("application") or ""
            return MacAutomation.close_application(app_name) if is_mac else WinAutomation.close_application(app_name) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        # 2. System Sound & Volume
        elif intent == "set_volume":
            level = params.get("level", 50)
            return MacAutomation.set_volume(level) if is_mac else WinAutomation.set_volume(level) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "mute_sound":
            mute = params.get("mute", True)
            return MacAutomation.mute_sound(mute) if is_mac else WinAutomation.mute_sound(mute) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        # 3. Screen & Display
        elif intent == "minimize_all":
            return MacAutomation.minimize_all() if is_mac else WinAutomation.minimize_all() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "set_brightness":
            level = params.get("level", 80)
            return MacAutomation.set_brightness(level) if is_mac else WinAutomation.set_brightness(level) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "take_screenshot":
            return MacAutomation.take_screenshot() if is_mac else WinAutomation.take_screenshot() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        # 4. System Power & Security
        elif intent == "lock_screen":
            return MacAutomation.lock_screen() if is_mac else WinAutomation.lock_screen() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "sleep_system":
            return MacAutomation.sleep_system() if is_mac else WinAutomation.sleep_system() if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "system_info":
            return SystemMonitor.get_metrics()

        # 5. Media & Spotify Deep Control
        elif intent == "media_control":
            action = params.get("action", "play_pause")
            return SpotifyController.control(action)

        elif intent == "spotify_play":
            query = params.get("query") or params.get("song") or ""
            return SpotifyController.search_and_play(query)

        # 6. Browser & Web Search
        elif intent == "open_url":
            url = params.get("url", "")
            return MacAutomation.open_url(url) if is_mac else WinAutomation.open_url(url) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "browser_search":
            engine = params.get("engine", "google")
            query = params.get("query", "")
            return BrowserController.search(engine, query)

        # 7. Multi-Window Tiling
        elif intent == "tile_windows":
            apps = params.get("apps", [])
            return MacAutomation.tile_windows(apps) if is_mac else WinAutomation.tile_windows(apps) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        elif intent == "tile_positions":
            positions = params.get("positions", params)
            return MacAutomation.tile_positions(positions) if is_mac else WinAutomation.tile_positions(positions) if is_win else {"success": False, "error": f"Unsupported platform: {sys.platform}"}

        # 8. File Management
        elif intent == "search_file":
            filename = params.get("filename") or params.get("query") or ""
            ext = params.get("extension")
            return FileManager.search_files(filename, extension=ext)

        elif intent == "create_file":
            filename = params.get("filename", "new_file.txt")
            content = params.get("content", "")
            return FileManager.create_file(filename, content)

        elif intent == "create_folder":
            folder_name = params.get("folder_name", "New Folder")
            return FileManager.create_folder(folder_name)

        elif intent == "organize_folder" or intent == "organize_downloads":
            return FileManager.organize_downloads()

        elif intent == "delete_file" or intent == "safe_delete":
            filename = params.get("filename", "")
            return FileManager.safe_delete_file(filename)

        elif intent == "recent_downloads":
            count = int(params.get("count", 5))
            return FileManager.read_recent_downloads(count)


        # 9. Advanced Clipboard
        elif intent == "clipboard_get":
            text = ClipboardManager.get_clipboard()
            return {"success": True, "text": text}

        elif intent == "clipboard_set":
            text = params.get("text", "")
            success = ClipboardManager.set_clipboard(text)
            return {"success": success, "text": text}

        elif intent == "clipboard_transform":
            transformation = params.get("transformation", "upper")
            return ClipboardManager.transform_clipboard(transformation)

        # 10. Multi-Step Workflows
        elif intent == "execute_workflow":
            name = params.get("workflow") or params.get("name") or ""
            return MultiStepWorkflows.execute_workflow(name)

        # 11. Memory Management
        elif intent == "clear_history":
            from backend.memory.database import MemoryDatabase
            return MemoryDatabase.clear_history()

        return {"success": False, "error": f"Unknown automation intent: {intent}"}

