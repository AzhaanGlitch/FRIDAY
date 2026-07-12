"""
Audio Buffer Latency Optimization Utilities
Calculates chunk size thresholds for low-latency streaming recognition.
"""

class AudioBufferOptimizer:
    def __init__(self, sample_rate: int = 16000, target_latency_ms: int = 150):
        self.sample_rate = sample_rate
        self.target_latency_ms = target_latency_ms
        self.chunk_size = int(sample_rate * (target_latency_ms / 1000.0))

    def get_chunk_size(self) -> int:
        return self.chunk_size

    def should_flush(self, current_buffer_len: int) -> bool:
        return current_buffer_len >= self.chunk_size
