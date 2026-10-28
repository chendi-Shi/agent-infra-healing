"""
Main entry point for the Agent-Infra Healing System.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import AgentOrchestrator
from infra.monitor import InfrastructureMonitor
from data.collector import DataCollector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution loop."""
    logger.info("=" * 60)
    logger.info("Agent-Infra Healing System Starting")
    logger.info("=" * 60)

    # Validate configuration
    if not os.getenv('ANTHROPIC_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        logger.error("No API key found. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        sys.exit(1)

    # Initialize components
    logger.info("Initializing components...")

    monitor = InfrastructureMonitor(
        prometheus_url=os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
        elasticsearch_url=os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    )

    collector = DataCollector(monitor)
    orchestrator = AgentOrchestrator(
        model=os.getenv('AGENT_MODEL', 'claude-3-5-sonnet-20241022'),
        monitor=monitor,
        collector=collector
    )

    logger.info("Components initialized successfully")
    logger.info(f"Model: {os.getenv('AGENT_MODEL', 'claude-3-5-sonnet-20241022')}")
    logger.info(f"Prometheus: {os.getenv('PROMETHEUS_URL', 'http://localhost:9090')}")
    logger.info(f"Elasticsearch: {os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')}")

    # Start monitoring loop
    logger.info("\nStarting monitoring loop...")
    logger.info("Press Ctrl+C to stop\n")

    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Agent-Infra Healing System stopped")


if __name__ == '__main__':
    main()
