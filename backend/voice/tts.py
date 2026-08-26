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
            "namaste", "kar", "diya", "rahi", "raha", "suno", "sunao", "aawaz"
        ]
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        return any(w in hindi_keywords for w in words)

    @classmethod
    async def _generate_edge_tts_audio(cls, text: str, voice: str, output_path: str):
        """Generate neural MP3 audio file using edge-tts with optimal cadence."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate="+2%", pitch="+1Hz")
        await communicate.save(output_path)

    @classmethod
    def speak(cls, text: str) -> dict:
        """
        Synthesize text with ultra-realistic Microsoft Edge Neural Voice and play immediately.
        """
        if not text or text.strip().upper() == "SILENT":
            return {"success": False, "error": "Empty text"}

        # Stop any previous ongoing speech first
        cls.stop_speaking()

        global _active_playback_proc

        # Select Voice (Swara for Hindi/Hinglish, Neerja Expressive for English)
        is_hi = cls._is_hindi(text)
        voice = cls.HINDI_VOICE if is_hi else cls.ENGLISH_VOICE

        temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_mp3_path = temp_mp3.name
        temp_mp3.close()

        try:
            # 1. Generate HD Neural Speech via edge-tts
            asyncio.run(cls._generate_edge_tts_audio(text, voice, temp_mp3_path))

            # 2. Play audio with low-latency native player (afplay on macOS)
            with _tts_lock:
                _is_speaking_event.set()
                if sys.platform == "darwin":
                    _active_playback_proc = subprocess.Popen(["afplay", temp_mp3_path])
                else:
                    _active_playback_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", temp_mp3_path])

            _active_playback_proc.wait()
            return {"success": True, "voice": voice, "method": "edge_neural"}

        except Exception as e:
            print(f"[VoiceTTS Edge-TTS Error]: {e}")
            return {"success": False, "error": str(e)}

        finally:
            with _tts_lock:
                _is_speaking_event.clear()
                _active_playback_proc = None
            try:
                if os.path.exists(temp_mp3_path):
                    os.unlink(temp_mp3_path)
            except OSError:
                pass
