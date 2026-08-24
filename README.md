# FRIDAY AI Assistant

Cross-Platform Voice-Controlled AI Computer Assistant inspired by Iron Man.

## Directory Structure

```
FRIDAY/
├── desktop/                # Tauri & React Desktop Application
│   ├── src/                # React / TypeScript source code
│   │   ├── App.tsx         # Desktop UI console with voice orb & Tauri IPC
│   │   ├── main.tsx        # React entry point
│   │   └── index.css       # Core theme tokens and animations
│   ├── src-tauri/          # Rust Native Desktop Shell & Tauri Config
│   │   ├── src/main.rs     # Rust desktop process & native handlers
│   │   ├── Cargo.toml      # Rust package manifest
│   │   └── tauri.conf.json # Tauri window & app configuration
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/                # Python Core AI Backend & OS Automation
│   ├── api/                # FastAPI application & WebSockets
│   │   └── main.py
│   ├── voice/              # Voice subsystem
│   │   ├── stt.py          # Speech recognition
│   │   └── tts.py          # Speech synthesis
│   ├── agents/             # Intent parser & LLM orchestrator
│   │   └── llm_orchestrator.py
│   ├── automation/         # System automation adapters
│   │   ├── mac_automation.py
│   │   └── system_automation.py
│   ├── config/             # Configuration & environment settings
│   ├── requirements.txt
│   └── run_backend.py      # Backend launch script
├── docs/                   # Documentation and project blueprints
└── tests/                  # Backend unit and integration tests
```

## Running the Phase 1 Core MVP (Tauri Desktop App)

### Quick Start (Automated Script)
- **Windows**: Double click or run `setup_and_run.bat`
- **macOS / Linux**: Run `./setup_and_run.sh`

### Manual Launch

#### 1. Start the Backend API Server
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 run_backend.py
```
The backend server will run on `http://localhost:8000`.

#### 2. Start the Tauri Desktop Application
```bash
cd desktop
npm install
npm run desktop:dev
```
This launches the native Tauri desktop window wrapping the FRIDAY AI Assistant interface.