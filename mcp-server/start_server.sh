#!/bin/bash
# Start MCP Chrome Server

echo "Starting Chrome HTML Viewer MCP Server..."
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
python3 mcp_chrome_server.py
