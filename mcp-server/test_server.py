#!/usr/bin/env python3
"""
Test WebSocket server - simple version to verify connection
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_connection(websocket):
    logger.info(f"New connection from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info(f"Received: {message}")
            data = json.loads(message)
            
            # Echo back to confirm connection
            if data.get("type") == "chrome_extension_connected":
                logger.info("Chrome extension connected successfully!")
                await websocket.send(json.dumps({
                    "type": "connection_confirmed",
                    "message": "WebSocket server is running"
                }))
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    except Exception as e:
        logger.error(f"Error: {e}")

async def main():
    logger.info("Starting test WebSocket server on ws://localhost:8765")
    async with websockets.serve(handle_connection, "localhost", 8765):
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
