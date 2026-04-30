#!/bin/bash

echo "================================================"
echo "Healthcare Assistant - Starting Application"
echo "================================================"
echo ""

echo "[1/2] Starting FastAPI Backend..."
echo "Backend will run at: http://localhost:8000"
echo ""

# Start backend in background
uvicorn app.main:app --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo "[2/2] Opening Frontend..."
echo ""

# Open frontend in browser
if command -v open &> /dev/null; then
    # macOS
    open frontend/index.html
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open frontend/index.html
else
    echo "Please open frontend/index.html in your browser"
fi

echo "================================================"
echo "Application Started!"
echo "================================================"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: Opened in your browser"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the backend"
echo ""

# Wait for backend process
wait $BACKEND_PID
