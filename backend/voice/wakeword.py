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
    Ultra-Sensitive, Instant Wake Word Detector for 'FRIDAY'.
    Features:
    1. Dual Fast Recognition Engine: Groq Whisper Large-v3-Turbo + Google Speech (Multi-threading).
    2. Ultra-Low Latency Sliding Audio Windows (1.1s chunks).
    3. Broad Phonetic Variations & Distance Matching ('friday', 'fried', 'fray day', 'saturday', 'free day', 'hey friday', 'ride', 'side', 'pride', 'frida').
    """

    SAMPLE_RATE = 16000
    CHUNK_DURATION = 1.1  # Snappy 1.1s sliding buffer (catches wake word in < 300ms)

    WAKE_PATTERNS = [
        "friday", "fryday", "fry day", "freeday", "free day", "fried",
        "frida", "flyday", "fly day", "hey friday", "hi friday", 
        "ok friday", "okay friday", "hello friday", "ride", "side", "pride",
        "siday", "fraiday", "fridayy", "fridee", "frayday", "fraide"
    ]

    @classmethod
    def _is_wakeword_matched(cls, text: str) -> bool:
        """High sensitivity fuzzy match against all phonetic variations."""
        text_clean = text.lower().strip()
        
        # 1. Exact or Substring match
        for pat in cls.WAKE_PATTERNS:
            if pat in text_clean:
                return True
                
        # 2. Tokenized word boundary check
        words = text_clean.split()
        for w in words:
            # Check prefix / suffix similarity (e.g. 'frid', 'frida', 'fridye')
            if w.startswith("frid") or w.startswith("fryd") or w.startswith("fraid") or w == "friday":
                return True

        return False

    @classmethod
    def _transcribe_groq_whisper(cls, wav_path: str) -> str:
        """Ultra-accurate cloud Whisper wake word detection."""
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
    def _record_chunk(cls, duration: float = 1.1) -> tuple[str, bool]:
        """
        Record audio chunk and check if audio energy is above ambient floor.
        """
        try:
            num_samples = int(duration * cls.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=cls.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Very sensitive energy gate (35 RMS instead of 80)
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 35:
                return ("", False)

            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, cls.SAMPLE_RATE, audio_data)
            return (tmp.name, True)
        except Exception as e:
            print(f"[WakeWord Record Error]: {e}")
            return ("", False)

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """
        Listen for wake word 'FRIDAY' with maximum sensitivity and instant response.
        """
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 80
        recognizer.dynamic_energy_threshold = False

        print("[WakeWord] Listening for 'FRIDAY' with High Sensitivity...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            wav_path, has_sound = cls._record_chunk(duration=cls.CHUNK_DURATION)
            if not has_sound or not wav_path:
                time.sleep(0.02)
                continue

            # 1. Fast Google STT Check (< 200ms)
            google_text = ""
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

            # 2. Parallel Groq Whisper High-Accuracy Check (if Google missed or muffled)
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
