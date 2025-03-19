# Ethereum Block Header Subscriber

This script connects to one or more reth clients via WebSocket and subscribes to new block headers. It logs the following information for each new block:

- Receive time (with millisecond precision)
- Block time
- Block height (number)
- Latency between block timestamp and receive time (in milliseconds)

## Features

- Connect to multiple reth nodes via WebSockets
- Subscribe to block headers using the Ethereum JSON-RPC API
- Log block reception times with millisecond precision
- Calculate and log latency between block time and reception time
- Run in Docker container for easy deployment

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

1. Establishes a WebSocket connection to the reth node(s) at the configured endpoint(s)
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
2025-03-18 18:42:50.890 - Instance: reth-local | Block #22075627 | Block Time: 2025-03-18 18:42:47.000 | Receive Time: 2025-03-18 18:42:50.890 | Latency: 3890ms
```

In this example:
- Block #22075627 was created at 18:42:47
- Your node received it at 18:42:50.890
- The latency was 3890 milliseconds (about 3.9 seconds)

## Configuration

### WebSocket Endpoints

The block subscriber now supports connecting to multiple Ethereum nodes simultaneously. Configure the endpoints in the `config.yaml` file:

```yaml
# WebSocket endpoint configurations
endpoints:
  - name: reth-local
    ws_url: ws://localhost:8546
  
  # Add more endpoints as needed, for example:
  # - name: reth-remote
  #   ws_url: ws://remote-server:8546
```

Each endpoint requires:
- A unique `name` which will appear in the logs
- A `ws_url` specifying the WebSocket endpoint

The block subscriber will connect to all configured endpoints and log block headers from each with the instance name included.

### Environment Variables

If the `config.yaml` file is not found, the subscriber falls back to using the environment variable:

- `WS_ENDPOINT`: WebSocket endpoint URL (default: `ws://localhost:8546`)

You can also specify an alternative path to the config file:

- `CONFIG_PATH`: Path to the config YAML file (default: `config.yaml`)

## Monitoring with Prometheus and Grafana

This project includes a full monitoring stack using Prometheus and Grafana to track and visualize block latency metrics for each Ethereum node instance.

### Container Names

The Docker Compose setup uses specific container names to avoid conflicts with other projects:

* `reth-ws-block-subscriber` - The main application that connects to Ethereum nodes
* `reth-ws-prometheus` - Prometheus instance for metrics collection
* `reth-ws-grafana` - Grafana instance for dashboards and visualization

### Metrics Collected

The application exports the following Prometheus metrics:

* `eth_blocks_total` - Counter for total number of blocks received per instance
* `eth_block_latency_ms` - Histogram of block latency in milliseconds per instance
* `eth_latest_block_number` - Gauge showing the latest block number received per instance
* `eth_latest_block_latency_ms` - Gauge showing the latency of the latest block per instance

### Accessing Dashboards

1. **Prometheus**: Available at http://localhost:9090
2. **Grafana**: Available at http://localhost:3000
   - Default login: admin / admin
   - Pre-configured dashboard: "Ethereum Block Subscription"

### Dashboard Features

The Grafana dashboard provides:

1. **Block Latency Chart**: Line chart showing latency for each instance over time
2. **Latest Block Numbers**: Current block numbers per instance 
3. **Block Rate**: Rate of blocks received in the last 5 minutes
4. **Latency Distribution**: Histogram showing the distribution of latency values

### Custom Metrics

The metrics module (`metrics.py`) can be extended with additional metrics as needed.

## Log Format

The block subscriber logs the following information for each block header:

```
2025-03-18 18:42:50.890 - Instance: reth-local | Block #22075627 | Block Time: 2025-03-18 18:42:47.000 | Receive Time: 2025-03-18 18:42:50.890 | Latency: 3890ms
```

- **Instance**: The name of the Ethereum node instance (from config.yaml)
- **Block #**: The block number/height
- **Block Time**: Timestamp when the block was created
- **Receive Time**: Timestamp when the block header was received by the subscriber
- **Latency**: Difference between receive time and block time in milliseconds

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Building and Running

1. Clone this repository:
   ```bash
   git clone https://github.com/fodorl/eth-reth-block-subscriber.git
   cd eth-reth-block-subscriber
   ```

2. Modify the `config.yaml` file to include your Ethereum node WebSocket endpoints.

3. Build and run with Docker Compose:
   ```bash
   docker compose up -d
   ```

4. Check the logs:
   ```bash
   docker logs -f block-subscriber
   ```

The block subscriber container mounts the `logs` directory and `config.yaml` from your host machine, so you can:
- View logs in real-time in the `logs` directory
- Modify `config.yaml` and restart the container to update configurations

## Note

Ensure your reth node is running with WebSocket enabled as specified in your docker-compose.yml.
