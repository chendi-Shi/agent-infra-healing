#!/bin/bash
# Deploy script for Agent-Infra Healing System

set -e

echo "=========================================="
echo "Agent-Infra Healing System - Deployment"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - OPENAI_API_KEY (optional)"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Validate API keys
source .env
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ No API key found in .env file"
    echo "Please add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env"
    exit 1
fi

echo "✓ API keys configured"
echo ""

# Start services
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✓ Prometheus: http://localhost:9090"
else
    echo "⚠️  Prometheus not ready yet"
fi

# Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✓ Grafana: http://localhost:3000 (admin/admin)"
else
    echo "⚠️  Grafana not ready yet"
fi

# Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✓ Elasticsearch: http://localhost:9200"
else
    echo "⚠️  Elasticsearch not ready yet"
fi

# Demo App
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "✓ Demo App: http://localhost:8080"
else
    echo "⚠️  Demo App not ready yet"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Kibana: http://localhost:5601"
echo "  - Demo App: http://localhost:8080"
echo ""
echo "View logs:"
echo "  docker-compose logs -f agent-system"
echo ""
echo "Inject faults:"
echo "  curl -X POST http://localhost:8080/inject/errors -H 'Content-Type: application/json' -d '{\"rate\": 0.5}'"
echo "  curl -X POST http://localhost:8080/inject/latency"
echo ""
echo "Recover:"
echo "  curl -X POST http://localhost:8080/recover"
echo ""
echo "Stop system:"
echo "  docker-compose down"
echo ""
