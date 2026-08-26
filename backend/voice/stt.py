import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import requests
import numpy as np
from backend.config.config import settings
from backend.voice.tts import VoiceTTS

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

class VoiceSTT:
    """
    Seamless, High-Fidelity Voice Recording & Speech-to-Text with Barge-In detection.
    When user speaks during audio recording, any background speech from assistant is instantly cut off.
    Supports English & Hindi.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq's Whisper Large v3 Turbo (unprompted, multilingual)."""
        if not settings.GROQ_API_KEY:
            return ""

        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            
            with open(wav_path, "rb") as f:
                files = {"file": (os.path.basename(wav_path), f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "temperature": 0.0
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=6)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    print(f"[STT Groq Whisper Large-v3]: '{text}'")
                    return text
            else:
                print(f"[STT Groq Warning]: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, duration_seconds: float = 3.5) -> dict:
        """
        Record live audio with active barge-in interrupt:
        If user starts speaking while assistant is speaking, assistant voice is instantly killed.
        """
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            num_samples = int(duration_seconds * self.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Verify that human sound energy was captured
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 60:
                return {"success": False, "error": "Silence"}

            # If user spoke with significant voice energy, trigger instant Barge-in!
            VoiceTTS.stop_speaking()

            # Save clean WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, audio_data)
            wav_path = tmp.name

            # 1. Primary: Groq Whisper Large-v3 (Multilingual English + Hindi)
            text = self._transcribe_groq_whisper(wav_path)

            # 2. Fallback: Google Speech Recognition
            if not text:
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio)
                        print(f"[STT Google Fallback]: '{text}'")
                except Exception:
                    pass

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
