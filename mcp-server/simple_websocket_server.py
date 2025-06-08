#!/usr/bin/env python3
"""
Chrome HTML Viewer MCP Server
Provides Chrome browser control and inspection capabilities to Claude Desktop
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
from pathlib import Path

import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromeBridgeServer:
    def __init__(self):
        self.chrome_connection: Optional[WebSocketServerProtocol] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_id = 0
        self.current_page_info = None
        
    async def handle_chrome_message(self, websocket: WebSocketServerProtocol):
        """Handle WebSocket connection from Chrome extension"""
        self.chrome_connection = websocket
        logger.info("Chrome extension connected")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                logger.info(f"Received from Chrome: {data.get('type')}")
                
                # Handle responses to our requests
                request_id = data.get("request_id")
                if request_id and request_id in self.pending_requests:
                    self.pending_requests[request_id].set_result(data)
                
                # Handle other messages
                if data.get("type") == "chrome_extension_connected":
                    logger.info("Chrome extension ready")
                elif data.get("type") == "tab_updated":
                    logger.info(f"Tab updated: {data.get('url')}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Chrome extension disconnected")
        finally:
            self.chrome_connection = None
    
    async def run(self):
        """Run WebSocket server"""
        # Start WebSocket server for Chrome extension
        logger.info("Starting WebSocket server...")
        async with websockets.serve(
            self.handle_chrome_message,
            "localhost",
            8765
        ):
            logger.info("WebSocket server started on ws://localhost:8765")
            logger.info("Waiting for Chrome extension connection...")
            # Keep the server running
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = ChromeBridgeServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
