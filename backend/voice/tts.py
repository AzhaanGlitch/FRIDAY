import sys
import subprocess

class VoiceTTS:
    """Text-To-Speech engine wrapper."""

    @classmethod
    def speak(cls, text: str) -> dict:
        """Speak given text using system native speech synthesizer (macOS `say` or pyttsx3 fallback)."""
        if not text:
            return {"success": False, "error": "Empty text"}

        if sys.platform == "darwin":
            try:
                # Use native macOS high quality voice generator
                subprocess.Popen(["say", text])
                return {"success": True, "method": "macos_say"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return {"success": True, "method": "pyttsx3"}
        except Exception as e:
            return {"success": False, "error": str(e)}
