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
        except sr.UnknownValueError:
            return {"success": False, "error": "Speech was unintelligible"}
        except sr.RequestError as e:
            return {"success": False, "error": f"API request error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
