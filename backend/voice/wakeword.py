import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import time
import os
import requests
import numpy as np
import speech_recognition as sr
from backend.config.config import settings

class WakeWordDetector:
    """
    Robust Wake Word Detector for 'FRIDAY'.
    - Balanced energy threshold to prevent false-triggers on ambient room noise.
    - Strict, accurate phonetic matching.
    """

    SAMPLE_RATE = 16000
    CHUNK_DURATION = 1.3

    # Clean, accurate wake word patterns
    WAKE_PATTERNS = [
        "friday", "hey friday", "hi friday", "hello friday", 
        "ok friday", "okay friday", "fraiday", "fryday"
    ]

    @classmethod
    def _is_wakeword_matched(cls, text: str) -> bool:
        """Accurate matching to eliminate false alarms."""
        text_clean = text.lower().strip()
        if not text_clean:
            return False

        # Direct pattern match
        for pat in cls.WAKE_PATTERNS:
            if pat in text_clean:
                return True
                
        # Word boundary match
        words = text_clean.split()
        for w in words:
            if w in ["friday", "fryday", "fraiday"] or w.startswith("frid"):
                return True

        return False

    @classmethod
    def _transcribe_groq_whisper(cls, wav_path: str) -> str:
        """Transcribe wake word candidate with Groq Whisper."""
        if not settings.GROQ_API_KEY:
            return ""
        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            with open(wav_path, "rb") as f:
                files = {"file": ("chunk.wav", f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "temperature": 0.0,
                    "prompt": "FRIDAY, hey Friday, hello Friday"
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=2.5)
            if res.status_code == 200:
                return res.json().get("text", "").strip()
        except Exception:
            pass
        return ""

    @classmethod
    def _record_chunk(cls, duration: float = 1.3) -> tuple[str, bool]:
        """Record audio chunk with balanced speech energy gate."""
        try:
            num_samples = int(duration * cls.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=cls.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Balanced threshold: 140 RMS (rejects faint room sounds, breathes, echoes)
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 140:
                return ("", False)

            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, cls.SAMPLE_RATE, audio_data)
            return (tmp.name, True)
        except Exception as e:
            print(f"[WakeWord Record Error]: {e}")
            return ("", False)

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """Listen for wake word 'FRIDAY' with high accuracy and low false-positive rate."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 180
        recognizer.dynamic_energy_threshold = False

        print("[WakeWord] Listening for 'FRIDAY'...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            wav_path, has_sound = cls._record_chunk(duration=cls.CHUNK_DURATION)
            if not has_sound or not wav_path:
                time.sleep(0.05)
                continue

            # 1. Fast Google STT Check
            try:
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                    google_text = recognizer.recognize_google(audio).lower()
                    print(f"[WakeWord Heard (Fast)]: '{google_text}'")
                    if cls._is_wakeword_matched(google_text):
                        print("[WakeWord] Woken up by 'FRIDAY'!")
                        if wav_path and os.path.exists(wav_path):
                            os.unlink(wav_path)
                        return True
            except Exception:
                pass

            # 2. Groq Whisper Check
            whisper_text = cls._transcribe_groq_whisper(wav_path).lower()
            if whisper_text:
                print(f"[WakeWord Heard (Whisper)]: '{whisper_text}'")
                if cls._is_wakeword_matched(whisper_text):
                    print("[WakeWord] Woken up by 'FRIDAY'!")
                    if wav_path and os.path.exists(wav_path):
                        os.unlink(wav_path)
                    return True

            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

        return False
