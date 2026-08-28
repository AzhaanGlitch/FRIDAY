import os
import sys
import subprocess
import threading
import asyncio
import tempfile
import re
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def safe_print(*args, **kwargs):
    """Safely print messages preventing charmap encoding errors on Windows console."""
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            encoding = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
            cleaned_args = [
                str(a).encode(encoding, errors='replace').decode(encoding)
                for a in args
            ]
            print(*cleaned_args, **kwargs)
        except Exception:
            pass

# Active playback subprocess reference for instant barge-in kill
_active_playback_proc = None
_tts_lock = threading.Lock()
_is_speaking_event = threading.Event()


class SarvamTTSHandler:
    """
    Sarvam AI Text-to-Speech Handler.
    Uses Sarvam AI API (bulbul:v3 model with high-quality female voices like 'priya' / 'shreya')
    for ultra-natural Indian English and Hindi speech synthesis.
    """

    API_URL = "https://api.sarvam.ai/text-to-speech"
    DEFAULT_MODEL = "bulbul:v3"
    DEFAULT_SPEAKER = "priya"  # High-quality natural Indian female voice
    DEFAULT_LANG = "hi-IN"

    @classmethod
    def get_api_key(cls) -> str:
        return os.getenv("SARVAM_API_KEY", "").strip()

    @classmethod
    def synthesize(
        cls,
        text: str,
        speaker: str = DEFAULT_SPEAKER,
        model: str = DEFAULT_MODEL,
        target_language_code: str = DEFAULT_LANG,
    ) -> str | None:
        """
        Synthesize speech using Sarvam AI Text-to-Speech API.
        Returns path to generated WAV file or None on failure.
        """
        api_key = cls.get_api_key()
        if not api_key:
            safe_print("[SarvamTTS] Warning: SARVAM_API_KEY is not set.")
            return None

        if not text or not text.strip():
            return None

        # Prepare payload for Sarvam API
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }

        # Compatible speaker mapping for female voices
        female_speaker = speaker if speaker in [
            "priya", "shreya", "ritu", "neha", "pooja", "simran",
            "kavya", "ishita", "roopa", "tanya"
        ] else "priya"

        payload = {
            "inputs": [text.strip()],
            "target_language_code": target_language_code,
            "speaker": female_speaker,
            "pace": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": model,
        }

        try:
            response = requests.post(cls.API_URL, headers=headers, json=payload, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                audios = data.get("audios", [])
                if audios and len(audios) > 0:
                    audio_b64 = audios[0]
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    tmp_wav.write(audio_bytes)
                    tmp_wav.close()
                    safe_print(f"[SarvamTTS] Audio successfully synthesized using speaker '{female_speaker}'.")
                    return tmp_wav.name
            else:
                safe_print(f"[SarvamTTS Error] HTTP {response.status_code}: {response.text}")
        except Exception as e:
            safe_print(f"[SarvamTTS Exception]: {e}")

        return None


class VoiceTTS:
    """
    Multilingual Neural Voice Engine with Sarvam AI (Primary) and Edge-TTS / pyttsx3 (Fallback).
    Barge-In (Instant Interruption) Support included.
    """

    FALLBACK_ENGLISH_VOICE = "en-IN-NeerjaExpressiveNeural"
    FALLBACK_HINDI_VOICE = "hi-IN-SwaraNeural"

    @classmethod
    def is_speaking(cls) -> bool:
        """Check if assistant voice is actively playing."""
        return _is_speaking_event.is_set()

    @classmethod
    def stop_speaking(cls):
        """Instant Barge-in Interrupt: Immediately kill active speech playback."""
        global _active_playback_proc
        with _tts_lock:
            _is_speaking_event.clear()
            if _active_playback_proc:
                try:
                    _active_playback_proc.terminate()
                    _active_playback_proc.kill()
                    safe_print("[VoiceTTS]: Interrupted! (Barge-in triggered)")
                except Exception:
                    pass
                _active_playback_proc = None

            # Stop pygame audio if active
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass

            # Kill platform-specific external players if any
            if sys.platform == "darwin":
                try:
                    subprocess.run(["pkill", "-9", "-f", "afplay"], capture_output=True)
                except Exception:
                    pass

    @classmethod
    def _is_hindi(cls, text: str) -> bool:
        """Detect if text contains Hindi (Devanagari) characters or common Romanized Hindi words."""
        if re.search(r'[\u0900-\u097F]', text):
            return True
        hindi_keywords = [
            "haan", "theek", "shukriya", "kya", "kaise", "batao", "karein", "hai", 
            "hain", "kardo", "kholo", "chalao", "hoon", "main", "aap", "tum", 
            "namaste", "kar", "diya", "rahi", "raha", "suno", "sunao", "aawaz",
            "sahi", "kuch", "karo", "bol", "bolo", "dhanyawad"
        ]
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        return any(w in hindi_keywords for w in words)

    @classmethod
    async def _generate_edge_tts_audio(cls, text: str, voice: str, output_path: str):
        """Generate neural MP3 audio file using edge-tts as fallback."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate="+3%", pitch="+1Hz")
        await communicate.save(output_path)

    @classmethod
    def _synthesize_fallback(cls, text: str) -> str | None:
        """Fallback to Edge-TTS / pyttsx3 female voices."""
        is_hi = cls._is_hindi(text)
        voice = cls.FALLBACK_HINDI_VOICE if is_hi else cls.FALLBACK_ENGLISH_VOICE

        temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_mp3_path = temp_mp3.name
        temp_mp3.close()

        try:
            asyncio.run(cls._generate_edge_tts_audio(text, voice, temp_mp3_path))
            safe_print(f"[VoiceTTS Fallback]: Generated audio via Edge-TTS ({voice})")
            return temp_mp3_path
        except Exception as e:
            safe_print(f"[VoiceTTS Fallback Error]: {e}")
            if os.path.exists(temp_mp3_path):
                try:
                    os.unlink(temp_mp3_path)
                except OSError:
                    pass

        # Final local fallback using pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            # Set female voice if available
            voices = engine.getProperty('voices')
            for v in voices:
                if 'female' in v.name.lower() or 'zira' in v.name.lower() or 'swara' in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wav_path = temp_wav.name
            temp_wav.close()
            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            return wav_path
        except Exception as e2:
            safe_print(f"[VoiceTTS Local Engine Error]: {e2}")
            return None

    @classmethod
    def synthesize_to_file(cls, text: str) -> str | None:
        """
        Synthesize text to audio file (Sarvam AI primary -> Edge-TTS fallback).
        Returns path to temporary audio file.
        """
        if not text or text.strip().upper() == "SILENT":
            return None

        # 1. Primary Engine: Sarvam AI TTS (Female Voice: Priya)
        audio_file = SarvamTTSHandler.synthesize(text)
        if audio_file and os.path.exists(audio_file):
            return audio_file

        # 2. Fallback Engine: Edge-TTS / pyttsx3
        safe_print("[VoiceTTS] Sarvam TTS unavailable or failed. Switching to secondary fallback TTS...")
        return cls._synthesize_fallback(text)

    @classmethod
    def play_synthesized_file(cls, audio_path: str, on_start=None, on_end=None):
        """Play synthesized audio file cleanly with interruption support."""
        if not audio_path or not os.path.exists(audio_path):
            return

        cls.stop_speaking()

        global _active_playback_proc
        try:
            with _tts_lock:
                _is_speaking_event.set()

                # Try pygame playback first
                try:
                    import pygame
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()

                    if on_start:
                        try:
                            on_start()
                        except Exception:
                            pass

                    while pygame.mixer.music.get_busy() and _is_speaking_event.is_set():
                        time.sleep(0.05)
                    return
                except Exception as pg_err:
                    safe_print(f"[VoiceTTS PyGame Warning]: {pg_err}. Using system player fallback.")

                # Platform specific fallbacks
                if sys.platform == "darwin":
                    _active_playback_proc = subprocess.Popen(["afplay", audio_path])
                elif sys.platform == "win32":
                    ps_cmd = f"(New-Object Media.SoundPlayer '{audio_path}').PlaySync();"
                    _active_playback_proc = subprocess.Popen(["powershell", "-c", ps_cmd])
                else:
                    _active_playback_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", audio_path])

            if on_start:
                try:
                    on_start()
                except Exception:
                    pass

            if _active_playback_proc:
                _active_playback_proc.wait()

        except Exception as e:
            safe_print(f"[VoiceTTS Playback Error]: {e}")
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
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
            except OSError:
                pass

    @classmethod
    def speak(cls, text: str) -> dict:
        """Synthesize and play speech in one step."""
        audio_file = cls.synthesize_to_file(text)
        if not audio_file:
            return {"success": False, "error": "Failed to synthesize speech"}

        cls.play_synthesized_file(audio_file)
        return {"success": True}


if __name__ == "__main__":
    test_phrase = "Namaste! Main F.R.I.D.A.Y. hoon, aapka personal AI assistant."
    safe_print(f"Testing VoiceTTS with phrase: '{test_phrase}'")
    result = VoiceTTS.speak(test_phrase)
    safe_print("TTS Result:", result)
