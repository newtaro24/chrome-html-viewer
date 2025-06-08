#!/usr/bin/env python3
"""
Chrome HTML Viewer Bridge Server
A standalone server that bridges Chrome extension and Claude Desktop
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        remote_address = websocket.remote_address
        logger.info(f"Chrome extension connected from {remote_address}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                logger.info(f"Received from Chrome: {msg_type}")
                
                # Handle different message types
                if msg_type == "chrome_extension_connected":
                    logger.info("Chrome extension ready")
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "type": "connection_confirmed",
                        "message": "Bridge server connected"
                    }))
                    
                elif msg_type == "tab_updated":
                    logger.info(f"Tab updated: {data.get('url', 'unknown')}")
                    
                elif msg_type == "page_info":
                    # Store page info for later use
                    self.current_page_info = data.get('data')
                    logger.info(f"Received page info for: {self.current_page_info.get('url', 'unknown')}")
                    
                elif msg_type == "element_styles":
                    logger.info(f"Received styles for selector: {data.get('selector')}")
                    
                elif msg_type == "screenshot":
                    logger.info("Received screenshot data")
                    # Handle screenshot data
                    if data.get('data'):
                        await self.save_screenshot(data['data'])
                
                # Handle responses to our requests
                request_id = data.get("request_id")
                if request_id and request_id in self.pending_requests:
                    self.pending_requests[request_id].set_result(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Chrome extension disconnected")
        except Exception as e:
            logger.error(f"Error handling Chrome message: {e}")
        finally:
            self.chrome_connection = None
    
    async def save_screenshot(self, data_url: str):
        """Save screenshot to file"""
        try:
            # Remove data URL prefix
            image_data = data_url.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            
            # Create screenshots directory if it doesn't exist
            Path("screenshots").mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/screenshot_{timestamp}.png"
            
            # Save file
            with open(filename, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"Screenshot saved as {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None
    
    async def send_to_chrome(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send message to Chrome extension and wait for response"""
        if not self.chrome_connection:
            logger.error("No Chrome connection available")
            return None
        
        try:
            request_id = str(self.request_id)
            self.request_id += 1
            
            message["request_id"] = request_id
            future = asyncio.Future()
            self.pending_requests[request_id] = future
            
            await self.chrome_connection.send(json.dumps(message))
            logger.info(f"Sent to Chrome: {message.get('type')}")
            
            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=10.0)
            return result
            
        except asyncio.TimeoutError:
            logger.error("Chrome request timed out")
            return None
        except Exception as e:
            logger.error(f"Error sending to Chrome: {e}")
            return None
        finally:
            self.pending_requests.pop(request_id, None)
    
    async def run(self):
        """Run WebSocket server"""
        logger.info("Starting Chrome HTML Viewer Bridge Server...")
        
        async with websockets.serve(
            self.handle_chrome_message,
            "localhost",
            8765
        ):
            logger.info("WebSocket server started on ws://localhost:8765")
            logger.info("Waiting for Chrome extension connection...")
            logger.info("")
            logger.info("You can now:")
            logger.info("1. Click the Chrome extension icon")
            logger.info("2. Use the popup buttons to test functionality")
            logger.info("3. Press Ctrl+C to stop the server")
            logger.info("")
            
            # Keep the server running
            await asyncio.Future()

if __name__ == "__main__":
    server = ChromeBridgeServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
