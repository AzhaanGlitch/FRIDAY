import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import numpy as np

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

# Global Whisper Model Cache
_whisper_model = None

def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            print("[STT] Loading Whisper (tiny) model for ultra-accurate speech recognition...")
            _whisper_model = whisper.load_model("tiny")
        except Exception as e:
            print(f"[STT] Whisper load notice: {e}")
    return _whisper_model

class VoiceSTT:
    """Speech-to-Text engine using Whisper AI + Google fallback with Smart Silence Detection (VAD)."""

    SAMPLE_RATE = 16000

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = True

    def record_and_transcribe(self, max_duration_seconds: int = 7, silence_limit_seconds: float = 1.0) -> dict:
        """Record live audio with VAD silence detection and transcribe with Whisper/Google."""
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

            print(f"[STT] Listening for command (Whisper + VAD)...")

            for _ in range(max_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()
                audio_chunks.append(chunk)

                # RMS energy
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > 120:  # Speech threshold
                    has_speech_started = True
                    silent_chunk_count = 0
                elif has_speech_started:
                    silent_chunk_count += 1
                    if silent_chunk_count >= silence_chunks_needed:
                        print("[STT] End of speech detected — stopping recording immediately.")
                        break

            if not audio_chunks:
                return {"success": False, "error": "No audio captured"}

            full_audio = np.concatenate(audio_chunks, axis=0)
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, full_audio)
            wav_path = tmp.name

            # 1. Try Whisper First (Most accurate)
            w_model = _get_whisper()
            if w_model:
                try:
                    result = w_model.transcribe(wav_path, fp16=False, language="en")
                    text = result.get("text", "").strip()
                    if text:
                        print(f"[STT Whisper Transcribed]: '{text}'")
                        return {"success": True, "text": text}
                except Exception as e:
                    print(f"[STT Whisper Error, falling back to Google]: {e}")

            # 2. Fallback to Google STT
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                print(f"[STT Google Transcribed]: '{text}'")
                return {"success": True, "text": text}

        except sr.UnknownValueError:
            return {"success": False, "error": "Speech was unintelligible"}
        except sr.RequestError as e:
            return {"success": False, "error": f"API request error: {e}"}
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
