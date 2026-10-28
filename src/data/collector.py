"""
Data collection and storage for training.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects fault scenarios and agent actions for training."""

    def __init__(self, monitor, data_dir: str = '/app/data'):
        self.monitor = monitor
        self.data_dir = Path(data_dir)
        self.scenarios_dir = self.data_dir / 'scenarios'
        self.logs_dir = self.data_dir / 'logs'

        # Create directories
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logger

    def save_scenario(self, scenario: Dict) -> str:
        """Save a fault scenario."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"scenario_{timestamp}.json"
        filepath = self.scenarios_dir / filename

        with open(filepath, 'w') as f:
            json.dump(scenario, f, indent=2)

        self.logger.info(f"Saved scenario: {filename}")
        return str(filepath)

    def save_agent_action(self, action: Dict) -> str:
        """Save an agent action for training."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"action_{timestamp}.json"
        filepath = self.logs_dir / filename

        with open(filepath, 'w') as f:
            json.dump(action, f, indent=2)

        return str(filepath)

    def collect_fault_data(self, anomalies: List[Dict]) -> Dict:
        """Collect comprehensive fault data."""
        fault_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'anomalies': anomalies,
            'metrics': {},
            'logs': []
        }

        # Collect relevant metrics
        for anomaly in anomalies:
            if anomaly['type'] in ['high_error_rate', 'high_latency']:
                service = anomaly.get('service', 'demo-app')
                fault_data['metrics'][service] = self.monitor.get_service_health(service)

            # Collect related logs
            if 'service' in anomaly:
                logs = self.monitor.search_logs(
                    f'service:{anomaly["service"]} AND level:ERROR',
                    size=20,
                    time_range=600
                )
                fault_data['logs'].extend(logs)

        return fault_data

    def load_scenarios(self) -> List[Dict]:
        """Load all saved scenarios."""
        scenarios = []
        for filepath in self.scenarios_dir.glob('scenario_*.json'):
            with open(filepath) as f:
                scenarios.append(json.load(f))
        return scenarios

    def get_training_dataset(self) -> List[Dict]:
        """Get all data for training."""
        return self.load_scenarios()
