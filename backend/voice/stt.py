import speech_recognition as sr
import os
import sys

class VoiceSTT:
    """Speech-to-Text engine supporting microphone input and Faster-Whisper/SpeechRecognition."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.recognizer = sr.Recognizer()

    def record_and_transcribe(self, duration_seconds: int = 4) -> dict:
        """Record live audio from system microphone and transcribe to text."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"[STT] Recording audio for {duration_seconds} seconds...")
                audio = self.recognizer.record(source, duration=duration_seconds)
                
                # Transcribe using SpeechRecognition default sphinx/google fallback engine
                text = self.recognizer.recognize_google(audio)
                return {"success": True, "text": text}
        except AttributeError as e:
            if "pyaudio" in str(e).lower() or "microphone" in str(e).lower():
                return {"success": False, "error": "PyAudio binary wheel build failed on Python 3.14. Please use Python 3.11/3.12 or type text commands into FRIDAY Console."}
            return {"success": False, "error": str(e)}
        except OSError as e:
            if "pyaudio" in str(e).lower() or "no default input device" in str(e).lower():
                return {"success": False, "error": "PyAudio / Microphone hardware device not available on this Python 3.14 installation."}
            return {"success": False, "error": str(e)}
        except sr.UnknownValueError:
            return {"success": False, "error": "Speech was unintelligible"}
        except sr.RequestError as e:
            return {"success": False, "error": f"API request error: {e}"}
        except Exception as e:
            err_msg = str(e)
            if "pyaudio" in err_msg.lower():
                return {"success": False, "error": "PyAudio is not installed for Python 3.14. Text commands remain fully supported."}
            return {"success": False, "error": err_msg}

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
