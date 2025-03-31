# Kubernetes Failure Simulation Scenarios

This directory contains YAML files and utilities for simulating various failure scenarios in Kubernetes environments. These scenarios are designed to test the Root Cause Analysis (RCA) capabilities of monitoring and observability tools.

## Purpose

The purpose of these simulation scenarios is to:

1. Create controlled, reproducible failure conditions in Kubernetes environments
2. Generate symptoms similar to real-world problems that operators encounter
3. Test the effectiveness of root cause analysis tools in identifying the underlying issues
4. Provide a comprehensive test suite for evaluating monitoring and observability solutions
5. Educate operators about common failure patterns and their manifestations

## Directory Structure

- **resource-issues/** - CPU, memory, and resource quota-related failures
- **network-issues/** - Network connectivity, DNS, and policy-related failures
- **storage-issues/** - PVC, volume, and storage class-related failures
- **application-issues/** - Kafka, Cassandra, and other application-specific failures
- **control-plane-issues/** - API server, scheduler, and other control plane failures
- **security-issues/** - RBAC, certificate, and other security-related failures
- **observability-issues/** - Prometheus, logging, and other observability failures
- **cascade/** - Complex multi-component failure scenarios
- **deployment-issues/** - Deployment, rollout, and update-related failures

## Testing Methodology

Each scenario includes:
- YAML manifests to create the failure condition
- A description of the expected symptoms
- The expected root cause that should be identified
- Resolution steps for remediation
- Cleanup instructions to restore normal operation

## Usage Guidelines

1. **Testing Environment:** Always run these simulations in a dedicated testing environment, never in production.
2. **Controlled Testing:** Apply one scenario at a time and observe the results.
3. **Monitoring Setup:** Ensure your monitoring and observability tools are properly configured.
4. **Documentation:** Document the findings and effectiveness of your RCA tools for each scenario.
5. **Cleanup:** Always clean up after testing to avoid lingering issues.

## How to Use

```bash
# Apply a scenario
./apply-scenario.sh resource-issues/memory-exhaustion.yaml

# Remove a scenario
./apply-scenario.sh resource-issues/memory-exhaustion.yaml --delete

# List available scenarios
./apply-scenario.sh
```

## Scenario Categories

## Resource Issues
- [ ] **Memory Exhaustion** - `resource-issues/memory-exhaustion.yaml`
  - Description: Pod with memory leak exceeding its limits
  - Expected Root Cause: Container OOMKilled due to exceeding memory limits
  
- [ ] **CPU Throttling** - `resource-issues/cpu-throttling.yaml`
  - Description: Pod with CPU limits set too low causing performance degradation
  - Expected Root Cause: CPU throttling due to restrictive limits

- [ ] **Resource Quota Exhaustion** - `resource-issues/quota-exhaustion.yaml`
  - Description: Namespace with tight resource quotas preventing deployment
  - Expected Root Cause: Namespace quota exceeded, blocking new resources

- [ ] **Node Affinity Mismatch** - `resource-issues/node-affinity-mismatch.yaml`
  - Description: Pods with node affinity requirements that cannot be satisfied
  - Expected Root Cause: Pod scheduling failure due to unsatisfiable node affinity

- [ ] **HPA Misconfiguration** - `resource-issues/hpa-misconfiguration.yaml`
  - Description: HPA with incorrect metric configuration causing scaling issues
  - Expected Root Cause: HPA unable to fetch metrics or making incorrect scaling decisions
  
- [ ] **InitContainer Resource Starvation** - `resource-issues/init-container-starvation.yaml`
  - Description: Pod with init container requesting more resources than available
  - Expected Root Cause: Pod stuck in Init phase due to insufficient resources

## Network Issues
- [ ] **Network Policy Blockage** - `network-issues/network-policy-blockage.yaml`
  - Description: Network policy blocking legitimate traffic
  - Expected Root Cause: Overly restrictive network policy

- [ ] **DNS Resolution Failure** - `network-issues/dns-failure.yaml`
  - Description: CoreDNS issues causing name resolution problems
  - Expected Root Cause: DNS service performance or configuration issues

- [ ] **Service Endpoint Selector Mismatch** - `network-issues/endpoint-selector-mismatch.yaml`
  - Description: Service with selector not matching any pod labels
  - Expected Root Cause: Service configuration mismatch with pod labels

- [ ] **Ingress Path Routing Errors** - `network-issues/ingress-routing-error.yaml`
  - Description: Ingress with conflicting path rules or unreachable backends
  - Expected Root Cause: Misconfigured ingress rules causing routing failures

- [ ] **Headless Service DNS Issues** - `network-issues/headless-service-dns.yaml`
  - Description: StatefulSet with incorrectly configured headless service DNS
  - Expected Root Cause: DNS record configuration preventing pod-to-pod communication

- [ ] **LoadBalancer Provisioning Failure** - `network-issues/loadbalancer-provision-failure.yaml`
  - Description: Service with type LoadBalancer that fails to provision external IP
  - Expected Root Cause: Missing cloud permissions or configuration for LoadBalancer

## Storage Issues
- [ ] **PVC Binding Failure** - `storage-issues/pvc-binding-failure.yaml`
  - Description: PVC with non-existent storage class cannot be bound
  - Expected Root Cause: Missing or misconfigured storage class

- [ ] **StorageClass Parameters Misconfiguration** - `storage-issues/storageclass-param-error.yaml`
  - Description: StorageClass with invalid parameters for provisioner
  - Expected Root Cause: Storage provisioner cannot create volumes with provided parameters

- [ ] **Volume Mount Path Conflicts** - `storage-issues/volume-mount-conflict.yaml`
  - Description: Pod with multiple volumes mounted to same path
  - Expected Root Cause: Container fails to start due to volume mount conflicts

- [ ] **Retention Policy Issues** - `storage-issues/retention-policy-issue.yaml`
  - Description: PV with incorrect reclaim policy causing data loss
  - Expected Root Cause: Volume reclaimed unexpectedly due to policy misconfiguration

- [ ] **Volume Expansion Failure** - `storage-issues/volume-expansion-failure.yaml`
  - Description: PVC expansion attempt with non-supporting StorageClass
  - Expected Root Cause: Volume expansion operation fails due to storage class limitations

## Application Issues
- [ ] **Kafka Partition Imbalance** - `application-issues/kafka-imbalance.yaml`
  - Description: Kafka topics with imbalanced partitions causing slowness
  - Expected Root Cause: Uneven partition distribution across brokers

- [ ] **Cassandra Compaction Slowness** - `application-issues/cassandra-compaction.yaml`
  - Description: Cassandra slowed by compaction process
  - Expected Root Cause: Maintenance operations affecting performance

- [ ] **Liveness Probe Failures** - `application-issues/liveness-probe-failure.yaml`
  - Description: Application with misconfigured liveness probe causing restarts
  - Expected Root Cause: Probe configuration doesn't match application behavior

- [ ] **Environment Variable Injection Errors** - `application-issues/env-var-errors.yaml`
  - Description: Application missing critical environment variables
  - Expected Root Cause: Referenced ConfigMap or Secret doesn't exist or wrong key

- [ ] **ImagePullBackOff with Rate Limiting** - `application-issues/image-pull-rate-limit.yaml`
  - Description: Pods unable to pull images due to registry rate limits
  - Expected Root Cause: Container registry rate limit exceeded

- [ ] **Sidecar Container Failures** - `application-issues/sidecar-failure.yaml`
  - Description: Main container depends on failing sidecar
  - Expected Root Cause: Sidecar container failure affecting main container

## Control Plane Issues
- [ ] **API Server Overload** - `control-plane-issues/api-server-overload.yaml`
  - Description: Too many API requests overwhelming API server
  - Expected Root Cause: API server resource constraints or client flooding

- [ ] **Etcd Performance Issues** - `control-plane-issues/etcd-performance.yaml`
  - Description: Etcd slowness affecting API server responsiveness
  - Expected Root Cause: Etcd under resource pressure or misconfiguration

- [ ] **Admission Webhook Latency** - `control-plane-issues/webhook-latency.yaml`
  - Description: Slow admission webhook causing operation timeouts
  - Expected Root Cause: Webhook service performance issues

- [ ] **CRD Validation Failures** - `control-plane-issues/crd-validation-failure.yaml`
  - Description: Custom resources rejected due to validation failures
  - Expected Root Cause: CRD schema validation rules violated

- [ ] **API Server Request Throttling** - `control-plane-issues/api-throttling.yaml`
  - Description: API requests being throttled due to excessive volume
  - Expected Root Cause: API priority and fairness configuration causing throttling

- [ ] **Controller Manager Overload** - `control-plane-issues/controller-overload.yaml`
  - Description: Controller manager unable to keep up with reconciliation
  - Expected Root Cause: Too many objects or insufficient controller resources

## Security Issues
- [ ] **Certificate Expiry** - `security-issues/certificate-expiry.yaml`
  - Description: TLS certificate expired causing connection failures
  - Expected Root Cause: Expired certificate not renewed

- [ ] **RBAC Permission Cascade** - `security-issues/rbac-permission-cascade.yaml`
  - Description: Service account missing permissions for dependent resources
  - Expected Root Cause: Incomplete RBAC permissions for operation chain

- [ ] **Pod Security Policy Violations** - `security-issues/psp-violations.yaml`
  - Description: Pods rejected due to security policy violations
  - Expected Root Cause: Pod spec violates security policies

- [ ] **Secret Mounting Permission Issues** - `security-issues/secret-mount-permission.yaml`
  - Description: Container unable to access mounted secrets
  - Expected Root Cause: Incorrect file permissions on mounted secrets

- [ ] **Invalid Image Signature Verification** - `security-issues/image-signature-failure.yaml`
  - Description: Image fails signature verification in secure cluster
  - Expected Root Cause: Image not properly signed or verification misconfigured

## CI/CD and Deployment Issues
- [ ] **Blue/Green Deployment Service Switch Failure** - `deployment-issues/blue-green-switch-failure.yaml`
  - Description: Service selector not updated to point to new deployment
  - Expected Root Cause: Service selector unchanged during blue/green deployment

- [ ] **Canary Deployment Weight Misconfiguration** - `deployment-issues/canary-weight-error.yaml`
  - Description: Traffic improperly distributed in canary deployment
  - Expected Root Cause: Misconfigured traffic splitting weights

- [ ] **Rolling Update Blocked by PDB** - `deployment-issues/pdb-blocked-update.yaml`
  - Description: Deployment update stalled due to restrictive PDB
  - Expected Root Cause: Pod Disruption Budget preventing pod termination

- [ ] **Failed Job Backoff Explosion** - `deployment-issues/job-backoff-explosion.yaml`
  - Description: Failed job with exponential backoff causing long delays
  - Expected Root Cause: Job failure with improper backoff configuration

## Database and Stateful Application Issues
- [ ] **StatefulSet Ordering Violations** - `stateful-issues/statefulset-order-violation.yaml`
  - Description: StatefulSet pods starting in incorrect order
  - Expected Root Cause: Dependency requirements violated by ordering issues

- [ ] **Database Connection Pool Exhaustion** - `stateful-issues/connection-pool-exhaustion.yaml`
  - Description: Application unable to get database connections
  - Expected Root Cause: Connection pool limits too low for workload

- [ ] **Redis Master-Replica Split Brain** - `stateful-issues/redis-split-brain.yaml`
  - Description: Redis cluster with multiple masters due to network partition
  - Expected Root Cause: Network partition causing split-brain in Redis

- [ ] **Elasticsearch Split Brain** - `stateful-issues/elasticsearch-split-brain.yaml`
  - Description: Elasticsearch cluster with incorrect quorum settings
  - Expected Root Cause: Discovery and quorum settings allowing split-brain

## Multi-Cluster and Federation Issues
- [ ] **Stale KubeFed Resources** - `multi-cluster-issues/kubefed-stale-resources.yaml`
  - Description: Federated resources out of sync with member clusters
  - Expected Root Cause: Federation controller issues or network problems

- [ ] **Cross-Cluster Service Discovery Failures** - `multi-cluster-issues/cross-cluster-discovery.yaml`
  - Description: Services unreachable across clusters
  - Expected Root Cause: Service mesh or DNS configuration issues

## Infrastructure Issues
- [ ] **Kubelet Node Pressure** - `infrastructure-issues/node-pressure.yaml`
  - Description: Node under disk/memory pressure triggering evictions
  - Expected Root Cause: Node resource pressure exceeding thresholds

- [ ] **Node Taint Manager Conflicts** - `infrastructure-issues/taint-manager-conflict.yaml`
  - Description: System pods affected by node taints
  - Expected Root Cause: Taints affecting critical system components

- [ ] **Container Runtime Errors** - `infrastructure-issues/container-runtime-errors.yaml`
  - Description: Container creation failures at runtime
  - Expected Root Cause: Container runtime issues (Docker/containerd)

- [ ] **CNI Plugin Conflicts** - `infrastructure-issues/cni-plugin-conflict.yaml`
  - Description: Networking initialization failures in pods
  - Expected Root Cause: Conflicting CNI plugin configurations

## Cascade Failure Scenarios
- [ ] **Anti-Affinity Deadlock** - `cascade-issues/anti-affinity-deadlock.yaml`
  - Description: Pods cannot be scheduled due to complex anti-affinity
  - Expected Root Cause: Mutually incompatible anti-affinity rules

- [ ] **NodeLocal DNSCache Failure Cascade** - `cascade-issues/dns-cache-cascade.yaml`
  - Description: DNS performance degraded across cluster
  - Expected Root Cause: NodeLocal DNSCache failure affecting DNS resolution

- [ ] **Certificate Rotation Cascade** - `cascade-issues/cert-rotation-cascade.yaml`
  - Description: Certificate rotation failure affecting service mesh
  - Expected Root Cause: Certificate rotation causing authentication failures

- [ ] **API Priority and Fairness Cascade** - `cascade-issues/api-fairness-cascade.yaml`
  - Description: Lower priority workloads starved of API access
  - Expected Root Cause: API priority configuration causing resource starvation

- [ ] **Storage Throttling Cascade** - `cascade-issues/storage-throttling-cascade.yaml`
  - Description: Application performance affected by storage throttling
  - Expected Root Cause: Storage throttling cascading to application performance

- [ ] **Service Mesh Sidecar Resource Contention** - `cascade-issues/sidecar-resource-contention.yaml`
  - Description: Service mesh proxies consuming excessive resources
  - Expected Root Cause: Sidecar containers starving main application containers

## Observability Issues
- [ ] **Prometheus Resource Exhaustion** - `observability-issues/prometheus-exhaustion.yaml`
  - Description: Prometheus running out of resources, affecting metrics
  - Expected Root Cause: Insufficient resources for metrics volume

- [ ] **Logging Pipeline Failure** - `observability-issues/logging-pipeline-failure.yaml`
  - Description: Logs not being collected or forwarded
  - Expected Root Cause: Logging agent or centralized logging issue

## Adding New Scenarios

When adding new scenarios:

1. Create the YAML file in the appropriate category directory
2. Update this README.md checklist
3. Test the scenario with the apply-scenario.sh script
4. Document expected symptoms and root causes in the YAML's ConfigMap

Each scenario should include:
- All necessary Kubernetes resources to create the issue
- A ConfigMap with detailed description and expected behaviors
- Clear symptoms that would be visible to operators
- The expected root cause that the analysis engine should identify 

### Deployment Issues

| Scenario | Description | YAML File | Expected Root Cause | Verified |
|----------|-------------|-----------|---------------------|----------|
| Blue/Green Deployment Service Switch Failure | Service selector isn't updated to point to new version | [blue-green-switch-failure.yaml](deployment-issues/blue-green-switch-failure.yaml) | Incomplete deployment process | ❌ | 