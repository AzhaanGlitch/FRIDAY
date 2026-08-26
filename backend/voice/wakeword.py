import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import time
import os

class WakeWordDetector:
    """Detects 'FRIDAY' wake word using sounddevice (no PyAudio) to prevent SIGSEGV crashes."""

    SAMPLE_RATE = 16000

    @classmethod
    def _record_chunk(cls, duration: float = 1.2) -> str:
        """Record a short 1.2s audio chunk to a temp WAV file."""
        try:
            audio_data = sd.rec(int(duration * cls.SAMPLE_RATE), samplerate=cls.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, cls.SAMPLE_RATE, audio_data)
            return tmp.name
        except Exception as e:
            print(f"[WakeWord Record Error]: {e}")
            return ""

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """
        Listen for speech containing 'FRIDAY'.
        Returns True if wake word matched, False if timeout.
        """
        recognizer = sr.Recognizer()
        print("[WakeWord] Listening for 'FRIDAY'...")

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            wav_path = cls._record_chunk(duration=1.2)
            if not wav_path:
                time.sleep(0.1)
                continue
            try:
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"[WakeWord Heard]: '{text}'")
                    if "friday" in text:
                        print("[WakeWord] Woken up by 'FRIDAY'!")
                        return True
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[WakeWord API Error]: {e}")
            except Exception as e:
                print(f"[WakeWord Transcribe Error]: {e}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

        return False
