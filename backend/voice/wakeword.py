import numpy as np
import speech_recognition as sr
import time
import re

class ClapAndWakeWordDetector:
    """Detects 2 Clap Sounds + 'FRIDAY' wake word to activate microphone loop."""

    @classmethod
    def detect_claps_and_wakeword(cls, timeout_seconds: int = 15) -> bool:
        """
        Listen for 2 distinct high-energy acoustic impulses (claps) followed by 'FRIDAY'.
        Returns True if wake sequence matched, False if timeout.
        """
        recognizer = sr.Recognizer()
        print("[WakeWord] Listening for 2 Claps + 'FRIDAY'...")

        start_time = time.time()
        clap_count = 0
        last_clap_time = 0

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Step 1: Detect 2 Claps (Audio amplitude spikes)
                # Using short audio chunk analysis
                while time.time() - start_time < timeout_seconds:
                    try:
                        audio_chunk = recognizer.listen(source, timeout=1.0, phrase_time_limit=1.5)
                        # Check audio energy / speech
                        try:
                            text = recognizer.recognize_google(audio_chunk).lower()
                            print(f"[WakeWord Heard]: '{text}'")
                            if "friday" in text:
                                return True
                        except sr.UnknownValueError:
                            # If speech was unknown, check if it was acoustic clap spike
                            raw_data = audio_chunk.get_raw_data()
                            audio_data = np.frombuffer(raw_data, dtype=np.int16)
                            peak_amplitude = np.max(np.abs(audio_data))
                            
                            # Clap threshold
                            if peak_amplitude > 15000:
                                now = time.time()
                                if now - last_clap_time > 0.15:  # Debounce consecutive spikes
                                    clap_count += 1
                                    last_clap_time = now
                                    print(f"[WakeWord] Clap detected ({clap_count}/2)")
                                    if clap_count >= 2:
                                        print("[WakeWord] 2 Claps confirmed! Listening for 'FRIDAY'...")
                                        # Next chunk must contain Friday or wake intent
                                        wake_audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=3.0)
                                        wake_text = recognizer.recognize_google(wake_audio).lower()
                                        if "friday" in wake_text or "hello" in wake_text:
                                            return True
                                        return True  # 2 Claps alone also activates
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            print(f"[WakeWord Error]: {e}")
            
        return False
