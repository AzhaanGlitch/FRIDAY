import sys
import subprocess
import re

class ClipboardManager:
    """
    Advanced cross-platform clipboard manager.
    Supports reading, writing, history retention, and text transformations.
    """

    _history: list[str] = []
    MAX_HISTORY = 10

    @classmethod
    def get_clipboard(cls) -> str:
        """Get current text from system clipboard."""
        try:
            if sys.platform == "darwin":
                p = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                text = p.stdout.strip()
            elif sys.platform == "win32":
                ps_cmd = "Get-Clipboard"
                p = subprocess.run(["powershell", "-c", ps_cmd], capture_output=True, text=True, timeout=2)
                text = p.stdout.strip()
            else:
                p = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=2)
                text = p.stdout.strip()

            if text and (not cls._history or cls._history[0] != text):
                cls._history.insert(0, text)
                if len(cls._history) > cls.MAX_HISTORY:
                    cls._history.pop()

            return text
        except Exception as e:
            print(f"[ClipboardManager Error]: {e}")
            return ""

    @classmethod
    def set_clipboard(cls, text: str) -> bool:
        """Set text to system clipboard and record in history."""
        try:
            if sys.platform == "darwin":
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"), timeout=2)
            elif sys.platform == "win32":
                ps_cmd = f"Set-Clipboard -Value @'\n{text}\n'@"
                subprocess.run(["powershell", "-c", ps_cmd], timeout=2)
            else:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"), timeout=2)

            if text:
                cls._history.insert(0, text)
                if len(cls._history) > cls.MAX_HISTORY:
                    cls._history.pop()
            return True
        except Exception as e:
            print(f"[ClipboardManager Set Error]: {e}")
            return False

    @classmethod
    def transform_clipboard(cls, transformation: str) -> dict:
        """
        Apply text transformation to clipboard:
        - "upper": Uppercase
        - "lower": Lowercase
        - "title": Title Case
        - "strip": Trim whitespace
        - "extract_urls": Extract all HTTP/HTTPS links
        """
        current_text = cls.get_clipboard()
        if not current_text:
            return {"success": False, "error": "Clipboard is empty"}

        transformed = current_text
        if transformation == "upper":
            transformed = current_text.upper()
        elif transformation == "lower":
            transformed = current_text.lower()
        elif transformation == "title":
            transformed = current_text.title()
        elif transformation == "strip":
            transformed = current_text.strip()
        elif transformation == "extract_urls":
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', current_text)
            transformed = "\n".join(urls) if urls else "No URLs found"

        cls.set_clipboard(transformed)
        return {
            "success": True,
            "original": current_text,
            "transformed": transformed,
            "transformation": transformation
        }

    @classmethod
    def get_history(cls) -> list[str]:
        """Return clipboard history."""
        return cls._history
