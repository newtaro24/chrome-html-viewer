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
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, Resource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromeBridgeServer:
    def __init__(self):
        self.server = Server("chrome-html-viewer")
        self.chrome_connection: Optional[WebSocketServerProtocol] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_id = 0
        self.current_page_info = None
        
        # Register MCP tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all available tools with MCP"""
        
        @self.server.tool()
        async def get_page_info() -> str:
            """Get current page HTML, CSS, and metadata"""
            result = await self._send_to_chrome({"type": "get_page_info"})
            if result:
                self.current_page_info = result
                return json.dumps(result, indent=2)
            return "Failed to get page info"
        
        @self.server.tool()
        async def get_element_styles(selector: str) -> str:
            """Get computed styles for elements matching the selector"""
            result = await self._send_to_chrome({
                "type": "get_element_styles",
                "selector": selector
            })
            return json.dumps(result, indent=2) if result else "No elements found"
        
        @self.server.tool()
        async def get_all_styles() -> str:
            """Get all CSS rules from the page"""
            result = await self._send_to_chrome({"type": "get_all_styles"})
            return json.dumps(result, indent=2) if result else "Failed to get styles"
        
        @self.server.tool()
        async def inject_css(css: str) -> str:
            """Inject CSS into the current page for live preview"""
            result = await self._send_to_chrome({
                "type": "inject_css",
                "css": css
            })
            return "CSS injected successfully" if result else "Failed to inject CSS"
        
        @self.server.tool()
        async def take_screenshot() -> str:
            """Take a screenshot of the current page"""
            result = await self._send_to_chrome({"type": "get_screenshot"})
            if result and "data" in result:
                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
                # Remove data URL prefix
                image_data = result["data"].split(",")[1]
                image_bytes = base64.b64decode(image_data)
                
                Path("screenshots").mkdir(exist_ok=True)
                with open(f"screenshots/{filename}", "wb") as f:
                    f.write(image_bytes)
                
                return f"Screenshot saved as {filename}"
            return "Failed to take screenshot"
        
        @self.server.tool()
        async def compare_with_figma(figma_url: str) -> str:
            """Compare current page design with Figma design"""
            # This would integrate with Figma API
            # For now, return a placeholder
            page_info = await self._send_to_chrome({"type": "get_page_info"})
            if page_info:
                return f"Ready to compare {page_info.get('url')} with Figma design at {figma_url}"
            return "Failed to get page info for comparison"
        
        @self.server.tool()
        async def analyze_css_differences(original_css: str) -> str:
            """Analyze differences between current page CSS and provided CSS"""
            current_styles = await self._send_to_chrome({"type": "get_all_styles"})
            if not current_styles:
                return "Failed to get current styles"
            
            # Here you would implement CSS diff logic
            # For now, return a basic comparison
            return json.dumps({
                "current_rules": len(current_styles.get("data", [])),
                "status": "Ready for detailed comparison"
            }, indent=2)
    
    async def _send_to_chrome(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                if data.get("type") == "tab_updated":
                    logger.info(f"Tab updated: {data.get('url')}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Chrome extension disconnected")
        finally:
            self.chrome_connection = None
    
    async def run(self):
        """Run both WebSocket server and MCP server"""
        # Start WebSocket server for Chrome extension
        ws_server = await websockets.serve(
            self.handle_chrome_message,
            "localhost",
            8765
        )
        logger.info("WebSocket server started on ws://localhost:8765")
        
        # Run MCP server
        async with self.server:
            await self.server.run()
        
        # Cleanup
        ws_server.close()
        await ws_server.wait_closed()

if __name__ == "__main__":
    bridge = ChromeBridgeServer()
    asyncio.run(bridge.run())
