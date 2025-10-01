#!/bin/bash
set -euo pipefail

# Form 3916 MCP Server Launch Script
# Ensures Docker is running and launches the MCP server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Log file for debugging (doesn't interfere with MCP protocol)
LOG_FILE="$PROJECT_ROOT/app/mcp_server/mcp_server.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker is not running" >> "$LOG_FILE"
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q "saas_nr-api-1"; then
    echo "$(date): Container not running, starting it..." >> "$LOG_FILE"
    cd "$PROJECT_ROOT" && docker compose up -d
    # Wait for container to be ready
    sleep 3
fi

# Verify container is healthy
if ! docker exec saas_nr-api-1 echo "test" &> /dev/null; then
    echo "ERROR: Container is not responding" >> "$LOG_FILE"
    exit 1
fi

# Log startup
echo "$(date): Starting Form 3916 MCP server..." >> "$LOG_FILE"
echo "$(date): Container: saas_nr-api-1" >> "$LOG_FILE"

# Start the server using exec to replace the shell process
# This is critical for MCP protocol to work correctly
exec docker exec -i saas_nr-api-1 python /app/mcp_server/form3916_server_v4.py