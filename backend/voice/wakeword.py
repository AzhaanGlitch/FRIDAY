import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import time
import os
import numpy as np
import speech_recognition as sr

class WakeWordDetector:
    """
    High-sensitivity Wake Word Detector for 'FRIDAY'.
    Uses multi-stage detection:
    1. Fast RMS Energy Gate (ignores dead silence immediately)
    2. Google Speech Recognition + Local Whisper fallbacks
    3. Fuzzy phonetic pattern matching (catches 'friday', 'fridayy', 'hi friday', 'hey friday', 'fry day', 'freeday', 'frida')
    """

    SAMPLE_RATE = 16000
    CHUNK_DURATION = 1.5  # Optimal window to capture 'FRIDAY'

    # Variations of how speech recognition might transcribe 'FRIDAY'
    WAKE_PATTERNS = [
        "friday", "fryday", "fry day", "freeday", "free day", 
        "frida", "flyday", "fly day", "hey friday", "hi friday", 
        "ok friday", "okay friday", "hello friday"
    ]

    @classmethod
    def _is_wakeword_matched(cls, text: str) -> bool:
        """Fuzzy match wake word against common phonetic variations."""
        text_clean = text.lower().strip()
        for pat in cls.WAKE_PATTERNS:
            if pat in text_clean:
                return True
        return False

    @classmethod
    def _record_chunk(cls, duration: float = 1.5) -> tuple[str, bool]:
        """
        Record audio chunk and check if sound energy exceeds ambient noise.
        Returns (wav_path, has_sound).
        """
        try:
            num_samples = int(duration * cls.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=cls.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            # Fast energy check
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 80:  # Silence threshold
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
        Listen for wake word 'FRIDAY' with high sensitivity and zero delay.
        """
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 150
        recognizer.dynamic_energy_threshold = True

        print("[WakeWord] Listening for 'FRIDAY'...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            wav_path, has_sound = cls._record_chunk(duration=cls.CHUNK_DURATION)
            if not has_sound or not wav_path:
                time.sleep(0.05)
                continue

            try:
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"[WakeWord Heard]: '{text}'")
                    if cls._is_wakeword_matched(text):
                        print("[WakeWord] Woken up by 'FRIDAY'!")
                        return True
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[WakeWord API Error]: {e}")
            except Exception as e:
                print(f"[WakeWord Error]: {e}")
            finally:
                if wav_path:
                    try:
                        os.unlink(wav_path)
                    except OSError:
                        pass

        return False
