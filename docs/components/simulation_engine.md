# Simulation Engine

## Overview

The Simulation Engine is a specialized component that creates controlled failure scenarios in Kubernetes environments to test, validate, and improve the root cause analysis capabilities of the system. It provides a comprehensive library of realistic failure patterns that can be deployed in test clusters to generate symptoms and conditions similar to real-world issues.

## Responsibilities

- Creating reproducible failure scenarios in Kubernetes environments
- Simulating various types of failures (resource, network, application, etc.)
- Generating controlled symptoms for testing detection capabilities
- Providing a testing framework for the root cause analysis system
- Supporting the training and improvement of analysis algorithms
- Validating remediation recommendations in controlled environments
- Documenting expected symptoms and root causes for each scenario

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Simulation Engine                            │
│                                                                  │
│  ┌─────────────────┐      ┌─────────────────┐                    │
│  │ Scenario        │      │ Deployment      │                    │
│  │ Library         │─────►│ Manager         │                    │
│  └─────────────────┘      └───────┬─────────┘                    │
│                                   │                              │
│                                   ▼                              │
│  ┌─────────────────┐      ┌─────────────────┐                    │
│  │ Validation      │◄────►│ Chaos           │                    │
│  │ Framework       │      │ Controller      │                    │
│  └─────────────────┘      └───────┬─────────┘                    │
│                                   │                              │
│                                   ▼                              │
│  ┌─────────────────┐      ┌─────────────────┐                    │
│  │ Result          │◄────►│ Cleanup         │                    │
│  │ Recorder        │      │ Manager         │                    │
│  └─────────────────┘      └─────────────────┘                    │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                            │
└──────────────────────────────────────────────────────────────────┘
```

## Implementation Details

The Simulation Engine is implemented with the following key components:

1. **Scenario Library**: Collection of predefined failure scenarios:
   - YAML manifests for creating specific failure conditions
   - Bash scripts for orchestrating complex scenarios
   - ConfigMaps with scenario descriptions and expected outcomes
   - Categorized by failure type and affected components

2. **Deployment Manager**: Controls the application of scenarios:
   - Validates scenario manifests before application
   - Manages scenario deployment to target clusters
   - Handles dependencies between components
   - Ensures proper isolation of test environments
   - Monitors deployment progress and status

3. **Chaos Controller**: Implements controlled disruptions:
   - Executes predefined failure patterns
   - Controls timing and severity of disruptions
   - Monitors the impact of injected failures
   - Provides fine-grained control over failure conditions
   - Supports various chaos engineering techniques

4. **Validation Framework**: Verifies scenario outcomes:
   - Confirms that expected symptoms are present
   - Validates that failure conditions match specifications
   - Checks system behavior against expected patterns
   - Ensures reproducibility of scenarios
   - Verifies isolation from other components

5. **Result Recorder**: Captures scenario execution data:
   - Logs all actions and system responses
   - Collects metrics during scenario execution
   - Records timestamps for event sequencing
   - Preserves evidence for later analysis
   - Generates execution reports and summaries

6. **Cleanup Manager**: Ensures proper scenario termination:
   - Removes all scenario-related resources
   - Restores system to pre-test state
   - Validates complete cleanup of test artifacts
   - Handles cleanup failure gracefully
   - Provides cleanup verification

## Scenario Categories

The Simulation Engine supports a wide range of failure scenarios organized into the following categories:

1. **Resource Issues**:
   - Memory exhaustion and OOM conditions
   - CPU throttling and starvation
   - Resource quota exhaustion
   - Node affinity mismatches
   - Init container resource starvation

2. **Network Issues**:
   - Network policy misconfiguration
   - DNS resolution failures
   - Service endpoint selector mismatches
   - Ingress routing errors
   - Load balancer provisioning failures

3. **Storage Issues**:
   - PVC binding failures
   - StorageClass parameter errors
   - Volume mount conflicts
   - Retention policy issues
   - Volume expansion failures

4. **Application Issues**:
   - Kafka partition imbalances
   - Cassandra compaction slowness
   - Liveness probe failures
   - Environment variable injection errors
   - Image pull rate limiting

5. **Control Plane Issues**:
   - API server overload
   - Etcd performance degradation
   - Admission webhook latency
   - CRD validation failures
   - Controller manager overload

6. **Security Issues**:
   - Certificate expiry
   - RBAC permission cascade failures
   - Pod security policy violations
   - Secret mounting permission issues
   - Invalid image signatures

7. **Deployment Issues**:
   - Blue/green deployment service switch failures
   - Canary deployment weight misconfiguration
   - Rolling update blocked by PDB
   - Failed job backoff issues

8. **Cascade Failures**:
   - Etcd -> API Server -> Scheduler cascade
   - Network latency -> Service discovery -> Application performance
   - Storage throttling cascade
   - Service mesh sidecar resource contention

## Scenario Implementation

Each scenario follows a standard structure:

```yaml
# Example: memory-exhaustion.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: simulation-resource-issues
  labels:
    scenario: memory-exhaustion
