import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import requests
import numpy as np
from backend.config.config import settings

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

class VoiceSTT:
    """
    Seamless, High-Fidelity Voice Recording & Speech-to-Text.
    Captures a full, uninterrupted audio buffer to guarantee words are never chopped in half.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq's Whisper Large v3 Turbo (unprompted, pure transcription)."""
        if not settings.GROQ_API_KEY:
            return ""

        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            
            with open(wav_path, "rb") as f:
                files = {"file": (os.path.basename(wav_path), f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "en",
                    "temperature": 0.0
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=6)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
            else:
                print(f"[STT Groq Warning]: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, duration_seconds: float = 3.5) -> dict:
        """
        Record continuous live audio for a clean 3.5s window.
        No premature silence cutoffs — guarantees full sentences like 'open spotify' are captured.
        """
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            print(f"[STT] Listening for command ({duration_seconds}s window)...")
            num_samples = int(duration_seconds * self.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Verify that some sound was actually captured
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 60:
                print("[STT] Ambient silence detected — no command spoken.")
                return {"success": False, "error": "Silence"}

            # Save clean WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, audio_data)
            wav_path = tmp.name

            # 1. Primary: Groq Whisper Large-v3 (Clean, unprompted)
            text = self._transcribe_groq_whisper(wav_path)

            # 2. Fallback: Google Speech Recognition
            if not text:
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio)
                        print(f"[STT Google Fallback]: '{text}'")
                except Exception as ge:
                    print(f"[STT Fallback Notice]: {ge}")

            if text:
                return {"success": True, "text": text}
            return {"success": False, "error": "No speech recognized"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            _mic_lock.release()
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

stt_engine = VoiceSTT()
