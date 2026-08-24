import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure backend folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config.config import settings
from backend.agents.llm_orchestrator import LLMOrchestrator
from backend.voice.tts import VoiceTTS

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

@app.post("/api/command")
def execute_command(req: CommandRequest):
    """Process natural language command over REST."""
    response = LLMOrchestrator.process_command(req.command)
    
    if req.speak_response and response.get("text_response"):
        VoiceTTS.speak(response["text_response"])
        
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
                
                if speak and res.get("text_response"):
                    VoiceTTS.speak(res["text_response"])
                    
                await websocket.send_json({
                    "type": "response",
                    "content": res.get("text_response", ""),
                    "action": res.get("action_executed", "none"),
                    "result": res.get("result", {})
                })
                
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")
