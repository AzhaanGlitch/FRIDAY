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
    High-Fidelity Speech-to-Text with Dynamic Voice Activity Detection (VAD).
    - Automatically streams audio chunks until a natural silence pause is detected.
    - Long sentences (up to 12s) won't get cut off prematurely.
    - Locks Hindi + English bilingual decoding to eliminate hallucinations.
    """

    SAMPLE_RATE = 16000
    BILINGUAL_PROMPT = "FRIDAY, tum kaun ho, kaise ho, spotify kholo, open youtube, volume badhao, gaana chalao, terminate system, coding mode, tile chrome left, tile terminal right"

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq's Whisper Large v3 Turbo with bilingual grounding."""
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
                    "prompt": self.BILINGUAL_PROMPT
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=6)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    lower_t = text.lower()
                    if any(phrase in lower_t for phrase in ["продолжение следует", "subtitles by", "amara.org", "you"]):
                        if len(text.split()) <= 2:
                            return ""
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
            else:
                print(f"[STT Groq Warning]: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, max_duration_seconds: float = 12.0, duration_seconds: float = None, **kwargs) -> dict:
        """
        Record live audio with Dynamic Speech Activity Detection (VAD).
        Keeps recording while user is speaking, stops automatically after 1.2s silence pause.
        """
        if duration_seconds is not None:
            max_duration_seconds = duration_seconds

        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            chunk_duration = 0.5
            chunk_samples = int(chunk_duration * self.SAMPLE_RATE)
            recorded_chunks = []
            
            voice_started = False
            silence_chunks = 0
            max_silence_chunks = 3  # ~1.2 to 1.5s of continuous silence after voice starts
            max_total_chunks = int(max_duration_seconds / chunk_duration)

            for _ in range(max_total_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()

                # Calculate RMS energy
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > 65:  # Voice detected
                    if not voice_started:
                        voice_started = True
                        VoiceTTS.stop_speaking() # Instant barge-in!
                    silence_chunks = 0
                    recorded_chunks.append(chunk)
                else:
                    if voice_started:
                        silence_chunks += 1
                        recorded_chunks.append(chunk)
                        # Stop if user finished speaking and paused
                        if silence_chunks >= max_silence_chunks:
                            break
                    else:
                        # Before speech starts, keep only 1 chunk buffer for crisp start
                        if len(recorded_chunks) >= 2:
                            recorded_chunks.pop(0)
                        recorded_chunks.append(chunk)

            if not voice_started or not recorded_chunks:
                return {"success": False, "error": "Silence"}

            # Combine all recorded speech chunks into single audio array
            full_audio = np.concatenate(recorded_chunks, axis=0)

            # Save clean WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, full_audio)
            wav_path = tmp.name

            # 1. Primary: Groq Whisper Large-v3 (Hinglish Grounded)
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
