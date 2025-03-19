#!/usr/bin/env python3
from prometheus_client import Counter, Gauge, Histogram, start_http_server, REGISTRY
import logging
import socket

logger = logging.getLogger(__name__)

# Prometheus metrics
class BlockMetrics:
    def __init__(self, port=8000):
        """Initialize Prometheus metrics"""
        # Start Prometheus HTTP server
        self.port = port
        
        # Metrics for block headers
        self.block_counter = Counter(
            'eth_blocks_total', 
            'Total number of blocks received',
            ['instance']
        )
        
        self.block_latency = Histogram(
            'eth_block_latency_ms',
            'Latency between block timestamp and receive time in milliseconds',
            ['instance'],
            buckets=(
                50, 100, 250, 500, 1000, 2000, 3000, 4000, 5000, 
                7500, 10000, 15000, 30000, 60000
            )
        )
        
        self.latest_block = Gauge(
            'eth_latest_block_number', 
            'Latest block number received',
            ['instance']
        )
        
        self.latest_block_latency = Gauge(
            'eth_latest_block_latency_ms',
            'Latest block latency in milliseconds',
            ['instance']
        )
        
        logger.info(f"Starting Prometheus metrics server on port {port}")
        start_http_server(port)
    
    def record_block(self, instance_name, block_number, latency_ms):
        """Record metrics for a new block"""
        self.block_counter.labels(instance=instance_name).inc()
        self.block_latency.labels(instance=instance_name).observe(latency_ms)
        self.latest_block.labels(instance=instance_name).set(block_number)
        self.latest_block_latency.labels(instance=instance_name).set(latency_ms)