---
# Memory-hungry deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-hog
  namespace: simulation-resource-issues
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-hog
  template:
    metadata:
      labels:
        app: memory-hog
    spec:
      containers:
      - name: memory-hog
        image: alpine:3.14
        command: ["/bin/sh", "-c"]
        args:
        - |
          # Consume memory until OOM killed
          dd if=/dev/zero of=/dev/null bs=1M count=1024
          sleep 3600
        resources:
          requests:
            memory: "64Mi"
          limits:
            memory: "128Mi"
---
# ConfigMap with scenario information
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

## Interfaces

### Input

The Simulation Engine accepts the following inputs:

1. **Scenario Selection**: Specification of which failure scenario to deploy
2. **Target Environment**: Kubernetes cluster and namespace information
3. **Execution Parameters**: Customization options for the scenario
4. **Duration Settings**: How long the scenario should run
5. **Validation Options**: What aspects to validate during execution

### Output

The Simulation Engine produces the following outputs:

1. **Deployment Status**: Information about successful deployment
2. **Execution Logs**: Detailed logs of scenario execution
3. **Validation Results**: Confirmation that expected conditions were created
4. **Resource Status**: State of affected Kubernetes resources
5. **Cleanup Results**: Confirmation of successful cleanup

## Usage

The Simulation Engine can be used through:

1. **Command Line Interface**:
   ```bash
   # Apply a scenario
   ./simulate/apply-scenario.sh resource-issues/memory-exhaustion.yaml
   
   # Remove a scenario
   ./simulate/apply-scenario.sh resource-issues/memory-exhaustion.yaml --delete
   
   # List available scenarios
   ./simulate/apply-scenario.sh
   ```

2. **Python API**:
   ```python
   from simulation.engine import SimulationEngine
   
   # Initialize the engine
   sim_engine = SimulationEngine(kubernetes_config="~/.kube/config")
   
   # Deploy a scenario
   deployment = sim_engine.deploy_scenario(
       scenario="resource-issues/memory-exhaustion.yaml",
       namespace="test-simulation",
       duration="10m"
   )
   
   # Check status
   status = sim_engine.get_status(deployment_id=deployment.id)
   print(f"Scenario status: {status.phase}")
   
   # Cleanup
   sim_engine.cleanup(deployment_id=deployment.id)
   ```

## Integration with Testing Framework

The Simulation Engine integrates with the testing framework to:

