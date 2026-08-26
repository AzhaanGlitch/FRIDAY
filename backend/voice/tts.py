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

class VoiceTTS:
    """
    Ultra-Realistic Microsoft Neural Voice Engine with Barge-In (Instant Interruption) Support.
    - English Voice: en-US-AvaNeural (Warm, fluent, modern human assistant)
    - Hindi Voice: hi-IN-SwaraNeural (Natural conversational Hindi)
    """

    ENGLISH_VOICE = "en-US-AvaNeural"
    HINDI_VOICE = "hi-IN-SwaraNeural"

    @classmethod
    def stop_speaking(cls):
        """Instant Barge-in Interrupt: Immediately kill active speech playback in <10ms."""
        global _active_playback_proc
        with _tts_lock:
            if _active_playback_proc:
                try:
                    _active_playback_proc.terminate()
                    _active_playback_proc.kill()
                    print("[VoiceTTS]: Interrupted! (Barge-in triggered)")
                except Exception:
                    pass
                _active_playback_proc = None
            
            # Kill any system afplay/say processes if running
            if sys.platform == "darwin":
                try:
                    subprocess.run(["pkill", "-9", "-f", "afplay"], capture_output=True)
                    subprocess.run(["pkill", "-9", "-f", "say"], capture_output=True)
                except Exception:
                    pass

    @classmethod
    def _is_hindi(cls, text: str) -> bool:
        """Detect if text contains Hindi (Devanagari) characters or common Hindi words."""
        # Devanagari Unicode range
        if re.search(r'[\u0900-\u097F]', text):
            return True
        # Common Romanized Hindi words
        hindi_keywords = ["haan", "theek", "shukriya", "kya", "kaise", "batao", "karein", "hai", "hain", "kardo"]
        words = text.lower().split()
        return any(w in words for w in hindi_keywords)

    @classmethod
    async def _generate_edge_tts_audio(cls, text: str, voice: str, output_path: str):
        """Generate neural MP3 audio file using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        await communicate.save(output_path)

    @classmethod
    def speak(cls, text: str) -> dict:
        """
        Synthesize text with ultra-realistic Microsoft Edge Neural Voice and play immediately.
        Supports instant barge-in interruption.
        """
        if not text:
            return {"success": False, "error": "Empty text"}

        # Stop any previous ongoing speech first
        cls.stop_speaking()

        global _active_playback_proc

        # Select Voice (Ava for English, Swara for Hindi)
        voice = cls.HINDI_VOICE if cls._is_hindi(text) else cls.ENGLISH_VOICE

        temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_mp3_path = temp_mp3.name
        temp_mp3.close()

        try:
            # 1. Generate HD Neural Speech via edge-tts
            asyncio.run(cls._generate_edge_tts_audio(text, voice, temp_mp3_path))

            # 2. Play audio with low-latency native player (afplay on macOS)
            with _tts_lock:
                if sys.platform == "darwin":
                    _active_playback_proc = subprocess.Popen(["afplay", temp_mp3_path])
                else:
                    # Windows / Linux fallback
                    _active_playback_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", temp_mp3_path])

            _active_playback_proc.wait()
            return {"success": True, "voice": voice, "method": "edge_neural"}

        except Exception as e:
            print(f"[VoiceTTS Edge-TTS Error, fallback to native]: {e}")
            # Fallback to macOS native say
            if sys.platform == "darwin":
                try:
                    with _tts_lock:
                        _active_playback_proc = subprocess.Popen(["say", "-v", "Samantha", text])
                    _active_playback_proc.wait()
                    return {"success": True, "method": "macos_say"}
                except Exception as ex:
                    return {"success": False, "error": str(ex)}
            return {"success": False, "error": str(e)}

        finally:
            with _tts_lock:
                _active_playback_proc = None
            try:
                if os.path.exists(temp_mp3_path):
                    os.unlink(temp_mp3_path)
            except OSError:
                pass
