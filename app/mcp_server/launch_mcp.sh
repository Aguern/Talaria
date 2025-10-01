#!/bin/bash

# Script to launch Form 3916 MCP Server
# Usage: ./launch_mcp.sh

# Set environment
export PYTHONPATH="/Users/nicolasangougeard/Desktop/SaaS_NR"

# Check if .env exists and source it
if [ -f "/Users/nicolasangougeard/Desktop/SaaS_NR/.env" ]; then
    export $(cat /Users/nicolasangougeard/Desktop/SaaS_NR/.env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "🚀 Starting Form 3916 MCP Server..."
echo "📡 Server will listen for JSON-RPC requests on stdin"
echo "💡 To test: Send JSON-RPC requests to stdin"
echo "🛑 To stop: Press Ctrl+C"
echo ""

# Launch the server
python3 /Users/nicolasangougeard/Desktop/SaaS_NR/app/mcp_server/form3916_server.py