1. **Automate Validation**: Verify root cause analysis accuracy
   ```python
   from tests.framework import TestFramework
   from simulation.engine import SimulationEngine
   
   # Setup test
   framework = TestFramework()
   sim_engine = SimulationEngine()
   
   # Deploy scenario
   deployment = sim_engine.deploy_scenario("resource-issues/memory-exhaustion.yaml")
   
   # Allow symptoms to appear
   framework.wait_for_condition(deployment, "OOMKilled")
   
   # Trigger analysis
   analysis_result = framework.trigger_analysis(deployment.namespace)
   
   # Validate results
   assert analysis_result.primary_cause == "Container memory limit exceeded"
   assert analysis_result.confidence_score > 80.0
   
   # Cleanup
   sim_engine.cleanup(deployment.id)
   ```

2. **Performance Testing**: Measure system responsiveness
   ```python
   import time
   from simulation.engine import SimulationEngine
   from analysis.engine import AnalysisEngine
   
   # Setup
   sim_engine = SimulationEngine()
   analysis_engine = AnalysisEngine()
   
   # Deploy scenario
   deployment = sim_engine.deploy_scenario("resource-issues/memory-exhaustion.yaml")
   
   # Wait for stability
   time.sleep(60)
   
   # Measure analysis performance
   start_time = time.time()
   analysis_result = analysis_engine.analyze(context={"namespace": deployment.namespace})
   duration = time.time() - start_time
   
   print(f"Analysis completed in {duration:.2f} seconds")
   print(f"Root cause identified: {analysis_result.primary_cause}")
   
   # Cleanup
   sim_engine.cleanup(deployment.id)
   ```

## Configuration

The Simulation Engine is configurable through:

1. **Environment Variables**:
   - `SIMULATION_ENGINE_LOG_LEVEL`: Sets the logging verbosity
   - `SIMULATION_ENGINE_TIMEOUT`: Default timeout for scenario operations
   - `SIMULATION_ENGINE_CLEANUP_ON_EXIT`: Automatically cleanup on termination

2. **Configuration File** (simulation_engine_config.yaml):
   ```yaml
   kubernetes:
     config_path: "~/.kube/config"
     default_namespace: "simulation"
     context: "test-cluster"
   
   execution:
     default_timeout: 600
     retry_attempts: 3
     retry_interval: 10
     parallel_scenarios: true
   
   validation:
     validate_deployment: true
     validate_symptoms: true
     validation_interval: 15
     validation_timeout: 300
   
   cleanup:
     force_cleanup: true
     cleanup_timeout: 120
     verify_cleanup: true
   ```

## Best Practices

1. **Isolation**: Always run scenarios in dedicated namespaces
2. **Resource Limits**: Set appropriate cluster resource quotas to prevent test impact on other workloads
3. **Validation**: Always validate that scenarios are generating expected symptoms
4. **Cleanup**: Ensure thorough cleanup after scenario completion
5. **Documentation**: Maintain clear descriptions of expected behaviors for each scenario
6. **Progressive Testing**: Start with simple scenarios before testing complex cascade failures
7. **Monitoring**: Monitor cluster health during scenario execution

## Error Handling

The Simulation Engine implements robust error handling for:

1. **Deployment Failures**: Gracefully handles failed scenario deployments
2. **Kubernetes API Issues**: Retries operations with exponential backoff
3. **Validation Failures**: Clearly reports when expected conditions aren't met
4. **Cleanup Failures**: Attempts recovery and reports remaining resources
5. **Timeout Management**: Enforces timeouts for all operations

## Future Enhancements

Planned enhancements for the Simulation Engine include:

1. **Scenario Composition**: Supporting the combination of multiple failure patterns
2. **Dynamic Scenarios**: Runtime modification of failure characteristics
3. **Graduated Severity**: Progressive intensification of failure conditions
4. **Custom Metric Generation**: Generating specific metrics patterns for testing
5. **Multi-Cluster Scenarios**: Simulating failures across cluster boundaries
6. **Schedule-Based Execution**: Time-based execution of scenario sequences

## References

- [Scenario Library](../../simulate/README.md)
- [Implementation Details](../../simulation/engine.py)
- [Testing Framework Integration](../../tests/framework.py)
- [Usage Examples](../../examples/simulation/) 