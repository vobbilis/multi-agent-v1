# Kubernetes Failure Simulation Scenarios

This document provides an overview of the simulation scenarios included in the system for testing and validating the root cause analysis capabilities. These scenarios are designed to replicate realistic failure patterns in Kubernetes environments.

## Overview

The simulation scenarios are organized into categories based on the type of failure they represent. Each scenario is implemented as a set of Kubernetes manifests that create controlled failure conditions when applied to a cluster. These scenarios are used for:

1. Testing the detection capabilities of the root cause analysis system
2. Training the system on new failure patterns
3. Validating remediation recommendations
4. Demonstrating the system's capabilities
5. Supporting development of new analysis algorithms

## Scenario Structure

Each simulation scenario follows a standard structure:

1. **Namespace Creation**: Isolated namespace for the scenario
2. **Application Components**: Deployments, services, etc. that will exhibit the failure
3. **Failure Triggers**: Resources or conditions that cause the failure
4. **Diagnostic Components**: Tools to observe and validate the scenario
5. **Documentation ConfigMap**: Description, expected symptoms, and root cause

Example:
```yaml
# Namespace for isolation
apiVersion: v1
kind: Namespace
metadata:
  name: simulation-resource-issues
  labels:
    scenario: memory-exhaustion
---
# Application component that will fail
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-hog
  namespace: simulation-resource-issues
spec:
  # Deployment spec
---
# Scenario documentation
apiVersion: v1
kind: ConfigMap
metadata:
  name: memory-exhaustion-scenario-info
  namespace: simulation-resource-issues
data:
  description: |
    Memory Exhaustion Scenario
    
    This scenario creates a pod that consumes memory
    beyond its limits, triggering OOM killing.
    
    Expected Symptoms:
    - Container restarts
    - OOMKilled status
    - Warning events for memory usage
    
    Root Cause:
    Container exceeding its memory limits due to
    improper resource management or memory leak.
```

## Scenario Categories

### Resource Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Memory Exhaustion | Pod with memory leak exceeding its limits | Container OOMKilled due to exceeding memory limits | [memory-exhaustion.yaml](../../simulate/resource-issues/memory-exhaustion.yaml) |
| CPU Throttling | Pod with CPU limits set too low | CPU throttling due to restrictive limits | [cpu-throttling.yaml](../../simulate/resource-issues/cpu-throttling.yaml) |
| Resource Quota Exhaustion | Namespace with tight resource quotas | Namespace quota exceeded, blocking new resources | [quota-exhaustion.yaml](../../simulate/resource-issues/quota-exhaustion.yaml) |
| Node Affinity Mismatch | Pods with unsatisfiable node affinity | Pod scheduling failure due to node affinity rules | [node-affinity-mismatch.yaml](../../simulate/resource-issues/node-affinity-mismatch.yaml) |

### Network Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Network Policy Blockage | Overly restrictive network policy | Network policy blocking legitimate traffic | [restrictive-netpol.yaml](../../simulate/network-issues/restrictive-netpol.yaml) |
| DNS Resolution Failure | CoreDNS issues causing name resolution problems | DNS service overload or configuration issues | [dns-failure.yaml](../../simulate/network-issues/dns-failure.yaml) |
| Service Endpoint Mismatch | Service selector not matching pod labels | Service configuration mismatch with pod labels | [endpoint-selector-mismatch.yaml](../../simulate/network-issues/endpoint-selector-mismatch.yaml) |

### Storage Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| PVC Binding Failure | PVC with non-existent storage class | Missing or misconfigured storage class | [pvc-binding-failure.yaml](../../simulate/storage-issues/pvc-binding-failure.yaml) |

### Application Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Kafka Partition Imbalance | Kafka topics with imbalanced partitions | Uneven partition distribution across brokers | [kafka-imbalance.yaml](../../simulate/application-issues/kafka-imbalance.yaml) |
| Cassandra Compaction Slowness | Cassandra slowed by compaction process | Maintenance operations affecting performance | [cassandra-compaction.yaml](../../simulate/application-issues/cassandra-compaction.yaml) |
| Liveness Probe Failures | App with misconfigured liveness probe | Probe configuration doesn't match app behavior | [liveness-probe-failure.yaml](../../simulate/application-issues/liveness-probe-failure.yaml) |

### Control Plane Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| API Server Throttling | API requests being throttled | API priority and fairness configuration issues | [api-throttling.yaml](../../simulate/control-plane-issues/api-throttling.yaml) |

