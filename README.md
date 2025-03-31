# Kubernetes Root Cause Analysis Engine

A multi-agent system for analyzing and troubleshooting Kubernetes issues, built with LangGraph and LangSmith.

## Overview

This project implements a sophisticated multi-agent system for Kubernetes root cause analysis, where each agent specializes in a specific aspect of Kubernetes. The system uses a directed graph structure to coordinate investigations, collect evidence, and determine the most likely root causes of issues.

## Key Features

- **Multi-Agent Architecture**: Master coordinator agent and multiple specialist agents (Network, Metrics, Cluster, Workload, etc.)
- **Directed Graph Workflow**: LangGraph-based investigation flow with conditional branching
- **Evidence Collection Framework**: Structured approach to gathering and analyzing Kubernetes cluster data
- **Confidence-Based Analysis**: Confidence scoring system for potential root causes
- **Decision Tree Logic**: Conditional investigation paths based on evidence
- **Visualizations**: Interactive visualizations of investigation flow, evidence relationships, and confidence evolution
- **LangSmith Integration**: Tracing and monitoring of agent interactions
- **Human-in-the-Loop**: Support for human intervention and guidance
- **Metrics Analysis**: Support for Kubernetes Metrics API and Prometheus with OAuth2 authentication
- **Cluster Analysis**: Analysis of control plane components (API Server, Scheduler, Controller Manager, ETCD) and cluster objects (Pods, Services, etc.)

## Directory Structure

The project has been organized into the following directory structure:

### Main Directories

- `agents/`: Contains all specialist agent implementations
- `bin/`: Core executable scripts
- `chaos-tests/`: Chaos engineering test YAML files
- `docs/`: Documentation
- `examples/`: Example scripts and files
- `k8s-manifests/`: Kubernetes manifests for testing
- `k8s_analyzer/`: Kubernetes analysis modules
- `output/`: Generated output from investigations
- `prompts/`: Prompt templates for agents
- `scripts/`: Utility shell scripts
- `tests/`: Test suite
- `utils/`: Utility functions and helpers

### Test Structure

- `tests/integration_tests/`: Tests for agent interactions and integration
- `tests/specialist_agents/`: Tests for individual specialist agents
- `tests/unit/`: Unit tests for core components
- `tests/workflow_tests/`: Tests for the full analysis workflow

### Main Scripts

- `run_investigation.py`: Symlink to main investigation script
- `run_live_cluster.py`: Symlink to script for live cluster analysis
- `workflow_investigation.py`: Symlink to workflow-based investigation script

## Architecture

The system consists of:

1. **Master Coordinator Agent**: Orchestrates the investigation, manages state, and makes decisions
2. **Specialist Agents**: Focus on specific aspects like networking, metrics, cluster infrastructure, workloads, etc.
3. **LangGraph Workflow**: Manages the flow of investigation and state transitions
4. **Kubernetes Client**: Interfaces with the Kubernetes API to collect data
5. **Metrics Collection**: Retrieves metrics from Kubernetes Metrics API or Prometheus
6. **Cluster State Analysis**: Examines control plane health and Kubernetes object configurations
7. **Visualization Engine**: Provides interactive diagrams of the investigation

For more details, see the [architecture documentation](docs/k8s_root_cause_analysis_architecture.md).

## Installation

# Clone the repository
git clone https://github.com/vobbilis/multi-agent-v1.git
cd multi-agent-v1

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY=your_api_key
export LANGSMITH_API_KEY=your_langsmith_key  # Optional, for tracing

# For metrics collection configure one of:
# Kubernetes Metrics API (default)
export METRICS_SOURCE=kubernetes

# Or Prometheus with OAuth2
export METRICS_SOURCE=prometheus
export PROMETHEUS_URL=http://prometheus.example.com:9090
export PROMETHEUS_AUTH_TYPE=oauth2
export PROMETHEUS_OAUTH_CLIENT_ID=your_oauth_client_id
export PROMETHEUS_OAUTH_CLIENT_SECRET=your_oauth_client_secret
export PROMETHEUS_OAUTH_TOKEN_URL=https://auth.example.com/oauth/token

