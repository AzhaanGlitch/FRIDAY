import sys
import os
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure backend folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config.config import settings
from backend.agents.llm_orchestrator import LLMOrchestrator
from backend.voice.tts import VoiceTTS
from backend.voice.stt import stt_engine
from backend.automation.system_monitor import SystemMonitor
from backend.memory.database import MemoryDatabase

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)


# Enable CORS for desktop frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str
    speak_response: bool = True

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.VERSION
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "FRIDAY Core API"}

@app.get("/api/system-status")
def get_system_status():
    """Return live system telemetry (CPU, RAM, Disk, Battery)."""
    return SystemMonitor.get_metrics()

@app.get("/api/wait-wakeword")
def wait_for_wakeword(timeout: int = 15):
    """Wait for 'FRIDAY' wake word trigger."""
    from backend.voice.wakeword import WakeWordDetector
    woken = WakeWordDetector.detect_wakeword(timeout_seconds=timeout)
    return {"success": woken, "woken": woken}


@app.get("/api/history")

def get_history(limit: int = 50):
    """Retrieve recent conversation history from SQLite database."""
    return {"success": True, "history": MemoryDatabase.get_recent_history(limit=limit)}

@app.post("/api/clear-history")
def clear_history():
    """Clear stored conversation history."""
    return MemoryDatabase.clear_history()

@app.post("/api/listen-mic")
def listen_microphone(duration: int = 7):
    """Record live mic audio for X seconds, transcribe to command, and execute."""
    stt_res = stt_engine.record_and_transcribe(duration_seconds=duration)
    if not stt_res.get("success"):
        return {"success": False, "error": stt_res.get("error", "Failed to capture mic audio")}
    
    user_command = stt_res.get("text", "")
    response = LLMOrchestrator.process_command(user_command)

    # Run TTS in background thread so we don't block the HTTP response
    tts_duration_ms = 0
    if response.get("text_response"):
        text_resp = response["text_response"]
        tts_duration_ms = max(3000, len(text_resp) * 65)
        threading.Thread(target=VoiceTTS.speak, args=(text_resp,), daemon=True).start()
        
    return {
        "success": True,
        "transcribed_command": user_command,
        "response": response,
        "tts_duration_ms": tts_duration_ms
    }



@app.post("/api/command")
def execute_command(req: CommandRequest):
    """Process natural language command over REST."""
    response = LLMOrchestrator.process_command(req.command)
    
    if req.speak_response and response.get("text_response"):
        # Run TTS in background thread so REST response is not blocked
        threading.Thread(target=VoiceTTS.speak, args=(response["text_response"],), daemon=True).start()
        
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Realtime WebSocket endpoint for low-latency communication."""
    await websocket.accept()
    await websocket.send_json({
        "type": "status",
        "message": "Connected to FRIDAY AI Backend"
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            command_type = data.get("type", "text")
            
            if command_type == "text":
                text_input = data.get("content", "")
                speak = data.get("speak", True)
                
                res = LLMOrchestrator.process_command(text_input)
                
                # Send response to UI immediately (never block on TTS)
                await websocket.send_json({
                    "type": "response",
                    "content": res.get("text_response", ""),
                    "action": res.get("action_executed", "none"),
                    "result": res.get("result", {})
                })

                # Run TTS in background thread AFTER sending response
                if speak and res.get("text_response"):
                    threading.Thread(target=VoiceTTS.speak, args=(res["text_response"],), daemon=True).start()
                
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")

