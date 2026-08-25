import speech_recognition as sr
import time

class WakeWordDetector:
    """Detects 'FRIDAY' wake word to activate active voice microphone loop safely without C-extension memory leaks."""

    _shared_microphone = None

    @classmethod
    def get_microphone(cls):
        if cls._shared_microphone is None:
            try:
                cls._shared_microphone = sr.Microphone()
            except Exception as e:
                print(f"[WakeWord Mic Init Error]: {e}")
                return None
        return cls._shared_microphone

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """
        Listen for speech containing 'FRIDAY' (or 'hello friday').
        Returns True if wake word matched, False if timeout.
        """
        recognizer = sr.Recognizer()
        print("[WakeWord] Listening for 'FRIDAY'...")

        mic = cls.get_microphone()
        if mic is None:
            return False

        start_time = time.time()

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                while time.time() - start_time < timeout_seconds:
                    try:
                        audio_chunk = recognizer.listen(source, timeout=2.0, phrase_time_limit=2.5)
                        try:
                            text = recognizer.recognize_google(audio_chunk).lower()
                            print(f"[WakeWord Heard]: '{text}'")
                            if "friday" in text or "friday" in text.replace(" ", ""):
                                print("[WakeWord] Woken up by 'FRIDAY'!")
                                return True
                        except sr.UnknownValueError:
                            continue
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            print(f"[WakeWord Loop Error]: {e}")
            
        return False