# Or Prometheus with basic auth
export METRICS_SOURCE=prometheus
export PROMETHEUS_URL=http://prometheus.example.com:9090
export PROMETHEUS_AUTH_TYPE=basic
export PROMETHEUS_USERNAME=your_username
export PROMETHEUS_PASSWORD=your_password

# For cluster analysis (optional)
export KUBECONFIG=/path/to/your/kubeconfig  # Optional, defaults to ~/.kube/config
export KUBECTL_PATH=/path/to/kubectl  # Optional, defaults to "kubectl" in PATH
export INVESTIGATION_NAMESPACE=your-namespace  # Optional, defaults to "default"

## Usage

```bash
# Run an investigation with symptoms provided directly
python main.py --symptoms "Several pods in the production namespace keep restarting with CrashLoopBackOff status. The application logs show connection timeouts when trying to reach the database service. This started approximately 30 minutes after a network policy update was applied. Control plane nodes are reporting disk pressure warnings." --namespace default --output report.md --visualize

# Or provide symptoms in a file
python main.py --symptoms-file symptoms.txt --namespace production --output report.md --visualize
```

## Implementation Details

The system is implemented using:

- **LangGraph**: For agent orchestration and workflow management
- **LangChain**: For LLM interaction and chain composition
- **LangSmith**: For tracing and debugging agent interactions
- **Kubernetes Python Client**: For interacting with the Kubernetes API
- **Prometheus API**: For collecting metrics with OAuth2 or basic authentication
- **kubectl**: For collecting cluster state information
- **D3.js and Chart.js**: For interactive visualizations

For more details, see the [implementation guide](docs/implementation_guide.md) and [visualization capabilities](docs/visualization_capabilities.md).

## Project Structure

- `main.py`: Main entry point for the multi-agent system
- `bin/`: Executable scripts and symlinks
- `cli/`: Command-line interface tools
- `chaos-tests/`: Chaos engineering test configurations
- `k8s-manifests/`: Kubernetes deployment manifests
- `output/logs/`: Log output directory
- `scripts/`: Utility scripts for the project
- `smagent/`: Main source code package
- `simulate/`: Kubernetes failure simulation scenarios for testing the Root Cause Analysis engine
- `tests/`: Test cases and test utilities

## Kubernetes Failure Simulations

The `simulate/` directory contains YAML manifests for creating realistic Kubernetes failure scenarios to test the Root Cause Analysis engine. These scenarios simulate various common Kubernetes issues:

### Available Scenario Categories

- **Resource Issues**: Memory exhaustion, CPU throttling, resource quota limits
- **Network Issues**: Network policy blockage, DNS resolution failures, service connectivity 
- **Storage Issues**: PVC binding failures, storage performance issues, volume mount problems
- **Application Issues**: Kafka partition imbalance, Cassandra compaction slowness, database connection issues
- **Control Plane Issues**: API server overload, etcd performance issues, scheduler failures
- **Security Issues**: Certificate expiry, RBAC permissions, secret access problems
- **Observability Issues**: Logging pipeline failures, metrics service issues

### Running Simulations

The `simulate/apply-scenario.sh` script helps apply and manage simulation scenarios:

```bash
# Apply a scenario
./simulate/apply-scenario.sh simulate/resource-issues/memory-exhaustion.yaml

# Remove a scenario
./simulate/apply-scenario.sh simulate/resource-issues/memory-exhaustion.yaml --delete

# List available scenarios
./simulate/apply-scenario.sh
```

Each scenario includes:
- Detailed description of the issue
- Expected symptoms
- Expected root cause
- Resolution steps

These scenarios provide a controlled environment to test and validate the Root Cause Analysis capabilities of the multi-agent system.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 