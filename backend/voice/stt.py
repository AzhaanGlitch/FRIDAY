import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import threading
import os
import numpy as np

# Global mutex — only one mic recording at a time
_mic_lock = threading.Lock()

class VoiceSTT:
    """Speech-to-Text engine using sounddevice with Smart Silence Detection (VAD)."""

    SAMPLE_RATE = 16000

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.recognizer = sr.Recognizer()

    def record_and_transcribe(self, max_duration_seconds: int = 5, silence_limit_seconds: float = 0.8) -> dict:
        """Record live audio until user stops speaking or max duration is reached."""
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

            print(f"[STT] Listening for command (smart silence detection)...")

            for _ in range(max_chunks):
                chunk = sd.rec(chunk_samples, samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()
                audio_chunks.append(chunk)

                # Calculate RMS energy of current 0.2s audio chunk
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > 200:  # Speech detected threshold
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

            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                print(f"[STT Transcribed]: '{text}'")
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

    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe an audio file to text."""
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio)
        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return ""

stt_engine = VoiceSTT()
