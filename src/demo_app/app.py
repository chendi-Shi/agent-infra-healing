"""
Demo application for fault injection testing.
Exposes metrics and can be made to fail on demand.
"""
import os
import time
import random
import logging
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['endpoint'])
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Application memory usage')
ERROR_RATE = Gauge('app_error_rate', 'Current error rate')

# Application state
app_state = {
    'healthy': True,
    'error_rate': 0.0,
    'slow_requests': False,
    'memory_leak': False,
    'request_count': 0
}

@app.route('/')
def home():
    return jsonify({
        'service': 'demo-app',
        'status': 'running',
        'state': app_state
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    app_state['request_count'] += 1

    if not app_state['healthy']:
        logger.error("Health check failed - service unhealthy")
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='503').inc()
        return jsonify({'status': 'unhealthy'}), 503

    # Random errors based on error_rate
    if random.random() < app_state['error_rate']:
        logger.error(f"Health check failed - random error (rate: {app_state['error_rate']})")
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='500').inc()
        return jsonify({'status': 'error', 'message': 'Random failure'}), 500

    # Slow requests
    if app_state['slow_requests']:
        delay = random.uniform(2, 5)
        logger.warning(f"Slow request - sleeping for {delay:.2f}s")
        time.sleep(delay)

    REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
    return jsonify({'status': 'healthy', 'requests': app_state['request_count']})

@app.route('/api/data')
@REQUEST_DURATION.labels(endpoint='/api/data').time()
def get_data():
    """API endpoint that returns data."""
    app_state['request_count'] += 1

    if random.random() < app_state['error_rate']:
        logger.error("API error - failed to fetch data")
        REQUEST_COUNT.labels(method='GET', endpoint='/api/data', status='500').inc()
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("API request successful")
    REQUEST_COUNT.labels(method='GET', endpoint='/api/data', status='200').inc()
    return jsonify({
        'data': [{'id': i, 'value': random.randint(1, 100)} for i in range(10)]
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    # Update metrics
    ERROR_RATE.set(app_state['error_rate'])
    MEMORY_USAGE.set(random.randint(100_000_000, 500_000_000))  # Simulated

    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Fault injection endpoints
@app.route('/inject/unhealthy', methods=['POST'])
def inject_unhealthy():
    """Make the service unhealthy."""
    app_state['healthy'] = False
    logger.warning("FAULT INJECTED: Service marked as unhealthy")
    return jsonify({'status': 'injected', 'fault': 'unhealthy'})

@app.route('/inject/errors', methods=['POST'])
def inject_errors():
    """Inject random errors."""
    rate = request.json.get('rate', 0.5) if request.is_json else 0.5
    app_state['error_rate'] = min(max(rate, 0.0), 1.0)
    logger.warning(f"FAULT INJECTED: Error rate set to {app_state['error_rate']}")
    return jsonify({'status': 'injected', 'fault': 'errors', 'rate': app_state['error_rate']})

@app.route('/inject/latency', methods=['POST'])
def inject_latency():
    """Inject high latency."""
    app_state['slow_requests'] = True
    logger.warning("FAULT INJECTED: High latency enabled")
    return jsonify({'status': 'injected', 'fault': 'latency'})

@app.route('/inject/memory-leak', methods=['POST'])
def inject_memory_leak():
    """Simulate memory leak."""
    app_state['memory_leak'] = True
    logger.warning("FAULT INJECTED: Memory leak enabled")
    return jsonify({'status': 'injected', 'fault': 'memory-leak'})

@app.route('/recover', methods=['POST'])
def recover():
    """Recover from all faults."""
    app_state.update({
        'healthy': True,
        'error_rate': 0.0,
        'slow_requests': False,
        'memory_leak': False
    })
    logger.info("Service recovered from all faults")
    return jsonify({'status': 'recovered', 'state': app_state})

if __name__ == '__main__':
    logger.info("Starting demo application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
