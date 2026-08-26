from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import asyncio
from backend.agents.llm_orchestrator import LLMOrchestrator
from backend.automation.system_automation import SystemAutomation
from backend.voice.wakeword import WakeWordDetector
from backend.voice.stt import VoiceSTT
from backend.voice.tts import VoiceTTS
from backend.memory.database import MemoryDatabase
from backend.config.config import settings

app = FastAPI(title="F.R.I.D.A.Y. AI Assistant Backend")

# Initialize persistent memory database
MemoryDatabase.init_db()

# Enable CORS for frontend Desktop GUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_engine = VoiceSTT()
_active_ws_clients: set[WebSocket] = set()

async def broadcast_ws(event: dict):
    """Broadcast real-time voice state events to UI."""
    for ws in list(_active_ws_clients):
        try:
            await ws.send_json(event)
        except Exception:
            _active_ws_clients.discard(ws)

class CommandRequest(BaseModel):
    command: str
    speak_response: bool = True

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "online", "model": settings.LLM_PROVIDER}

@app.get("/api/wait-wakeword")
def wait_for_wakeword(timeout: int = 15):
    """Block until wake word 'FRIDAY' is heard with high sensitivity."""
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

def _play_speech_in_thread(text: str):
    """Helper to synthesize and play speech with exact active state tracking."""
    VoiceTTS.speak(text)

@app.post("/api/listen-mic")
def listen_microphone(duration: float = 12.0):
    """Record live mic audio with dynamic VAD, parse intent, and return response immediately."""
    stt_res = stt_engine.record_and_transcribe(max_duration_seconds=duration)


    if not stt_res.get("success"):
        return {"success": False, "error": stt_res.get("error", "Failed to capture mic audio")}
    
    user_command = stt_res.get("text", "")
    response = LLMOrchestrator.process_command(user_command)

    # If there is a text response, launch TTS in background thread immediately
    text_resp = response.get("text_response", "")
    if text_resp:
        threading.Thread(target=_play_speech_in_thread, args=(text_resp,), daemon=True).start()

    return {
        "success": True,
        "transcribed_command": user_command,
        "response": response
    }

@app.get("/api/is-speaking")
def check_is_speaking():
    """Check if assistant is currently speaking."""
    return {"speaking": VoiceTTS.is_speaking()}

@app.post("/api/interrupt-speech")
def interrupt_speech():
    """Immediately stop/interrupt ongoing speech playback (Barge-in)."""
    VoiceTTS.stop_speaking()
    return {"success": True, "interrupted": True}

@app.post("/api/command")
def execute_command(req: CommandRequest):
    """Process natural language command over REST."""
    response = LLMOrchestrator.process_command(req.command)
    
    if req.speak_response and response.get("text_response"):
        threading.Thread(target=VoiceTTS.speak, args=(response["text_response"],), daemon=True).start()
        
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Realtime WebSocket endpoint for low-latency state and communication."""
    await websocket.accept()
    _active_ws_clients.add(websocket)
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
                
                await websocket.send_json({
                    "type": "response",
                    "content": res.get("text_response", ""),
                    "action": res.get("action_executed", "none"),
                    "result": res.get("result", {})
                })

                if speak and res.get("text_response"):
                    threading.Thread(target=VoiceTTS.speak, args=(res["text_response"],), daemon=True).start()
                    
    except Exception:
        pass
    finally:
        _active_ws_clients.discard(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host=settings.HOST, port=settings.PORT, reload=True)
