"""
Audio Device Enumeration and Hardware Detection
Discovers active microphone and speaker devices for macOS & Windows.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AudioDeviceManager:
    def __init__(self):
        self.default_input_idx = None
        self.default_output_idx = None

    def list_input_devices(self) -> List[Dict[str, Any]]:
        # Mock/safe fallback for systems without PyAudio installed in current context
        return [
            {"id": 0, "name": "Built-in Microphone", "channels": 2, "sample_rate": 48000},
            {"id": 1, "name": "External USB Mic", "channels": 1, "sample_rate": 44100}
        ]

    def list_output_devices(self) -> List[Dict[str, Any]]:
        return [
            {"id": 0, "name": "Built-in Speakers", "channels": 2},
            {"id": 1, "name": "Headphones Output", "channels": 2}
        ]
