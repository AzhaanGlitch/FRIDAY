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
    High-Fidelity Speech-to-Text with Continuous Speech Buffer & Robust VAD.
    - Does NOT cut off while user is speaking (allows natural pauses up to 1.6 seconds).
    - Captures long, complex tiling commands smoothly up to 15s.
    """

    SAMPLE_RATE = 16000
    BILINGUAL_PROMPT = "FRIDAY, tum kaun ho, spotify kholo, open photos, visual studio code, terminal, google chrome, tile chrome left, tile photos top left, vs code top right, terminal bottom right"

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _transcribe_groq_whisper(self, wav_path: str) -> str:
        """Transcribe audio using Groq's Whisper Large v3 Turbo."""
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
                res = requests.post(url, headers=headers, files=files, data=data, timeout=8)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    lower_t = text.lower()
                    # Filter phantom hallucinations on ambient noise
                    if any(phrase in lower_t for phrase in ["продолжение следует", "subtitles by", "amara.org", "you", "thank you", "thanks for watching", "bye"]):
                        if len(text.split()) <= 2:
                            return ""
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
            else:
                print(f"[STT Groq Warning]: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, max_duration_seconds: float = 15.0, duration_seconds: float = None, **kwargs) -> dict:
        """
        Record live audio until user finishes full command.
        Waits for clear speech (>130 RMS), allows natural breathing pauses (~1.6s of silence), then transcribes.
        """
        if duration_seconds is not None:
            max_duration_seconds = max(max_duration_seconds, duration_seconds)

        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            chunk_duration = 0.35
            chunk_samples = int(chunk_duration * self.SAMPLE_RATE)
            recorded_chunks = []
            
            voice_started = False
            silence_chunks = 0
            # 5 consecutive silence chunks = 5 * 0.35s = ~1.75 seconds pause needed to finish speaking
            max_silence_chunks = 5
            max_total_chunks = int(max_duration_seconds / chunk_duration)

            for _ in range(max_total_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()

                # Calculate RMS energy
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                # Human voice threshold (130 RMS)
                if energy > 130:
                    if not voice_started:
                        voice_started = True
                        VoiceTTS.stop_speaking()
                    silence_chunks = 0
                    recorded_chunks.append(chunk)
                else:
                    if voice_started:
                        silence_chunks += 1
                        recorded_chunks.append(chunk)
                        # Finish ONLY when user genuinely stopped speaking for 1.75s
                        if silence_chunks >= max_silence_chunks:
                            break

            if not voice_started or len(recorded_chunks) < 3:
                return {"success": False, "error": "Silence"}

            # Combine recorded speech chunks
            full_audio = np.concatenate(recorded_chunks, axis=0)

            # Save clean WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, full_audio)
            wav_path = tmp.name

            # Transcribe with Whisper
            text = self._transcribe_groq_whisper(wav_path)

            if not text:
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio)
                        print(f"[STT Google Fallback]: '{text}'")
                except Exception:
                    pass

            if text and len(text.strip()) > 1:
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
