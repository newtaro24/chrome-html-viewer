#!/usr/bin/env python3
"""
Chrome HTML Viewer Integrated MCP Server v6 - Fixed Handler
WebSocket handler signature fix
"""

import json
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import base64
from pathlib import Path
import traceback
import os

try:
    import websockets
except ImportError:
    print("Error: websockets module not installed. Run: pip install websockets", file=sys.stderr)
    sys.exit(1)

# Configure logging to file to avoid stdout interference
log_file = Path('/tmp/chrome-html-viewer-integrated-v6.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

class IntegratedMCPServer:
    def __init__(self):
        self.initialized = False
        self.chrome_connection = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_id_counter = 0
        self.ws_server = None
        
    async def run(self):
        """Run the MCP server on stdio"""
        logger.info("Starting Chrome HTML Viewer Integrated MCP Server v6")
        logger.info(f"Log file: {log_file}")
        
        try:
            # Start WebSocket server first
            ws_task = asyncio.create_task(self.start_websocket_server())
            
            # Wait for WebSocket server to start
            await asyncio.sleep(2)
            
            # Run MCP server
            mcp_task = asyncio.create_task(self.mcp_server())
            
            # Wait for both tasks
            await asyncio.gather(ws_task, mcp_task)
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            logger.error(traceback.format_exc())
    
    async def start_websocket_server(self):
        """Start WebSocket server with retry"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to start WebSocket server (attempt {attempt + 1}/{max_retries})")
                
                # Handler function that takes only websocket parameter
                async def handler(websocket):
                    await self.handle_chrome_message(websocket)
                
                self.ws_server = await websockets.serve(
                    handler,
                    "localhost",
                    8765,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                logger.info("WebSocket server successfully started on ws://localhost:8765")
                logger.info("Waiting for Chrome extension connection...")
                
                # Keep the server running
                await asyncio.Future()
                
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    logger.warning(f"Port 8765 is already in use. Waiting {retry_delay} seconds before retry...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Failed to start WebSocket server: {e}")
                    break
            except Exception as e:
                logger.error(f"WebSocket server error: {e}")
                logger.error(traceback.format_exc())
                break
    
    async def handle_chrome_message(self, websocket):
        """Handle WebSocket connection from Chrome extension"""
        self.chrome_connection = websocket
        remote_address = websocket.remote_address
        logger.info(f"Chrome extension connected from {remote_address}")
        
        try:
            # Send initial connection confirmation
            await websocket.send(json.dumps({
                "type": "server_ready",
                "message": "MCP WebSocket Bridge Ready"
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    logger.info(f"WS Received: {msg_type}")
                    
                    # Handle responses to our requests
                    request_id = data.get("request_id")
                    if request_id and request_id in self.pending_requests:
                        self.pending_requests[request_id].set_result(data)
                        continue
                    
                    # Handle different message types
                    if msg_type == "chrome_extension_connected":
                        logger.info("Chrome extension ready")
                        await websocket.send(json.dumps({
                            "type": "connection_confirmed",
                            "message": "MCP Bridge connected successfully"
                        }))
                    elif msg_type == "tab_updated":
                        logger.info(f"Tab updated: {data.get('url', 'unknown')}")
                    elif msg_type == "error":
                        logger.error(f"Chrome error: {data.get('message', 'Unknown error')}")
                    elif msg_type == "test":
                        # Echo test message
                        await websocket.send(json.dumps({
                            "type": "test_response",
                            "message": "Test successful"
                        }))
                    else:
                        logger.info(f"Received message type: {msg_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    logger.error(traceback.format_exc())
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Chrome extension disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.chrome_connection = None
            logger.info("Chrome connection closed")
    
    async def mcp_server(self):
        """Run MCP protocol handler"""
        logger.info("Starting MCP protocol handler")
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    logger.info("EOF received, stopping MCP server")
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                logger.debug(f"MCP Received: {line}")
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    if response:
                        self.send_response(response)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    self.send_response(error_response)
                    
            except Exception as e:
                logger.error(f"Error in MCP main loop: {e}")
                logger.error(traceback.format_exc())
                break
    
    def send_response(self, response: Dict[str, Any]):
        """Send response to stdout"""
        response_str = json.dumps(response)
        sys.stdout.write(response_str + '\n')
        sys.stdout.flush()
        logger.debug(f"MCP Sent: {response_str}")
    
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP request"""
        method = request.get('method', '')
        request_id = request.get('id')
        
        # Handle notifications (no id field)
        if request_id is None:
            if method == 'initialized':
                self.initialized = True
                logger.info("MCP initialization complete")
                return None
            elif method == 'notifications/initialized':
                logger.info("MCP client initialized")
                return None
            else:
                logger.warning(f"Unknown notification: {method}")
                return None
        
        # Handle requests
        if method == 'initialize':
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "chrome-html-viewer",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == 'tools/list':
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "test_connection",
                            "description": "Test if Chrome extension is connected",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_page_info",
                            "description": "Get current page HTML and metadata",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_element_styles",
                            "description": "Get computed styles for elements matching the selector",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "selector": {
                                        "type": "string",
                                        "description": "CSS selector"
                                    }
                                },
                                "required": ["selector"]
                            }
                        },
                        {
                            "name": "take_screenshot",
                            "description": "Take a screenshot of the current page",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            }
            
        elif method == 'resources/list':
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            }
            
        elif method == 'prompts/list':
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": []
                }
            }
            
        elif method == 'tools/call':
            tool_name = request.get('params', {}).get('name')
            arguments = request.get('params', {}).get('arguments', {})
            
            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            
            try:
                if tool_name == 'test_connection':
                    result_text = await self.test_connection()
                elif tool_name == 'get_page_info':
                    result_text = await self.get_page_info()
                elif tool_name == 'get_element_styles':
                    result_text = await self.get_element_styles(arguments.get('selector'))
                elif tool_name == 'take_screenshot':
                    result_text = await self.take_screenshot()
                else:
                    result_text = f"Unknown tool: {tool_name}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    # Tool implementation methods
    async def test_connection(self) -> str:
        """Test connection status"""
        ws_status = "Connected ✓" if self.chrome_connection else "Not connected ✗"
        chrome_status = "Connected ✓" if self.chrome_connection else "Not connected ✗"
        
        ws_server_status = "Running ✓" if self.ws_server else "Not running ✗"
        
        return f"""Chrome HTML Viewer Status:
- MCP Server: Running ✓
- WebSocket Server: {ws_server_status} (ws://localhost:8765)
- Chrome Extension: {chrome_status}

{("All systems connected and ready!" if self.chrome_connection else "Chrome extension not connected. Please check the extension is installed and the popup shows 'Connected'.")}

Debug info:
- Log file: {log_file}
- Process ID: {os.getpid()}
"""

    async def get_page_info(self) -> str:
        """Get page information from Chrome"""
        result = await self.send_to_chrome({"type": "get_page_info"})
        
        if result and result.get('data'):
            data = result['data']
            return f"""Page Information:
URL: {data.get('url', 'N/A')}
Title: {data.get('title', 'N/A')}
Viewport: {data.get('viewport', {}).get('width')}x{data.get('viewport', {}).get('height')}

HTML Length: {len(data.get('html', ''))} characters
Stylesheets: {len(data.get('stylesheets', []))}
Inline Styles: {len(data.get('inlineStyles', []))}

Full data received successfully."""
        
        return "Failed to get page info. Please ensure Chrome extension is connected and you have an active tab."

    async def get_element_styles(self, selector: str) -> str:
        """Get element styles"""
        if not selector:
            return "Error: CSS selector is required"
        
        result = await self.send_to_chrome({
            "type": "get_element_styles",
            "selector": selector
        })
        
        if result and result.get('data'):
            elements = result['data']
            if elements:
                return f"""Found {len(elements)} element(s) matching '{selector}':

{json.dumps(elements, indent=2)}"""
            else:
                return f"No elements found matching selector: {selector}"
        
        return "Failed to get element styles. Please ensure Chrome extension is connected."

    async def take_screenshot(self) -> str:
        """Take screenshot"""
        result = await self.send_to_chrome({"type": "get_screenshot"})
        
        if result and result.get('data'):
            try:
                # Save screenshot
                image_data = result['data'].split(",")[1]
                image_bytes = base64.b64decode(image_data)
                
                screenshots_dir = Path("/Users/newtaro/project/chrome-html-viewer/mcp-server/screenshots")
                screenshots_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = screenshots_dir / f"screenshot_{timestamp}.png"
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                return f"Screenshot saved as {filename}"
            except Exception as e:
                return f"Error saving screenshot: {e}"
        
        return "Failed to take screenshot. Please ensure Chrome extension is connected."

    async def send_to_chrome(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send message to Chrome and wait for response"""
        if not self.chrome_connection:
            logger.error("No Chrome connection available")
            return None
        
        try:
            request_id = str(self.request_id_counter)
            self.request_id_counter += 1
            
            # Create future for response
            future = asyncio.Future()
            self.pending_requests[request_id] = future
            
            # Send message
            message["request_id"] = request_id
            await self.chrome_connection.send(json.dumps(message))
            logger.info(f"Sent to Chrome: {message}")
            
            # Wait for response with timeout
            try:
                result = await asyncio.wait_for(future, timeout=10.0)
                logger.info(f"Received response: {result}")
                return result
            except asyncio.TimeoutError:
                logger.error("Chrome request timed out")
                return None
                
        except Exception as e:
            logger.error(f"Error sending to Chrome: {e}")
            return None
        finally:
            self.pending_requests.pop(request_id, None)


if __name__ == "__main__":
    server = IntegratedMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
