# FRIDAY Desktop IPC & WebSocket API Specifications

## WebSocket Channel: `ws://localhost:8000/ws`
- **Events Emitted**:
  - `voice_state`: `"listening"` | `"processing"` | `"speaking"` | `"idle"`
  - `intent_executed`: Action name, execution latency, status.
