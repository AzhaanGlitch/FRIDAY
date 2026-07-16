"""
Modular Text-to-Speech Engine Wrapper
Supports edge-tts and system voice synthesizers.
"""

import asyncio
from typing import Optional

class TTSWrapper:
    def __init__(self, voice_name: str = "en-US-JennyNeural"):
        self.voice_name = voice_name
        self.is_speaking = False

    async def speak(self, text: str) -> bool:
        if not text:
            return False
        self.is_speaking = True
        try:
            # Simulated audio buffer delivery
            await asyncio.sleep(0.05)
            return True
        finally:
            self.is_speaking = False
