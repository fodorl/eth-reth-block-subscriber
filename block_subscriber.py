#!/usr/bin/env python3
import asyncio
import json
import websockets
import datetime
import time
import logging
import sys
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', 'block_subscription.log'))
    ]
)
logger = logging.getLogger(__name__)

# WebSocket endpoint for reth - get from environment variable or use default
WS_ENDPOINT = os.environ.get("WS_ENDPOINT", "ws://localhost:8546")

async def subscribe_to_new_block_headers():
    """Connect to reth WS endpoint and subscribe to newHeads"""
    while True:
        try:
            async with websockets.connect(WS_ENDPOINT) as websocket:
                logger.info(f"Connected to {WS_ENDPOINT}")

                # Subscribe to newHeads
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newHeads"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                subscription_response = await websocket.recv()
                logger.info(f"Subscription response: {subscription_response}")

                # Process incoming block headers
                while True:
                    # Receive message first
                    message = await websocket.recv()
                    
                    # IMMEDIATELY record receive time with millisecond precision after receiving the message
                    receive_time = datetime.datetime.now()
                    
                    # Parse block header
                    block_data = json.loads(message)
                    
                    try:
                        # Extract block information
                        block_header = block_data.get('params', {}).get('result', {})
                        block_number = int(block_header.get('number', '0x0'), 16)
                        block_timestamp = int(block_header.get('timestamp', '0x0'), 16)
                        
                        # Convert block timestamp to datetime for display
                        block_time = datetime.datetime.fromtimestamp(block_timestamp)
                        
                        # Calculate latency - simply the difference between receive time and block time
                        # Expressed in milliseconds as requested
                        latency_ms = (receive_time.timestamp() - block_timestamp) * 1000
                        
                        # Log the block information
                        logger.info(
                            f"Block #{block_number} | "
                            f"Block Time: {block_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
                            f"Receive Time: {receive_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
                            f"Latency: {latency_ms:.0f}ms"
                        )
                    except Exception as e:
                        logger.error(f"Error processing block header: {e}")
                        logger.error(f"Raw message: {message}")
            
        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.InvalidStatusCode,
                ConnectionRefusedError) as e:
            logger.error(f"WebSocket connection error: {e}")
            logger.info("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        logger.info("Starting block header subscription...")
        asyncio.run(subscribe_to_new_block_headers())
    except KeyboardInterrupt:
        logger.info("Subscription stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
