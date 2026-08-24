# FRIDAY AI Assistant

Cross-Platform Voice-Controlled AI Computer Assistant inspired by Iron Man.

## Directory Structure

```
FRIDAY/
├── desktop/                # Tauri & React Frontend Interface
│   ├── src/                # React / TypeScript source code
│   │   ├── components/     # UI components
│   │   ├── services/       # WebSocket & REST service connectors
│   │   ├── App.tsx         # Main UI console with glassmorphism & voice orb
│   │   ├── main.tsx        # React entry point
│   │   └── index.css       # Core theme tokens and animations
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/                # Python Core AI Backend & OS Automation
│   ├── api/                # FastAPI application & WebSockets
│   │   └── main.py
│   ├── voice/              # Voice subsystem
│   │   ├── stt.py          # Faster-Whisper speech recognition
│   │   └── tts.py          # macOS native & pyttsx3 speech synthesis
│   ├── agents/             # Intent parser & LLM orchestrator
│   │   └── llm_orchestrator.py
│   ├── automation/         # System automation adapters
│   │   ├── mac_automation.py # macOS native open, osascript, screenshot
│   │   └── system_automation.py # Unified cross-platform automation router
│   ├── config/             # Configuration & environment settings
│   │   └── config.py
│   ├── requirements.txt
│   └── run_backend.py      # Server launch entry point
├── docs/                   # Documentation and project blueprints
└── tests/                  # Backend unit and integration tests
```

## Running the Phase 1 Core MVP

### 1. Start the Backend API Server
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run_backend.py
```
The backend server will run on `http://localhost:8000`.

### 2. Start the Desktop Frontend
```bash
cd desktop
npm install
npm run dev
```
The React desktop interface will open on `http://localhost:3000`.