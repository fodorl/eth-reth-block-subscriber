# Ethereum Block Header Subscriber

This script connects to a reth client via WebSocket and subscribes to new block headers. It logs the following information for each new block:

- Receive time (with millisecond precision)
- Block time
- Block height (number)
- Latency between block timestamp and receive time (in milliseconds)

## Requirements

- Python 3.6+
- websockets package

## Installation

1. Set up a Python virtual environment:
```bash
# Install required packages for virtual environments (if not already installed)
sudo apt install python3-venv python3-full

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

2. Make the script executable:
```bash
chmod +x block_subscriber.py
```

## Usage

Activate the virtual environment and run the script:
```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run the script
./block_subscriber.py
```

Alternatively, you can run it with python directly:
```bash
venv/bin/python block_subscriber.py
```

## How It Works

The script performs the following operations:

1. Establishes a WebSocket connection to the reth node at `ws://localhost:8546`
2. Subscribes to the Ethereum `newHeads` event to receive notifications about new blocks
3. For each new block, the script:
   - Records the exact receive time (with millisecond precision) immediately after the message is received
   - Extracts the block number and block timestamp
   - Calculates latency as (receive time - block time) in milliseconds
   - Logs all information to both console and the log file

### Latency Calculation

The latency is calculated as the time difference between when the block was received by the script and when the block was created according to its timestamp:

```python
latency_ms = (receive_time.timestamp() - block_timestamp) * 1000
```

This provides an accurate measure of the delay between block creation and when your node received it.

### Sample Output

```
2025-03-17 19:19:01.417 - Block #22068351 | Block Time: 2025-03-17 19:18:59.000 | Receive Time: 2025-03-17 19:19:01.417 | Latency: 2417ms
```

In this example:
- Block #22068351 was created at 19:18:59
- Your node received it at 19:19:01.417
- The latency was 2417 milliseconds (about 2.4 seconds)

## Configuration

Edit the script to modify:
- WebSocket endpoint (default: `ws://localhost:8546`)
- Logging format and destination

## Note

Ensure your reth node is running with WebSocket enabled as specified in your docker-compose.yml.

## Docker Setup

The application can be run in a Docker container that connects to your existing Ethereum network.

### Prerequisites

- Docker and Docker Compose installed
- reth node running in a Docker container with WebSocket enabled

### Building and Running

1. Build and start the container:
```bash
# If your user has Docker permissions
docker compose up -d

# If you need sudo to run Docker commands
sudo docker compose up -d
```

2. View logs:
```bash
# If your user has Docker permissions
docker logs -f block-subscriber

# If you need sudo to run Docker commands
sudo docker logs -f block-subscriber
```

3. Stop the container:
```bash
# If your user has Docker permissions
docker compose down

# If you need sudo to run Docker commands
sudo docker compose down
```

### Configuration

The Docker setup uses the following configuration:
- Container automatically connects to the reth node using the network name `eth-network`
- WebSocket endpoint is set to `ws://reth:8546` by default
- Logs are stored in the `./logs` directory on the host

### Integration with Existing reth Setup

This docker-compose.yml is designed to connect to your existing reth node. It assumes:
1. Your reth node is running on the Docker network named `eth-network`
2. Your reth service is named `reth` in the Docker network
3. The WebSocket port 8546 is enabled on your reth node

If your setup differs, modify the `WS_ENDPOINT` environment variable in the docker-compose.yml file.
