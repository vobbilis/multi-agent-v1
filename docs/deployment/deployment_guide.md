# Deployment Guide

This guide provides comprehensive instructions for deploying the Multi-Agent Root Cause Analysis System in various environments. It covers prerequisites, installation steps, configuration options, and best practices for deployment.

## System Requirements

### Minimum Requirements

- Kubernetes cluster v1.20+
- 4 CPU cores (minimum)
- 8GB RAM (minimum)
- 20GB disk space
- Python 3.9+
- Connectivity to the Kubernetes API server
- Network access to log and metrics sources

### Recommended Requirements

- Kubernetes cluster v1.24+
- 8 CPU cores
- 16GB RAM
- 50GB SSD storage
- Python 3.10+
- Persistent storage for the knowledge base
- Prometheus and Elasticsearch for metrics and logs

## Deployment Architectures

The system supports three primary deployment models:

### 1. In-Cluster Deployment

The entire system runs as pods within the target Kubernetes cluster.

**Advantages:**
- Simplified access to Kubernetes API
- Automatic scaling with cluster capacity
- Native integration with Kubernetes security

**Disadvantages:**
- System may be affected by cluster-wide issues
- Resource consumption within the monitored cluster
- May miss some control plane issues

![In-Cluster Deployment](../diagrams/in_cluster_deployment.png)

### 2. External Deployment

The system runs outside the target cluster, connecting via the Kubernetes API.

**Advantages:**
- Independent from cluster failures
- Can monitor multiple clusters
- Not affected by cluster resource constraints

**Disadvantages:**
- Requires external infrastructure
- More complex security setup
- May have limited access to some data sources

![External Deployment](../diagrams/external_deployment.png)

### 3. Hybrid Deployment

Core components run externally while data collection agents run within the cluster.

**Advantages:**
- Balance of isolation and access
- Resilient to cluster issues
- Good data collection capabilities

**Disadvantages:**
- More complex architecture
- Requires both internal and external security configuration
- More challenging to troubleshoot

![Hybrid Deployment](../diagrams/hybrid_deployment.png)

## Deployment Options

### Kubernetes Deployment

The recommended way to deploy the system is using Kubernetes manifests or Helm charts.

#### Using Manifests

1. Clone the repository:
   ```bash
   git clone https://github.com/vobbilis/multi-agent-v1.git
   cd multi-agent-v1
   ```

2. Apply the base manifests:
   ```bash
   kubectl apply -f k8s-manifests/namespace.yaml
   kubectl apply -f k8s-manifests/rbac.yaml
   kubectl apply -f k8s-manifests/configmaps.yaml
   kubectl apply -f k8s-manifests/secrets.yaml
   ```

3. Deploy the core components:
   ```bash
   kubectl apply -f k8s-manifests/orchestrator.yaml
   kubectl apply -f k8s-manifests/specialist-agents.yaml
   kubectl apply -f k8s-manifests/analysis-engine.yaml
   kubectl apply -f k8s-manifests/knowledge-base.yaml
   ```

4. Deploy the optional components:
   ```bash
   kubectl apply -f k8s-manifests/visualization.yaml
   kubectl apply -f k8s-manifests/api-gateway.yaml
   ```

#### Using Helm

1. Add the Helm repository:
   ```bash
   helm repo add multi-agent https://vobbilis.github.io/multi-agent-v1/charts
   helm repo update
   ```

2. Install the chart:
   ```bash
   helm install rca multi-agent/root-cause-analysis \
     --namespace rca-system \
     --create-namespace \
     --set global.environment=production
   ```

### Local Development Deployment

For development or testing purposes, you can run the system locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/vobbilis/multi-agent-v1.git
   cd multi-agent-v1
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure KUBECONFIG:
   ```bash
   export KUBECONFIG=~/.kube/config
   ```

5. Run the system:
   ```bash
   python main.py --config config/development.yaml
   ```

## Configuration

### Main Configuration File

The system is configured through a YAML configuration file. Example:

```yaml
# config/production.yaml
global:
  environment: production
  log_level: info
  telemetry_enabled: true

kubernetes:
  context: production-cluster
  namespace: rca-system
  in_cluster: true

agents:
  logs:
    enabled: true
    sources:
      - type: elasticsearch
        url: http://elasticsearch:9200
  events:
    enabled: true
  resources:
    enabled: true
  network:
    enabled: true

analysis:
  confidence_threshold: 75.0
  max_processing_time: 300

api:
  port: 8080
  enabled: true
  auth:
    type: bearer
    jwt_secret: ${JWT_SECRET}

storage:
  type: postgresql
  url: ${DATABASE_URL}
  
llm:
  provider: openai
  model: gpt-4
  api_key: ${OPENAI_API_KEY}
```

### Environment Variables

The system uses environment variables for sensitive configuration and overrides:

| Variable | Description | Default |
|----------|-------------|---------|
| `RCA_CONFIG_PATH` | Path to configuration file | `config/production.yaml` |
| `RCA_LOG_LEVEL` | Logging verbosity | `info` |
| `RCA_NAMESPACE` | Kubernetes namespace | `rca-system` |
| `DATABASE_URL` | Database connection string | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `JWT_SECRET` | Secret for JWT authentication | - |

### Secrets Management

For Kubernetes deployments, use Kubernetes Secrets to manage sensitive information:

```bash
# Create secrets from literal values
kubectl create secret generic rca-secrets \
  --namespace rca-system \
  --from-literal=database-url='postgresql://user:password@db:5432/rca' \
  --from-literal=openai-api-key='sk-your-api-key' \
  --from-literal=jwt-secret='your-jwt-secret'

# Create secrets from files
kubectl create secret generic rca-tls \
  --namespace rca-system \
  --from-file=tls.crt=./certs/tls.crt \
  --from-file=tls.key=./certs/tls.key
```

## Security Considerations

### Authentication and Authorization

1. **API Authentication**:
   - JWT token-based authentication
   - OAuth2 integration options
   - API key authentication for service accounts

2. **Kubernetes RBAC**:
   - Dedicated service account for the system
   - Principle of least privilege for permissions
   - Regular review of RBAC policies

3. **Secrets Management**:
   - Use Kubernetes Secrets or external secret managers
   - Encryption of secrets at rest
   - Rotation policies for credentials

### Network Security

1. **API Endpoint Security**:
   - TLS encryption for all endpoints
   - Network policies to restrict access
   - Rate limiting to prevent abuse

2. **Kubernetes API Access**:
   - Secure connection to Kubernetes API
   - Minimal API permissions required
   - Audit logging of all API requests

3. **Data Source Security**:
   - Secure connections to logs and metrics sources
   - Read-only access to data sources
   - Proper authentication to all external systems

## Scaling and High Availability

### Horizontal Scaling

The system supports horizontal scaling of components:

1. **Specialist Agents**:
   - Deploy multiple replicas for high-throughput environments
   - Configure with different specializations if needed

2. **Analysis Engine**:
   - Scale horizontally for parallel analysis of multiple incidents
   - Use leader election for coordinated processing

3. **API Gateway**:
   - Deploy multiple replicas behind a load balancer
   - Configure session affinity if needed

### High Availability Configuration

For production environments, enable high availability:

```yaml
# High availability configuration
orchestrator:
  replicas: 3
  podAntiAffinity: true
  leaderElection: true

specialist_agents:
  logs:
    replicas: 3
    podAntiAffinity: true
  events:
    replicas: 3
    podAntiAffinity: true

analysis_engine:
  replicas: 2
  podAntiAffinity: true

api_gateway:
  replicas: 2
  podAntiAffinity: true
```

### Resource Allocation

Configure appropriate resource requests and limits:

```yaml
resources:
  orchestrator:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
      
  specialist_agents:
    logs:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 4Gi
```

## Integration with External Systems

### Log Sources

1. **Elasticsearch**:
   ```yaml
   agents:
     logs:
       sources:
         - type: elasticsearch
           url: http://elasticsearch:9200
           index_pattern: "kubernetes-*"
           credentials:
             username: ${ES_USERNAME}
             password: ${ES_PASSWORD}
   ```

