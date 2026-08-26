import sys
import subprocess
import threading

_tts_engine = None
_tts_lock = threading.Lock()

def _get_engine():
    global _tts_engine
    if _tts_engine is None:
        try:
            import pyttsx3
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty('rate', 185)  # Natural fast speech rate
        except Exception as e:
            print(f"[TTS Init Error]: {e}")
    return _tts_engine

class VoiceTTS:
    """Text-To-Speech engine wrapper."""

    @classmethod
    def speak(cls, text: str) -> dict:
        """Speak given text using system native speech synthesizer."""
        if not text:
            return {"success": False, "error": "Empty text"}

        if sys.platform == "darwin":
            try:
                subprocess.Popen(["say", text])
                return {"success": True, "method": "macos_say"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        with _tts_lock:
            try:
                engine = _get_engine()
                if engine:
                    engine.say(text)
                    engine.runAndWait()
                    return {"success": True, "method": "pyttsx3"}
            except Exception as e:
                global _tts_engine
                _tts_engine = None
                return {"success": False, "error": str(e)}
