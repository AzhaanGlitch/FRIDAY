import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
import os

class VoiceSTT:
    """Speech-to-Text engine using sounddevice (no PyAudio) for microphone recording."""

    SAMPLE_RATE = 16000

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.recognizer = sr.Recognizer()

    def record_and_transcribe(self, duration_seconds: int = 4) -> dict:
        """Record live audio from system microphone using sounddevice and transcribe to text."""
        wav_path = ""
        try:
            print(f"[STT] Recording audio for {duration_seconds} seconds...")
            audio_data = sd.rec(int(duration_seconds * self.SAMPLE_RATE), samplerate=self.SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()

            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wav.write(tmp.name, self.SAMPLE_RATE, audio_data)
            wav_path = tmp.name

            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                return {"success": True, "text": text}
        except sr.UnknownValueError:
            return {"success": False, "error": "Speech was unintelligible"}
        except sr.RequestError as e:
            return {"success": False, "error": f"API request error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
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
