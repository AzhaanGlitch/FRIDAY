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
    Ultra-Reliable Cross-Platform Speech Recognition Engine (macOS & Windows).
    Uses sounddevice for 100% C-level PortAudio capturing (bypasses PyAudio issues on Windows).
    - Energy-based Voice Activity Detection (VAD) with 1.8s speech hold.
    - Google Cloud Multi-lingual (hi-IN / en-IN) as Primary STT with zero hallucinations.
    - Groq Whisper Large-v3 as high-accuracy secondary fallback.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _transcribe_google(self, wav_path: str) -> str:
        """Transcribe using Google Speech Recognition (High-accuracy bilingual Hindi+English)."""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                
                # 1. Hindi-India (Detects pure Hindi, Hinglish and English commands seamlessly)
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
                    if any(phrase in lower_t for phrase in ["subtitles by", "amara.org", "thank you for watching", "bye"]):
                        return ""
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, max_duration_seconds: float = 15.0, duration_seconds: float = None, **kwargs) -> dict:
        """
        Record live mic audio via sounddevice (works on 100% Windows & macOS without PyAudio).
        Listens until user genuinely finishes speaking with a comfortable 1.8s pause.
        """
        if duration_seconds is not None:
            max_duration_seconds = max(max_duration_seconds, duration_seconds)

        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            chunk_duration = 0.3
            chunk_samples = int(chunk_duration * self.SAMPLE_RATE)
            recorded_chunks = []
            
            voice_started = False
            silence_chunks = 0
            # 6 consecutive silence chunks = 6 * 0.3s = 1.8 seconds pause needed to finish speaking
            max_silence_chunks = 6
            max_total_chunks = int(max_duration_seconds / chunk_duration)

            for _ in range(max_total_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()

                # Calculate RMS energy
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                # Human voice threshold (75 RMS to support quiet Windows laptop mics)
                if energy > 75:
                    if not voice_started:
                        voice_started = True
                        VoiceTTS.stop_speaking()
                    silence_chunks = 0
                    recorded_chunks.append(chunk)
                else:
                    if voice_started:
                        silence_chunks += 1
                        recorded_chunks.append(chunk)
                        if silence_chunks >= max_silence_chunks:
                            break

            if not voice_started or len(recorded_chunks) < 2:
                return {"success": False, "error": "Silence"}

            # Combine recorded speech chunks
            full_audio = np.concatenate(recorded_chunks, axis=0)

            # Save clean WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, full_audio)
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
            print(f"[VoiceSTT Capture Error]: {e}")
            return {"success": False, "error": str(e)}
        finally:
            _mic_lock.release()
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

stt_engine = VoiceSTT()
