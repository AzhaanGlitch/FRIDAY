"""
Wake Word Timeout and Energy Threshold Controller
"""

import time

class WakeWordTimeoutController:
    def __init__(self, active_duration_sec: float = 6.0):
        self.active_duration_sec = active_duration_sec
        self.last_activated_timestamp = 0.0

    def activate(self):
        self.last_activated_timestamp = time.time()

    def is_listening_active(self) -> bool:
        return (time.time() - self.last_activated_timestamp) < self.active_duration_sec
