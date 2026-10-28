"""
Infrastructure monitoring component.
Collects metrics from Prometheus and logs from Elasticsearch.
"""
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InfrastructureMonitor:
    """Monitors infrastructure health via Prometheus and Elasticsearch."""

    def __init__(self, prometheus_url: str, elasticsearch_url: str):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.elasticsearch_url = elasticsearch_url.rstrip('/')
        self.logger = logger

    def check_connectivity(self) -> Dict[str, bool]:
        """Check if monitoring services are reachable."""
        status = {}

        # Check Prometheus
        try:
            resp = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            status['prometheus'] = resp.status_code == 200
        except Exception as e:
            self.logger.warning(f"Prometheus unreachable: {e}")
            status['prometheus'] = False

        # Check Elasticsearch
        try:
            resp = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=5)
            status['elasticsearch'] = resp.status_code == 200
        except Exception as e:
            self.logger.warning(f"Elasticsearch unreachable: {e}")
            status['elasticsearch'] = False

        return status

    def query_metrics(self, query: str, time_range: Optional[int] = 300) -> Dict:
        """
        Query Prometheus metrics.

        Args:
            query: PromQL query string
            time_range: Time range in seconds (default: 5 minutes)

        Returns:
            Query results
        """
        try:
            # Query current value
            resp = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            if data['status'] != 'success':
                self.logger.error(f"Prometheus query failed: {data}")
                return {'status': 'error', 'data': []}

            return data

        except Exception as e:
            self.logger.error(f"Failed to query Prometheus: {e}")
            return {'status': 'error', 'data': [], 'error': str(e)}

    def query_range(self, query: str, start: datetime, end: datetime, step: str = '15s') -> Dict:
        """Query Prometheus metrics over a time range."""
        try:
            resp = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start.timestamp(),
                    'end': end.timestamp(),
                    'step': step
                },
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            self.logger.error(f"Failed to query Prometheus range: {e}")
            return {'status': 'error', 'data': [], 'error': str(e)}

    def get_service_health(self, service: str = 'demo-app') -> Dict:
        """Get health status of a service."""
        queries = {
            'up': f'up{{job="{service}"}}',
            'request_rate': f'rate(http_requests_total{{job="{service}"}}[5m])',
            'error_rate': f'rate(http_requests_total{{job="{service}",status=~"5.."}}[5m])',
            'latency_p95': f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="{service}"}}[5m]))',
        }

        results = {}
        for name, query in queries.items():
            data = self.query_metrics(query)
            if data['status'] == 'success' and data.get('data', {}).get('result'):
                results[name] = data['data']['result'][0]['value'][1]
            else:
                results[name] = None

        return results

    def search_logs(self, query: str, size: int = 100, time_range: Optional[int] = 300) -> List[Dict]:
        """
        Search logs in Elasticsearch.

        Args:
            query: Search query
            size: Max results
            time_range: Time range in seconds

        Returns:
            List of log entries
        """
        try:
            # Build time range filter
            now = datetime.utcnow()
            start_time = now - timedelta(seconds=time_range) if time_range else now - timedelta(hours=1)

            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"query_string": {"query": query}},
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": now.isoformat()
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": size,
                "sort": [{"@timestamp": "desc"}]
            }

            resp = requests.post(
                f"{self.elasticsearch_url}/logs-*/_search",
                json=search_body,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            hits = data.get('hits', {}).get('hits', [])
            return [hit['_source'] for hit in hits]

        except Exception as e:
            self.logger.error(f"Failed to search logs: {e}")
            return []

    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in metrics and logs."""
        anomalies = []

        # Check service health
        health = self.get_service_health('demo-app')

        # Service down
        if health.get('up') == '0':
            anomalies.append({
                'type': 'service_down',
                'severity': 'critical',
                'service': 'demo-app',
                'message': 'Service is not responding'
            })

        # High error rate
        error_rate = float(health.get('error_rate') or 0)
        if error_rate > 0.1:  # 10% error rate
            anomalies.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'service': 'demo-app',
                'value': error_rate,
                'message': f'High error rate: {error_rate:.2%}'
            })

        # High latency
        latency = float(health.get('latency_p95') or 0)
        if latency > 1.0:  # 1 second
            anomalies.append({
                'type': 'high_latency',
                'severity': 'medium',
                'service': 'demo-app',
                'value': latency,
                'message': f'High P95 latency: {latency:.2f}s'
            })

        # Search for error logs
        error_logs = self.search_logs('level:ERROR', size=10, time_range=300)
        if len(error_logs) > 5:
            anomalies.append({
                'type': 'frequent_errors',
                'severity': 'medium',
                'count': len(error_logs),
                'message': f'Frequent errors in logs: {len(error_logs)} in last 5 minutes',
                'sample_logs': error_logs[:3]
            })

        return anomalies
