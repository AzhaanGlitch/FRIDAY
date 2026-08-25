import speech_recognition as sr
import time

class WakeWordDetector:
    """Detects 'FRIDAY' wake word to activate active voice microphone loop."""

    @classmethod
    def detect_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """
        Listen for speech containing 'FRIDAY' (or 'hello friday').
        Returns True if wake word matched, False if timeout.
        """
        recognizer = sr.Recognizer()
        print("[WakeWord] Listening for 'FRIDAY'...")

        start_time = time.time()

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                while time.time() - start_time < timeout_seconds:
                    try:
                        audio_chunk = recognizer.listen(source, timeout=3.0, phrase_time_limit=3.0)
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
            print(f"[WakeWord Error]: {e}")
            
        return False