2. **Loki**:
   ```yaml
   agents:
     logs:
       sources:
         - type: loki
           url: http://loki:3100
           query_range_path: "/loki/api/v1/query_range"
   ```

3. **File Logs**:
   ```yaml
   agents:
     logs:
       sources:
         - type: file
           paths:
             - /var/log/containers/*.log
           parser: json
   ```

### Metrics Sources

1. **Prometheus**:
   ```yaml
   agents:
     resources:
       sources:
         - type: prometheus
           url: http://prometheus:9090
           query_path: "/api/v1/query"
   ```

2. **Metrics Server**:
   ```yaml
   agents:
     resources:
       sources:
         - type: metrics_server
           in_cluster: true
   ```

### Alerting Systems

1. **Alertmanager**:
   ```yaml
   integrations:
     alerting:
       - type: alertmanager
         url: http://alertmanager:9093
         receivers:
           - name: rca-notifications
             webhook_configs:
               - url: http://rca-system-api/alerts
   ```

2. **Slack**:
   ```yaml
   integrations:
     alerting:
       - type: slack
         webhook_url: ${SLACK_WEBHOOK_URL}
         channel: "#incidents"
         username: "RCA System"
   ```

## Maintenance and Operations

### Health Monitoring

Monitor the system's health using the built-in health endpoints:

- `/health/live`: Liveness check
- `/health/ready`: Readiness check
- `/health/startup`: Startup check

Example Kubernetes liveness probe:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Logging and Observability

1. **Logging Configuration**:
   ```yaml
   logging:
     format: json
     level: info
     output: stdout
     structured: true
     include_trace_id: true
   ```

2. **Metrics Exposure**:
   ```yaml
   metrics:
     enabled: true
     port: 9090
     path: /metrics
     format: prometheus
   ```

3. **Distributed Tracing**:
   ```yaml
   tracing:
     enabled: true
     provider: jaeger
     endpoint: http://jaeger-collector:14268/api/traces
     service_name: rca-system
   ```

### Backup and Restore

1. **Knowledge Base Backup**:
   ```bash
   # Backup the knowledge base
   kubectl exec -n rca-system deploy/knowledge-base -- /app/scripts/backup.sh > knowledge-base-backup.json
   ```

2. **Configuration Backup**:
   ```bash
   # Backup all ConfigMaps and Secrets
   kubectl get configmaps -n rca-system -o yaml > configmaps-backup.yaml
   kubectl get secrets -n rca-system -o yaml > secrets-backup.yaml
   ```

3. **Restore Procedure**:
   ```bash
   # Restore the knowledge base
   kubectl exec -i -n rca-system deploy/knowledge-base -- /app/scripts/restore.sh < knowledge-base-backup.json
   ```

## Troubleshooting

### Common Issues and Solutions

1. **Connection to Kubernetes API fails**:
   - Verify KUBECONFIG environment variable
   - Check service account permissions
   - Ensure network connectivity to API server

2. **Specialist Agents not collecting data**:
   - Verify data source configuration
   - Check connectivity to data sources
   - Inspect agent logs for authentication issues

3. **Analysis Engine not producing results**:
   - Check confidence threshold settings
   - Verify that specialist agents are providing findings
   - Inspect analysis engine logs for processing errors

4. **System Performance Issues**:
   - Monitor resource usage of components
   - Adjust resource limits if needed
   - Consider scaling horizontally for high load

### Diagnostic Commands

```bash
# Check component status
kubectl get pods -n rca-system

# View component logs
kubectl logs -n rca-system deploy/orchestrator

# Check configuration
kubectl describe configmap -n rca-system rca-config

# Access shell in a component
kubectl exec -it -n rca-system deploy/orchestrator -- /bin/bash

# Check API connectivity
kubectl port-forward -n rca-system svc/api-gateway 8080:8080
curl http://localhost:8080/api/v1/status
```

## References

- [System Architecture](../architecture/system_overview.md)
- [Component Documentation](../components/README.md)
- [Configuration Reference](configuration.md)
- [Security Guide](security.md)
- [API Documentation](../api/api_reference.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/) 