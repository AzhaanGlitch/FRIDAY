class VoiceSTT:
    """Speech to text engine wrapper."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None

    def initialize(self):
        """Lazy load Faster-Whisper model."""
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            return True
        except Exception as e:
            print(f"[STT] Faster-Whisper init skipped/failed: {e}")
            return False

    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe an audio file to text."""
        if not self.model:
            if not self.initialize():
                return ""
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return ""

stt_engine = VoiceSTT()
