import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import requests
import time
import numpy as np
from backend.config.config import settings
from backend.voice.tts import VoiceTTS

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

class VoiceSTT:
    """
    State-of-the-Art Speech Recognition Engine.
    Uses Google Cloud Speech API as ultra-fast, robust Primary STT (zero hallucination, perfect Hindi/English words)
    backed by Groq Whisper Large-v3 fallback.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 2.0  # Allow 2.0 seconds of natural speech pause before finishing!
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 1.0

    def _transcribe_google(self, wav_path: str) -> str:
        """Transcribe using Google Speech Recognition (High-accuracy bilingual Hindi+English, zero hallucinations)."""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                
                # 1. Primary: Hindi-India (Detects both pure Hindi, Hinglish and English commands seamlessly)
                try:
                    text_hi = self.recognizer.recognize_google(audio, language="hi-IN")
                    if text_hi and len(text_hi.strip()) > 1:
                        print(f"[STT Google hi-IN]: '{text_hi}'")
                        return text_hi
                except Exception:
                    pass

                # 2. English-India fallback
                try:
                    text_en = self.recognizer.recognize_google(audio, language="en-IN")
                    if text_en and len(text_en.strip()) > 1:
                        print(f"[STT Google en-IN]: '{text_en}'")
                        return text_en
                except Exception:
                    pass

        except Exception as e:
            print(f"[STT Google Error]: {e}")
        return ""

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq Whisper Large v3 Turbo as secondary fallback."""
        if not settings.GROQ_API_KEY:
            return ""

        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            
            with open(wav_path, "rb") as f:
                files = {"file": (os.path.basename(wav_path), f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "temperature": 0.0,
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=8)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    lower_t = text.lower()
                    # Filter phantom hallucinations
                    if any(phrase in lower_t for phrase in ["subtitles by", "amara.org", "thank you for watching", "bye"]):
                        return ""
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, max_duration_seconds: float = 15.0, duration_seconds: float = None, **kwargs) -> dict:
        """
        Record user speech cleanly using SpeechRecognition microphone stream:
        - Listens until user genuinely finishes speaking with a comfortable 2.0s pause.
        - Captures full, long sentences without any premature cutoffs.
        """
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            # Record using recognizer with 2.0s pause threshold
            with sr.Microphone(sample_rate=self.SAMPLE_RATE) as source:
                VoiceTTS.stop_speaking()
                # Record phrase with max phrase time limit of 15 seconds and 4.0s timeout to start
                try:
                    audio = self.recognizer.listen(source, timeout=3.5, phrase_time_limit=15.0)
                except sr.WaitTimeoutError:
                    return {"success": False, "error": "Silence"}

            # Save temporary WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            tmp.write(audio.get_wav_data())
            tmp.close()
            wav_path = tmp.name

            # 1. Primary: Google Multi-Lingual STT (hi-IN / en-IN)
            text = self._transcribe_google(wav_path)

            # 2. Fallback: Groq Whisper Large-v3
            if not text:
                text = self._transcribe_groq_whisper(wav_path)

            if text and len(text.strip()) > 1:
                return {"success": True, "text": text}
            return {"success": False, "error": "No speech recognized"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            _mic_lock.release()
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

stt_engine = VoiceSTT()
