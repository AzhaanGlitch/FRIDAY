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

def _drain_mic_buffer(sample_rate: int = 16000, drain_duration: float = 0.4):
    """Silently read and discard mic input to flush any stale/residual audio (e.g. TTS echo)."""
    try:
        drain_samples = int(drain_duration * sample_rate)
        sd.rec(drain_samples, samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
    except Exception:
        pass

def _wait_for_tts_silence(max_wait: float = 8.0):
    """Block until VoiceTTS finishes speaking, so mic calibration isn't poisoned by playback audio."""
    start = time.time()
    while VoiceTTS.is_speaking() and (time.time() - start) < max_wait:
        time.sleep(0.1)
    # Extra brief settle time for audio hardware to fully quiet down
    time.sleep(0.15)

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
        self.recognizer.energy_threshold = 50
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.2
        self.recognizer.pause_threshold = 1.5
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8

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
                    "prompt": "User voice command in English or Hindi: open youtube, open google chrome, tile windows, start coding, kaun se apps hain"
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=8)

            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    lower_t = text.lower().strip()
                    # Filter phantom hallucinations & single-word noise artifacts
                    if any(phrase in lower_t for phrase in ["subtitles by", "amara.org", "thank you for watching", "bye"]):
                        return ""
                    if lower_t in ["y", "so", "right.", "sorry.", "great.", "cool.", "gracias.", "view.", "what", "yeah.", "thank you."]:
                        return ""
                    print(f"[STT Groq Whisper]: '{text}'")
                    return text
        except Exception as e:
            print(f"[STT Groq Error]: {e}")

        return ""

    def record_and_transcribe(self, max_duration_seconds: float = 12.0, duration_seconds: float = None, **kwargs) -> dict:
        """
        Record live mic audio via sounddevice.
        Uses intelligent VAD:
        - Adaptive noise floor calibration
        - Pre-roll buffer to prevent cutting off the beginning of words
        - Requires genuine speech before starting capture
        - Sustains recording until user completes their sentence with a 1.25s pause
        """
        if duration_seconds is not None:
            max_duration_seconds = max(max_duration_seconds, duration_seconds)

        # Wait up to 5s for the lock (in case wake word detector just released the mic)
        if not _mic_lock.acquire(blocking=True, timeout=5.0):
            print("[VoiceSTT]: Mic lock acquisition timed out — another recording still active")
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            # Step 0: Wait for TTS to finish and drain residual mic buffer
            # This prevents the calibration from being poisoned by echo/TTS playback
            _wait_for_tts_silence()
            _drain_mic_buffer(self.SAMPLE_RATE)

            chunk_duration = 0.25
            chunk_samples = int(chunk_duration * self.SAMPLE_RATE)
            
            # Step 1: Calibration - sample ambient noise level (first 3 chunks for accuracy)
            ambient_samples = []
            for _ in range(3):
                c = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()
                ambient_samples.append(c)
            
            ambient_energy = np.sqrt(np.mean(np.concatenate(ambient_samples).astype(np.float32) ** 2))
            # Adaptive threshold: ambient floor + 35 RMS, with minimum threshold of 60 RMS
            # Much lower than before to ensure normal/soft speech is captured
            speech_threshold = max(60.0, ambient_energy + 35.0)
            print(f"[VoiceSTT]: Ambient energy={ambient_energy:.1f}, Speech threshold={speech_threshold:.1f}")

            # Only keep the last 2 ambient chunks as pre-roll (discard extra calibration chunk)
            recorded_chunks = list(ambient_samples[-2:])  # pre-roll buffer
            voice_started = False
            consecutive_speech_chunks = 0
            silence_chunks = 0
            max_silence_chunks = 5  # 5 * 0.25s = 1.25s silence to end phrase
            max_total_chunks = int(max_duration_seconds / chunk_duration)

            for _ in range(max_total_chunks - 2):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()

                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > speech_threshold:
                    consecutive_speech_chunks += 1
                    silence_chunks = 0
                    recorded_chunks.append(chunk)

                    if consecutive_speech_chunks >= 2 and not voice_started:
                        voice_started = True
                        VoiceTTS.stop_speaking()
                else:
                    if voice_started:
                        silence_chunks += 1
                        recorded_chunks.append(chunk)
                        if silence_chunks >= max_silence_chunks:
                            break
                    else:
                        consecutive_speech_chunks = 0
                        # Keep rolling 2-chunk pre-roll
                        recorded_chunks = recorded_chunks[-2:]
                        recorded_chunks.append(chunk)

            if not voice_started or len(recorded_chunks) < 4:
                print(f"[VoiceSTT]: No speech detected (voice_started={voice_started}, chunks={len(recorded_chunks)})")
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
