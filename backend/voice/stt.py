import os
import sys
import time
import tempfile
import threading
import numpy as np
import requests
import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
from dotenv import load_dotenv
from backend.voice.tts import VoiceTTS

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

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()


class SarvamSTTHandler:
    """
    Sarvam AI Speech-to-Text Handler.
    High-accuracy, low-latency multilingual speech recognition for Indian English, Hindi, and Hinglish.
    """

    API_URL = "https://api.sarvam.ai/speech-to-text"
    DEFAULT_MODEL = "saaras:v3"
    DEFAULT_LANG = "unknown"  # Auto-detects English, Hindi, Hinglish with perfect accuracy

    @classmethod
    def get_api_key(cls) -> str:
        return os.getenv("SARVAM_API_KEY", "").strip()

    @classmethod
    def transcribe(
        cls,
        wav_path: str,
        model: str = DEFAULT_MODEL,
        language_code: str = DEFAULT_LANG,
    ) -> str:
        """
        Transcribe audio file using Sarvam AI STT API.
        Returns transcribed text string or empty string on failure.
        """
        api_key = cls.get_api_key()
        if not api_key:
            safe_print("[SarvamSTT] Warning: SARVAM_API_KEY not configured.")
            return ""

        if not wav_path or not os.path.exists(wav_path):
            return ""

        headers = {
            "api-subscription-key": api_key,
        }

        data = {
            "model": model,
            "language_code": language_code,
        }

        try:
            with open(wav_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(wav_path), audio_file, "audio/wav")
                }
                response = requests.post(
                    cls.API_URL,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=8.0,
                )

            if response.status_code == 200:
                res_data = response.json()
                transcript = res_data.get("transcript") or res_data.get("text", "")
                if transcript and len(transcript.strip()) > 0:
                    safe_print(f"[SarvamSTT ({res_data.get('language_code', language_code)})]: '{transcript.strip()}'")
                    return transcript.strip()
            else:
                safe_print(f"[SarvamSTT Error] HTTP {response.status_code}: {response.text}")
        except Exception as e:
            safe_print(f"[SarvamSTT Exception]: {e}")

        return ""


class VoiceSTT:
    """
    Primary Sarvam AI Speech-to-Text with Google Speech (hi-IN / en-IN) Fallback Engine.
    Accurate and robust recognition for English, Hindi, and Hinglish.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

    def _transcribe_google_fallback(self, wav_path: str) -> str:
        """Fallback transcription using Google Speech Recognition."""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)

                # 1. Hindi-India (Detects pure Hindi, Hinglish, and English)
                try:
                    text_hi = self.recognizer.recognize_google(audio, language="hi-IN")
                    if text_hi and len(text_hi.strip()) > 1:
                        safe_print(f"[Google STT Fallback hi-IN]: '{text_hi}'")
                        return text_hi.strip()
                except Exception:
                    pass

                # 2. English-India fallback
                try:
                    text_en = self.recognizer.recognize_google(audio, language="en-IN")
                    if text_en and len(text_en.strip()) > 1:
                        safe_print(f"[Google STT Fallback en-IN]: '{text_en}'")
                        return text_en.strip()
                except Exception:
                    pass
        except Exception as e:
            safe_print(f"[Google STT Fallback Error]: {e}")

        return ""

    def transcribe_file(self, wav_path: str) -> str:
        """
        Transcribe an existing WAV file:
        1. Attempt Sarvam AI STT primary engine.
        2. Fall back to Google STT if Sarvam fails or is unavailable.
        """
        # 1. Primary Engine: Sarvam AI STT
        text = SarvamSTTHandler.transcribe(wav_path)
        if text and len(text.strip()) > 0:
            return text

        # 2. Fallback Engine: Google Speech API (hi-IN)
        safe_print("[VoiceSTT] Sarvam STT returned empty or failed. Invoking Google STT fallback...")
        return self._transcribe_google_fallback(wav_path)

    _working_device = None

    @classmethod
    def _get_input_device(cls):
        """Find the most stable audio input device on Windows/macOS/Linux."""
        if cls._working_device is not None:
            return cls._working_device

        try:
            sd.check_input_settings(channels=1, samplerate=cls.SAMPLE_RATE, dtype='int16')
            cls._working_device = None
            return None
        except Exception:
            pass

        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    try:
                        sd.check_input_settings(device=idx, channels=1, samplerate=cls.SAMPLE_RATE, dtype='int16')
                        cls._working_device = idx
                        return idx
                    except Exception:
                        continue
        except Exception:
            pass

        return None

    def record_and_transcribe(self, max_duration_seconds: float = 4.5, **kwargs) -> dict:
        """
        Record user speech cleanly using sounddevice and transcribe.
        """
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            safe_print("[STT] Listening for user speech...")
            VoiceTTS.stop_speaking()

            # Record audio buffer using sounddevice
            dev = self._get_input_device()
            duration = max_duration_seconds
            num_samples = int(duration * self.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16', device=dev)
            sd.wait()

            # Energy check to discard silence
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 120:
                safe_print("[STT] Silence detected (ambient noise only).")
                return {"success": False, "error": "Silence"}

            # Save temporary WAV file
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, audio_data)
            tmp.close()
            wav_path = tmp.name

            # Transcribe (Sarvam AI -> Google STT fallback)
            text = self.transcribe_file(wav_path)

            if text and len(text.strip()) > 1:
                safe_print(f"[STT Final Recognized]: '{text}'")
                return {"success": True, "text": text}

            safe_print("[STT] Audio captured but no speech could be transcribed.")
            return {"success": False, "error": "No speech recognized"}

        except Exception as e:
            safe_print(f"[STT Error]: {e}")
            return {"success": False, "error": str(e)}
        finally:
            _mic_lock.release()
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass


stt_engine = VoiceSTT()


if __name__ == "__main__":
    safe_print("Testing VoiceSTT Engine (Speak a command now for 4.5 seconds)...")
    res = stt_engine.record_and_transcribe()
    safe_print("STT Result:", res)
