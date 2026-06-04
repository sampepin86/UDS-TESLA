#!/bin/bash
# Tesla UDS Diagnostic Tool - Quick Start Script
# Launches both backend (Python 2.7) and frontend (Python 3) in separate terminals

set -e

WORKSPACE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Tesla UDS Diagnostic Tool - Quick Start"
echo "========================================"
echo ""
echo "This script will launch:"
echo "  1. UDS Bridge Backend (Python 2.7) on port 5000"
echo "  2. GUI Frontend (Python 3) in CustomTkinter"
echo ""

# Check if uds-py27 environment exists
echo "Checking for uds-py27 conda environment..."
if ! conda env list | grep -q "uds-py27"; then
    echo "ERROR: uds-py27 environment not found"
    echo ""
    echo "Please create it first with:"
    echo "  CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7"
    echo "  conda activate uds-py27"
    echo "  pip install pyserial enum34"
    exit 1
fi

echo "✓ uds-py27 environment found"
echo ""

# Check if customtkinter is installed
echo "Checking for CustomTkinter in Python 3..."
if ! python3 -c "import customtkinter" 2>/dev/null; then
    echo "ERROR: CustomTkinter not installed"
    echo ""
    echo "Please install it with:"
    echo "  pip install customtkinter"
    exit 1
fi

echo "✓ CustomTkinter found"
echo ""

# Launch backend in background
echo "Starting UDS Bridge Backend..."
terminal_open_backend() {
    if command -v open &> /dev/null; then
        # macOS
        open -a Terminal <<EOF
            cd "$WORKSPACE" && conda activate uds-py27 && python uds_bridge.py
EOF
    else
        # Linux
        gnome-terminal -- bash -c "cd $WORKSPACE && conda activate uds-py27 && python uds_bridge.py" &
    fi
}

# Give user option to launch backend
echo "Would you like to:"
echo "  1) Launch both backend and GUI (requires manual terminal for backend)"
echo "  2) Just show setup instructions"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "IMPORTANT: Open a new terminal and run:"
    echo ""
    echo "  conda activate uds-py27"
    echo "  cd $WORKSPACE"
    echo "  python uds_bridge.py"
    echo ""
    echo "This will start the backend on 127.0.0.1:5000"
    echo ""
    echo "Press ENTER to launch the GUI..."
    read -r
    
    cd "$WORKSPACE"
    python3 gui.py
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "Setup Instructions:"
    echo "=================="
    echo ""
    echo "Terminal 1 (Backend - Python 2.7):"
    echo "  cd $WORKSPACE"
    echo "  conda activate uds-py27"
    echo "  python uds_bridge.py"
    echo ""
    echo "Terminal 2 (Frontend - Python 3):"
    echo "  cd $WORKSPACE"
    echo "  python3 gui.py"
    echo ""
    exit 0
else
    echo "Invalid choice"
    exit 1
fi