### Security Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Certificate Expiry | TLS certificate expired | Expired certificate not renewed | [certificate-expiry.yaml](../../simulate/security-issues/certificate-expiry.yaml) |
| RBAC Permission Cascade | Missing permissions for dependent resources | Incomplete RBAC permissions for operation chain | [rbac-permission-cascade.yaml](../../simulate/security-issues/rbac-permission-cascade.yaml) |

### Deployment Issues

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Blue/Green Deployment Failure | Service selector not updated | Service selector unchanged during deployment | [blue-green-switch-failure.yaml](../../simulate/deployment-issues/blue-green-switch-failure.yaml) |

### Cascade Failures

| Scenario | Description | Expected Root Cause | File Path |
|----------|-------------|---------------------|-----------|
| Etcd → API Server → Scheduler | Cascading failure starting with etcd | Etcd performance issues affecting dependent components | [etcd-apiserver-scheduler.yaml](../../simulate/cascade/etcd-apiserver-scheduler.yaml) |

## Using the Scenarios

### Applying a Scenario

To apply a scenario to a Kubernetes cluster:

```bash
# Using kubectl directly
kubectl apply -f simulate/resource-issues/memory-exhaustion.yaml

# Using the provided script
./simulate/apply-scenario.sh resource-issues/memory-exhaustion.yaml
```

### Removing a Scenario

To remove a scenario from a Kubernetes cluster:

```bash
# Using kubectl directly
kubectl delete -f simulate/resource-issues/memory-exhaustion.yaml

# Using the provided script
./simulate/apply-scenario.sh resource-issues/memory-exhaustion.yaml --delete
```

### Observing Scenario Symptoms

Each scenario includes diagnostic components that help observe the symptoms:

```bash
# Get the scenario namespace
NAMESPACE=$(kubectl get ns -l scenario=memory-exhaustion -o name | cut -d/ -f2)

# Check pod status
kubectl get pods -n $NAMESPACE

# View scenario description
kubectl describe configmap -n $NAMESPACE memory-exhaustion-scenario-info

# View diagnostic job logs
kubectl logs -n $NAMESPACE -l job-name=memory-diagnosis
```

### Testing Root Cause Analysis

To test the root cause analysis system against a scenario:

```python
from analysis.engine import AnalysisEngine
from simulation.engine import SimulationEngine

# Deploy scenario
sim_engine = SimulationEngine()
deployment = sim_engine.deploy_scenario("resource-issues/memory-exhaustion.yaml")

# Allow symptoms to develop
import time
time.sleep(60)

# Run analysis
analysis_engine = AnalysisEngine()
result = analysis_engine.analyze(
    context={"namespace": deployment.namespace}
)

# Check if root cause was identified correctly
expected_cause = "Container memory limit exceeded"
actual_cause = result.root_cause.description
confidence = result.confidence_score

print(f"Expected: {expected_cause}")
print(f"Detected: {actual_cause}")
print(f"Confidence: {confidence}%")

# Cleanup
sim_engine.cleanup(deployment.id)
```

## Extending the Scenarios

### Adding a New Scenario

To add a new scenario:

1. Identify the failure pattern you want to simulate
2. Create a YAML file in the appropriate category directory
3. Follow the standard structure (namespace, components, documentation)
4. Test the scenario to ensure it produces the expected symptoms
5. Add the scenario to this documentation

### Best Practices for Scenario Development

1. **Isolation**: Ensure scenarios are isolated in their own namespace
2. **Documentation**: Include clear documentation of expected symptoms and root cause
3. **Diagnostics**: Add diagnostic components to validate the scenario
4. **Cleanup**: Ensure all resources can be easily removed
5. **Resource Limits**: Set appropriate resource requests and limits
6. **Validation**: Include a mechanism to verify the scenario is working as expected
7. **Progressive Complexity**: Start with simple scenarios before creating complex ones

## Scenario Validation Methodology

Each scenario should be validated to ensure it:

1. **Deploys Correctly**: All resources are created successfully
2. **Generates Symptoms**: The expected symptoms appear
3. **Remains Isolated**: No impact on other namespaces or clusters
4. **Cleans Up Properly**: All resources are removed on cleanup
5. **Is Detectable**: The root cause analysis system can detect the issue
6. **Is Reproducible**: The scenario behaves consistently when redeployed

## References

- [Simulation Engine Documentation](../components/simulation_engine.md)
- [Root Cause Analysis Testing](../testing/root_cause_testing.md)
- [Kubernetes Resource Definitions](https://kubernetes.io/docs/reference/kubernetes-api/)
- [Chaos Engineering Principles](https://principlesofchaos.org/)
- [Original Scenario Implementations](../../simulate/README.md) 