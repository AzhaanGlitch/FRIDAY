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

# Global Whisper Model Cache
_whisper_model = None

def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            print("[STT] Initializing local Whisper (tiny) model...")
            _whisper_model = whisper.load_model("tiny")
        except Exception as e:
            print(f"[STT] Local Whisper init notice: {e}")
    return _whisper_model

class VoiceSTT:
    """
    Ultra-Fast & Accurate Speech-to-Text Engine:
    1. Groq Cloud Whisper API (whisper-large-v3-turbo) -> ~200ms latency & highest accuracy
    2. Local Whisper (tiny) -> 100% offline fallback
    3. Google Speech Recognition -> emergency fallback
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = True

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq's ultra-fast Whisper Large v3 Turbo cloud API."""
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
                    "temperature": 0.0,
                    "prompt": "open spotify, open youtube, open chrome, volume, music, coding mode, terminate system"
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=5)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    print(f"[STT Groq Whisper Large-v3]: '{text}'")
                    return text
            else:
                print(f"[STT Groq Whisper Warning]: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[STT Groq Whisper Error]: {e}")

        return ""

    def _transcribe_local_whisper(self, wav_path: str) -> str:
        """Transcribe audio using local Whisper model."""
        w_model = _get_whisper()
        if not w_model:
            return ""
        try:
            result = w_model.transcribe(wav_path, fp16=False, language="en")
            text = result.get("text", "").strip()
            if text:
                print(f"[STT Local Whisper]: '{text}'")
                return text
        except Exception as e:
            print(f"[STT Local Whisper Error]: {e}")
        return ""

    def record_and_transcribe(self, max_duration_seconds: int = 6, silence_limit_seconds: float = 0.9) -> dict:
        """Record audio with VAD silence cutoff and transcribe with Whisper."""
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            chunk_duration = 0.2
            chunk_samples = int(chunk_duration * self.SAMPLE_RATE)
            max_chunks = int(max_duration_seconds / chunk_duration)
            silence_chunks_needed = int(silence_limit_seconds / chunk_duration)

            audio_chunks = []
            has_speech_started = False
            silent_chunk_count = 0

            print(f"[STT] Listening for command (Cloud Whisper + VAD)...")

            for _ in range(max_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()
                audio_chunks.append(chunk)

                # Energy check
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > 100:  # Active speech
                    has_speech_started = True
                    silent_chunk_count = 0
                elif has_speech_started:
                    silent_chunk_count += 1
                    if silent_chunk_count >= silence_chunks_needed:
                        print("[STT] Silence detected — cutting recording.")
                        break

            if not audio_chunks:
                return {"success": False, "error": "No audio captured"}

            full_audio = np.concatenate(audio_chunks, axis=0)
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, full_audio)
            wav_path = tmp.name

            # 1. Primary: Groq Whisper Cloud (Ultra-accurate & 200ms fast)
            text = self._transcribe_groq_whisper(wav_path)

            # 2. Secondary: Local Whisper
            if not text:
                text = self._transcribe_local_whisper(wav_path)

            # 3. Tertiary: Google Speech
            if not text:
                with sr.AudioFile(wav_path) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    print(f"[STT Google Transcribed]: '{text}'")

            if text:
                return {"success": True, "text": text}
            return {"success": False, "error": "No speech recognized"}

        except sr.UnknownValueError:
            return {"success": False, "error": "Speech was unintelligible"}
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
