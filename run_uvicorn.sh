#!/bin/bash

# Research-Orra - Uvicorn Server Startup Script

echo "🚀 Starting Research-Orra with Uvicorn..."
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Create static directory if it doesn't exist
mkdir -p static

# Start Uvicorn server
echo "🌐 Starting Uvicorn server on http://0.0.0.0:8080"
echo ""

uvicorn asgi:asgi_app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --log-level info \
    --access-log

echo ""
echo "✅ Server stopped"
