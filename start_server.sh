#!/bin/bash

# Start Business Location Advisor API Server

echo "🚀 Starting Business Location Advisor API Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_api.txt --quiet

# Start the server
echo ""
echo "✅ Starting FastAPI server with Uvicorn..."
echo "📍 Open http://localhost:8000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python api_server.py
