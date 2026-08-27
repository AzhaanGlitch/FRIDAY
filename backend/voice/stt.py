import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import sys
import time
import numpy as np
from backend.voice.tts import VoiceTTS

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

class VoiceSTT:
    """
    Speech Recognition Engine.
    Uses Google Speech API as ultra-fast, robust Primary STT (zero hallucination, perfect Hindi/English words).
    Only Google STT hi-IN / en-IN is used — no Whisper fallback.
    """

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # 0.8s pause to finish phrase quickly
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

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



    def record_and_transcribe(self, max_duration_seconds: float = 10.0, **kwargs) -> dict:
        """
        Record user speech cleanly using sounddevice (100% compatible with Windows sounddevice mic handling).
        """
        if not _mic_lock.acquire(blocking=False):
            return {"success": False, "error": "Another recording is already in progress"}

        wav_path = ""
        try:
            print("[STT] Listening for user command...")
            VoiceTTS.stop_speaking()

            # Record 4.5 second audio buffer using sounddevice (same device stack as WakeWord)
            duration = 4.5
            num_samples = int(duration * self.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Energy check to see if user actually spoke
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 120:
                print("[STT] Silence (ambient noise only).")
                return {"success": False, "error": "Silence"}

            # Save temporary WAV
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, audio_data)
            tmp.close()
            wav_path = tmp.name

            # Google STT (hi-IN / en-IN)
            text = self._transcribe_google(wav_path)

            if text and len(text.strip()) > 1:
                print(f"[STT Recognized]: '{text}'")
                return {"success": True, "text": text}
            
            print("[STT] Sound detected but no clear speech transcribed.")
            return {"success": False, "error": "No speech recognized"}

        except Exception as e:
            print(f"[STT Error]: {e}")
            return {"success": False, "error": str(e)}
        finally:
            _mic_lock.release()
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

stt_engine = VoiceSTT()
