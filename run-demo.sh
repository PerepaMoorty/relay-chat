#!/usr/bin/env bash
set -e

echo "========================================================"
echo "        Relay - Real-Time Chat Application Demo"
echo "========================================================"
echo ""

# 1. Check Python installation
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.11+."
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -f ".venv/bin/activate" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
fi

echo "[*] Activating virtual environment..."
source .venv/bin/activate

# 3. Install Dependencies
echo "[*] Installing / checking dependencies..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt

# 4. Seed Database if Missing
if [ ! -f "instance/relay.db" ]; then
    echo "[*] Seeding demo database (alice, bob, carol, admin)..."
    flask --app run seed-demo || echo "[WARNING] Seed-demo CLI not yet ready; database will initialize on server start."
else
    echo "[*] Database instance/relay.db already exists."
fi

# 5. Launch Relay Server
echo ""
echo "========================================================"
echo " Server starting at: http://localhost:5000"
echo " Press Ctrl+C to terminate the server."
echo "========================================================"
echo ""

$PYTHON_CMD run.py
