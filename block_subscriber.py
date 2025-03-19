#!/usr/bin/env python3
import asyncio
import json
import websockets
import datetime
import time
import logging
import sys
import os
import yaml
from typing import Dict, Any, List
from metrics import BlockMetrics

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

# Initialize Prometheus metrics
metrics = BlockMetrics(port=int(os.environ.get("METRICS_PORT", 8000)))

# Load configuration from YAML file or use environment variable as fallback
def load_config():
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    logger.info(f"Looking for config file at: {config_path}")
    
    # List all files in current directory for debugging
    try:
        files = os.listdir('.')
        logger.info(f"Files in current directory: {files}")
    except Exception as e:
        logger.error(f"Error listing directory contents: {e}")
    
    # Check if config file exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                file_content = file.read()
                logger.info(f"Raw config file content: {file_content}")
                config = yaml.safe_load(file_content)
                logger.info(f"Parsed config: {json.dumps(config)}")
                return config
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    else:
        logger.warning(f"Config file not found at: {config_path}")
    
    # Create a default config with a single endpoint
    logger.info("Using fallback configuration")
    ws_endpoint = os.environ.get("WS_ENDPOINT", "ws://localhost:8546")
    default_config = {
        "endpoints": [
            {
                "name": "reth-local",
                "ws_url": ws_endpoint
            }
        ]
    }
    logger.info(f"Default config: {json.dumps(default_config)}")
    return default_config

async def subscribe_to_new_block_headers(instance_name: str, ws_url: str):
    """Connect to reth WS endpoint and subscribe to newHeads"""
    while True:
        try:
            logger.info(f"Instance: {instance_name} | Connecting to {ws_url}")
            async with websockets.connect(ws_url) as websocket:
                logger.info(f"Instance: {instance_name} | Connected to {ws_url}")

                # Subscribe to newHeads
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newHeads"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                subscription_response = await websocket.recv()
                logger.info(f"Instance: {instance_name} | Subscription response: {subscription_response}")

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
                        
                        # Record metrics
                        metrics.record_block(instance_name, block_number, latency_ms)
                        
                        # Log the block information with the instance name
                        logger.info(
                            f"Instance: {instance_name} | "
                            f"Block #{block_number} | "
                            f"Block Time: {block_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
                            f"Receive Time: {receive_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
                            f"Latency: {latency_ms:.0f}ms"
                        )
                    except Exception as e:
                        logger.error(f"Instance: {instance_name} | Error processing block header: {e}")
                        logger.error(f"Instance: {instance_name} | Raw message: {message}")
            
        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.InvalidStatusCode,
                ConnectionRefusedError) as e:
            logger.error(f"Instance: {instance_name} | WebSocket connection error: {e}")
            logger.error(f"Instance: {instance_name} | Error type: {type(e).__name__}")
            logger.info(f"Instance: {instance_name} | Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Instance: {instance_name} | Unexpected error: {str(e)}")
            logger.error(f"Instance: {instance_name} | Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Instance: {instance_name} | Traceback: {traceback.format_exc()}")
            logger.info(f"Instance: {instance_name} | Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    """Start subscriptions for all configured endpoints"""
    # Load configuration
    config = load_config()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Extract endpoints from config
    endpoints = config.get('endpoints', [])
    
    if not endpoints:
        logger.error("No endpoints configured. Using default endpoint.")
        # Provide a default endpoint
        endpoints = [{
            "name": "reth-local",
            "ws_url": "ws://localhost:8546"
        }]
    
    # Log startup with endpoint details
    logger.info(f"Starting block header subscription service with {len(endpoints)} endpoint(s)...")
    for endpoint in endpoints:
        name = endpoint.get('name', 'unnamed')
        ws_url = endpoint.get('ws_url')
        logger.info(f"Configured endpoint: {name} -> {ws_url}")
    
    # Create tasks for each endpoint
    tasks = []
    for endpoint in endpoints:
        name = endpoint.get('name', 'unnamed')
        ws_url = endpoint.get('ws_url')
        
        if not ws_url:
            logger.error(f"Instance: {name} | Missing WebSocket URL in configuration. Skipping.")
            continue
        
        logger.info(f"Starting subscription for instance: {name} -> {ws_url}")
        tasks.append(subscribe_to_new_block_headers(name, ws_url))
    
    # Run all subscriptions concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        logger.info("Starting block header subscription service...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Subscription stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
