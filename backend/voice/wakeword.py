import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import time
import os
import sys
import numpy as np
import speech_recognition as sr

class WakeWordDetector:
    """
    Robust Wake Word Detector for 'FRIDAY'.
    - Balanced energy threshold to prevent false-triggers on ambient room noise.
    - Strict, accurate phonetic matching.
    """

    SAMPLE_RATE = 16000
    CHUNK_DURATION = 1.3

    # Clean, accurate wake word patterns
    WAKE_PATTERNS = [
        "friday", "hey friday", "hi friday", "hello friday", 
        "ok friday", "okay friday", "fraiday", "fryday"
    ]

    @classmethod
    def _is_wakeword_matched(cls, text: str) -> bool:
        """Accurate matching to eliminate false alarms."""
        text_clean = text.lower().strip()
        if not text_clean:
            return False

        # Direct pattern match
        for pat in cls.WAKE_PATTERNS:
            if pat in text_clean:
                return True
                
        # Word boundary match
        words = text_clean.split()
        for w in words:
            if w in ["friday", "fryday", "fraiday"] or w.startswith("frid"):
                return True

        return False



    _working_device = None

    @classmethod
    def _get_input_device(cls):
        """Find the most stable audio input device on Windows/macOS/Linux."""
        if cls._working_device is not None:
            return cls._working_device

        try:
            # Check default first
            sd.check_input_settings(channels=1, samplerate=cls.SAMPLE_RATE, dtype='int16')
            cls._working_device = None  # Use system default
            return None
        except Exception:
            pass

        # Try DirectSound or MME devices
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    try:
                        sd.check_input_settings(device=idx, channels=1, samplerate=cls.SAMPLE_RATE, dtype='int16')
                        cls._working_device = idx
                        return idx
                    except Exception:
                        continue
        except Exception:
            pass

        return None

    @classmethod
    def _record_chunk(cls, duration: float = 1.3) -> tuple[str, bool]:
        """Record audio chunk with balanced speech energy gate."""
        try:
            dev = cls._get_input_device()
            num_samples = int(duration * cls.SAMPLE_RATE)
            audio_data = sd.rec(num_samples, samplerate=cls.SAMPLE_RATE, channels=1, dtype='int16', device=dev)
            sd.wait()

            # Balanced threshold: 140 RMS (rejects faint room sounds, breathes, echoes)
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if energy < 140:
                return ("", False)

            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, cls.SAMPLE_RATE, audio_data)
            return (tmp.name, True)
        except Exception as e:
            print(f"[WakeWord Record Error]: {e}")
            cls._working_device = None  # Reset to re-probe next time
            time.sleep(1.0)
            return ("", False)

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """Listen for wake word 'FRIDAY' with high accuracy and low false-positive rate."""
        # Ensure any previous sounddevice session is fully stopped (prevents Windows mic lock)
        try:
            sd.stop()
        except Exception:
            pass

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 180
        recognizer.dynamic_energy_threshold = False

        print("[WakeWord] Listening for 'FRIDAY'...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            wav_path, has_sound = cls._record_chunk(duration=cls.CHUNK_DURATION)
            if not has_sound or not wav_path:
                time.sleep(0.05)
                continue

            # 1. Fast Google STT Check
            try:
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                    google_text = recognizer.recognize_google(audio).lower()
                    print(f"[WakeWord Heard (Fast)]: '{google_text}'")
                    if cls._is_wakeword_matched(google_text):
                        print(f"[WakeWord] Woken up by '{google_text}'!")
                        if wav_path and os.path.exists(wav_path):
                            try:
                                os.unlink(wav_path)
                            except OSError:
                                pass
                        # Release audio device before returning (critical for Windows mic handoff)
                        try:
                            sd.stop()
                        except Exception:
                            pass
                        if sys.platform == "win32":
                            time.sleep(0.3)
                        return True
            except Exception:
                pass



            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

        return False
