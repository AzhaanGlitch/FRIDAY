#!/bin/bash

# FRIDAY Setup & Run Script for macOS/Linux

echo "=========================================="
echo "    F.R.I.D.A.Y. AI Assistant Setup"
echo "=========================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Setup Backend
echo "[1/4] Setting up Python Backend..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing backend dependencies..."
./venv/bin/pip install -r requirements.txt

# 2. Setup Frontend
echo "[2/4] Setting up Desktop Frontend..."
cd "$PROJECT_ROOT/desktop"
if [ ! -d "node_modules" ]; then
    echo "Installing node dependencies..."
    npm install --legacy-peer-deps
fi

# 3. Launch Backend in background
echo "[3/4] Starting FRIDAY Backend Server..."
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
./backend/venv/bin/python3 backend/run_backend.py &
BACKEND_PID=$!


sleep 2

# 4. Launch Desktop Application (Tauri)
echo "[4/4] Starting FRIDAY Desktop Application (Tauri)..."
cd "$PROJECT_ROOT/desktop"
npm run desktop:dev

# Cleanup on exit
kill $BACKEND_PID
