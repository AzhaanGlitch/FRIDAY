import os
import sys
import subprocess
import threading
import asyncio
import tempfile
import re

# Active playback subprocess reference for instant barge-in kill
_active_playback_proc = None
_tts_lock = threading.Lock()
_is_speaking_event = threading.Event()

class VoiceTTS:
    """
    Ultra-Realistic Microsoft Neural Voice Engine with Barge-In (Instant Interruption) Support.
    - Multilingual & Indian English: en-IN-NeerjaExpressiveNeural / en-US-AvaMultilingualNeural
    - Hindi Voice: hi-IN-SwaraNeural (Warm, expressive Indian human female)
    """

    ENGLISH_VOICE = "en-IN-NeerjaExpressiveNeural"  # Highly natural expressive Indian English assistant voice
    HINDI_VOICE = "hi-IN-SwaraNeural"              # Real human Hindi voice

    @classmethod
    def is_speaking(cls) -> bool:
        """Check if assistant voice is actively playing."""
        return _is_speaking_event.is_set()

    @classmethod
    def stop_speaking(cls):
        """Instant Barge-in Interrupt: Immediately kill active speech playback in <10ms."""
        global _active_playback_proc
        with _tts_lock:
            _is_speaking_event.clear()
            if _active_playback_proc:
                try:
                    _active_playback_proc.terminate()
                    _active_playback_proc.kill()
                    print("[VoiceTTS]: Interrupted! (Barge-in triggered)")
                except Exception:
                    pass
                _active_playback_proc = None
            
            # Kill any system afplay processes if running
            if sys.platform == "darwin":
                try:
                    subprocess.run(["pkill", "-9", "-f", "afplay"], capture_output=True)
                except Exception:
                    pass

    @classmethod
    def _is_hindi(cls, text: str) -> bool:
        """Detect if text contains Hindi (Devanagari) characters or common Romanized Hindi words."""
        # Devanagari Unicode range
        if re.search(r'[\u0900-\u097F]', text):
            return True
        # Common Romanized Hindi keywords
        hindi_keywords = [
            "haan", "theek", "shukriya", "kya", "kaise", "batao", "karein", "hai", 
            "hain", "kardo", "kholo", "chalao", "hoon", "main", "aap", "tum", 
            "namaste", "kar", "diya", "rahi", "raha", "suno", "sunao", "aawaz",
            "sahi", "kuch", "karo", "bol", "bolo"
        ]
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        return any(w in hindi_keywords for w in words)

    @classmethod
    async def _generate_edge_tts_audio(cls, text: str, voice: str, output_path: str):
        """Generate neural MP3 audio file using edge-tts with optimal cadence."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate="+3%", pitch="+1Hz")
        await communicate.save(output_path)

    @classmethod
    def synthesize_to_file(cls, text: str) -> str | None:
        """Synthesize text to temporary MP3 file and return path."""
        if not text or text.strip().upper() == "SILENT":
            return None
        
        is_hi = cls._is_hindi(text)
        voice = cls.HINDI_VOICE if is_hi else cls.ENGLISH_VOICE

        temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_mp3_path = temp_mp3.name
        temp_mp3.close()

        try:
            asyncio.run(cls._generate_edge_tts_audio(text, voice, temp_mp3_path))
            return temp_mp3_path
        except Exception as e:
            print(f"[VoiceTTS Synth Error]: {e}")
            if os.path.exists(temp_mp3_path):
                os.unlink(temp_mp3_path)
            return None

    @classmethod
    def play_synthesized_file(cls, mp3_path: str, on_start=None, on_end=None):
        """Play already synthesized MP3 file with zero startup delay."""
        if not mp3_path or not os.path.exists(mp3_path):
            return

        cls.stop_speaking()

        global _active_playback_proc
        try:
            with _tts_lock:
                _is_speaking_event.set()
                if sys.platform == "darwin":
                    _active_playback_proc = subprocess.Popen(["afplay", mp3_path])
                else:
                    _active_playback_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", mp3_path])

            if on_start:
                try:
                    on_start()
                except Exception:
                    pass

            _active_playback_proc.wait()
        except Exception as e:
            print(f"[VoiceTTS Playback Error]: {e}")
        finally:
            with _tts_lock:
                _is_speaking_event.clear()
                _active_playback_proc = None
            if on_end:
                try:
                    on_end()
                except Exception:
                    pass
            try:
                if os.path.exists(mp3_path):
                    os.unlink(mp3_path)
            except OSError:
                pass

    @classmethod
    def speak(cls, text: str) -> dict:
        """
        Synthesize and play in one step.
        """
        mp3 = cls.synthesize_to_file(text)
        if not mp3:
            return {"success": False, "error": "Failed to synthesize speech"}

        cls.play_synthesized_file(mp3)
        return {"success": True}
