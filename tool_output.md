# Kubernetes Analyzer Tool Output Structure

Below is a comprehensive example of the JSON structure that should be returned by the analyzer:

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "main_response": "Analysis of the Kubernetes cluster reveals several critical areas requiring attention. The cluster is running 92 pods across 12 namespaces, with 85% of pods in Running state. There are 3 pods in CrashLoopBackOff state in the bank-of-anthos namespace, and 2 pods showing ImagePullBackOff errors in the otel-demo namespace.",
    "actions": [
        {
            "priority": "HIGH",
            "component": "bank-of-anthos/ledger-db-6db96d49f9-x8d4r",
            "description": "Pod is in CrashLoopBackOff state with repeated container restarts",
            "command": "kubectl logs -n bank-of-anthos ledger-db-6db96d49f9-x8d4r --previous"
        },
        {
            "priority": "HIGH",
            "component": "otel-demo/frontend-85d9b88d56-j2xkp",
            "description": "ImagePullBackOff error due to invalid image reference",
            "command": "kubectl describe pod -n otel-demo frontend-85d9b88d56-j2xkp"
        },
        {
            "priority": "MEDIUM",
            "component": "monitoring/prometheus-server",
            "description": "Pod showing high memory usage (85% of limit)",
            "command": "kubectl top pod -n monitoring prometheus-server"
        }
    ],
    "next_steps": [
        {
            "id": 1,
            "category": "INVESTIGATE",
            "description": "Analyze container logs for bank-of-anthos/ledger-db pod to identify crash cause",
            "rationale": "Multiple container restarts indicate application-level issues that need investigation"
        },
        {
            "id": 2,
            "category": "OPTIMIZE",
            "description": "Review and adjust resource limits for monitoring namespace pods",
            "rationale": "Several pods are approaching resource limits which could affect stability"
        },
        {
            "id": 3,
            "category": "MONITOR",
            "description": "Set up alerts for pods in ImagePullBackOff state",
            "rationale": "Early detection of image pull issues can prevent service disruptions"
        }
    ],
    "error": null,
    "metadata": {
        "cluster_stats": {
            "total_nodes": 3,
            "total_pods": 92,
            "namespaces": 12,
            "pod_status": {
                "Running": 85,
                "CrashLoopBackOff": 3,
                "ImagePullBackOff": 2,
                "Pending": 2
            }
        },
        "analysis_timestamp": "2024-03-21T06:45:30Z",
        "analyzed_components": [
            "cluster_health",
            "workload_status",
            "resource_utilization"
        ]
    }
}
```

## Field Descriptions

### Top Level Fields
- `session_id`: Unique identifier for the analysis session
- `main_response`: Primary analysis summary in human-readable format
- `actions`: List of immediate actions that should be taken
- `next_steps`: List of recommended follow-up actions
- `error`: Error message if any, null otherwise
- `metadata`: Additional context about the analysis

### Action Fields
- `priority`: HIGH, MEDIUM, or LOW
- `component`: Affected component in format namespace/resource-name
- `description`: Clear description of the issue
- `command`: Suggested kubectl command to investigate (optional)

### Next Step Fields
- `id`: Unique identifier for the step
- `category`: INVESTIGATE, MONITOR, or OPTIMIZE
- `description`: Description of the suggested action
- `rationale`: Explanation of why this step is important

### Metadata Fields
- `cluster_stats`: Overall cluster statistics
- `analysis_timestamp`: When the analysis was performed
- `analyzed_components`: List of components that were analyzed

## Usage Notes

1. All actions are ordered by priority (HIGH → MEDIUM → LOW)
2. Next steps are ordered by logical sequence of investigation
3. Commands are provided where direct investigation is possible
4. The metadata section provides context for the entire analysis 