# Cascade Failure Simulation Scenarios

This directory contains advanced simulation scenarios that create cascading failures across multiple Kubernetes components. These scenarios are particularly valuable for testing the root cause analysis engine's ability to identify the *primary* cause in a chain of related symptoms.

## What Are Cascade Failures?

Cascade failures occur when a problem in one component triggers issues in dependent components, creating a chain reaction of failures or degraded performance. These scenarios are among the most challenging to diagnose because:

1. Symptoms appear in multiple places simultaneously
2. Logs and metrics show problems across various components
3. The original root cause may be obscured by more visible downstream effects
4. Traditional monitoring might alert on the symptoms rather than the cause

## Scenarios Included

| Scenario | Description | Key Components Affected |
|----------|-------------|-------------------------|
| [etcd-apiserver-scheduler.yaml](etcd-apiserver-scheduler.yaml) | Etcd performance issues cascade to API server and scheduler | etcd → API Server → Scheduler |
| [network-dns-application.yaml](network-dns-application.yaml) | Network latency affecting service discovery, causing application slowdowns | Network → CoreDNS → Application Services |
| [node-eviction-service.yaml](node-eviction-service.yaml) | Node pressure triggering evictions, causing service disruption | Node Resources → Pod Evictions → Service Availability |
| [database-cache-api.yaml](database-cache-api.yaml) | Database slowdown affecting cache warming, causing API slowness | Database → Cache → API Services |
| [cert-webhook-deployment.yaml](cert-webhook-deployment.yaml) | Expired certs causing webhook failures, blocking deployments | Certificates → Admission Webhooks → Deployments |

## Testing Methodology

When testing cascade failures:

1. Apply the scenario: `kubectl apply -f cascade/<scenario>.yaml`
2. Wait for the failure to fully develop (times vary by scenario, typically 3-5 minutes)
3. Run the root cause analysis with the symptoms described in the scenario
4. Verify that the tool correctly identifies the *primary* cause, not just the symptoms
5. Assess whether the tool properly explains the relationships between cause and effects
6. Clean up: `kubectl delete -f cascade/<scenario>.yaml`

## Success Criteria

The root cause analysis tool should be able to:

1. Identify the initiating component failure (primary cause)
2. Explain how the issue propagates through the system
3. Show the cause-and-effect relationships between components
4. Recommend fixing the primary issue first, rather than just addressing symptoms
5. Provide a comprehensive remediation strategy that accounts for the entire failure path

## Expected Challenges

These scenarios intentionally create situations where:

- Multiple components show high error rates simultaneously
- Logs from different components show different types of errors
- The component with the most visible symptoms may not be the root cause
- Time delays between cause and effect may obscure relationships
- Standard monitoring tools may point to different culprits

## Adding New Cascade Scenarios

When creating new cascade failure scenarios:

1. Ensure the scenario involves at least 3 interconnected components
2. Document the expected propagation path of the failure
3. Include specific symptoms that would be observed at each stage
4. Provide clear explanation of the primary root cause
5. Include sufficient diagnostic information to validate the analysis results 