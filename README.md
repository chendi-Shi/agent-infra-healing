# Agent-Infra Healing System

Multi-Agent Infrastructure Orchestration System for automated fault diagnosis, recovery planning, and self-healing.

## Project Overview

**Goal**: Build a multi-agent system that automatically manages infrastructure failures:
- Diagnosis Agent: Analyze logs and metrics to identify root causes
- Strategy Agent: Generate and evaluate multiple recovery plans
- Execution Agent: Execute fixes and verify recovery

**Tech Stack**:
- Agent Framework: LangGraph
- Infrastructure: Kubernetes (kind for local dev) + Docker
- Monitoring: Prometheus + Grafana
- Logging: ELK Stack (lightweight local setup)

## Project Phases

### Phase 1: Infrastructure Setup (Current - Week 1-2)
- [x] Project initialization
- [ ] Local K8s cluster (kind)
- [ ] Basic monitoring stack (Prometheus + Grafana)
- [ ] Logging infrastructure (Fluent Bit + Elasticsearch)
- [ ] Chaos engineering tools (Chaos Mesh)
- [ ] Agent framework skeleton

### Phase 2: Agent Training (Week 3-6)
- [ ] Data collection pipeline
- [ ] Agent model fine-tuning
- [ ] Multi-agent coordination
- [ ] Evaluation metrics

### Phase 3: Evaluation (Week 7-8)
- [ ] Benchmark creation
- [ ] Baseline comparison
- [ ] Performance optimization

## Budget Estimate
- GPU Training: ¥800-1300 (2 months)
- Total Timeline: 8 weeks

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Start local K8s cluster
kind create cluster --config k8s/kind-config.yaml

# Deploy monitoring stack
kubectl apply -f k8s/monitoring/

# Run agents
python src/main.py
```

## Directory Structure

```
agent-infra-healing/
├── src/                    # Agent source code
│   ├── agents/            # Agent implementations
│   ├── infra/             # Infrastructure management
│   ├── data/              # Data collection & processing
│   └── utils/             # Utilities
├── k8s/                   # Kubernetes manifests
│   ├── monitoring/        # Prometheus, Grafana
│   ├── logging/           # Fluent Bit, Elasticsearch
│   └── chaos/             # Chaos Mesh experiments
├── data/                  # Fault scenarios & logs
├── models/                # Trained models
├── experiments/           # Experiment results
└── docs/                  # Documentation
```
