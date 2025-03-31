# API Reference

This document provides a comprehensive reference for the Multi-Agent Root Cause Analysis System API. It includes endpoint details, request/response formats, authentication, and usage examples.

## API Overview

The API Gateway provides a RESTful interface to interact with the Root Cause Analysis system:

- Base URL: `https://<host>:<port>/api/v1`
- Content Type: `application/json`
- Authentication: JWT, OAuth2, or API Key

## Authentication

### JWT Authentication

```bash
curl -X GET https://rca-api.example.com/api/v1/incidents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### OAuth2 Authentication

```bash
# Step 1: Obtain an access token
curl -X POST https://auth.example.com/oauth2/token \
  -d "grant_type=client_credentials&client_id=CLIENT_ID&client_secret=CLIENT_SECRET"

# Step 2: Use the access token
curl -X GET https://rca-api.example.com/api/v1/incidents \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

### API Key Authentication

```bash
curl -X GET https://rca-api.example.com/api/v1/incidents \
  -H "X-API-Key: your-api-key"
```

## Endpoints

### Incidents

#### List Incidents

```
GET /incidents
```

Query Parameters:
- `status` (string, optional): Filter by incident status (open, closed, in_progress)
- `severity` (string, optional): Filter by severity (critical, high, medium, low)
- `since` (ISO8601 date, optional): Return incidents after this date
- `limit` (integer, optional): Maximum number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

Response:
```json
{
  "incidents": [
    {
      "id": "incident-123",
      "title": "Pod OOM Killed in production-api",
      "status": "open",
      "severity": "high",
      "created_at": "2023-06-15T12:00:00Z",
      "updated_at": "2023-06-15T12:30:00Z",
      "affected_components": ["production-api", "database"],
      "source": "kubernetes_events",
      "analysis_status": "in_progress"
    },
    ...
  ],
  "total": 120,
  "limit": 50,
  "offset": 0
}
```

#### Get Incident Details

```
GET /incidents/{incident_id}
```

Response:
```json
{
  "id": "incident-123",
  "title": "Pod OOM Killed in production-api",
  "description": "Multiple pods from production-api deployment were terminated due to OOM",
  "status": "open",
  "severity": "high",
  "created_at": "2023-06-15T12:00:00Z",
  "updated_at": "2023-06-15T12:30:00Z",
  "affected_components": ["production-api", "database"],
  "source": "kubernetes_events",
  "analysis_status": "completed",
  "analysis_id": "analysis-456",
  "timeline": [
    {
      "timestamp": "2023-06-15T11:55:00Z",
      "event": "Database connection pool reached maximum capacity",
      "source": "logs",
      "component": "database"
    },
    {
      "timestamp": "2023-06-15T11:58:00Z",
      "event": "Memory usage in production-api pod exceeded 90%",
      "source": "metrics",
      "component": "production-api"
    },
    {
      "timestamp": "2023-06-15T12:00:00Z",
      "event": "Pod OOM Killed",
      "source": "kubernetes_events",
      "component": "production-api"
    }
  ]
}
```

#### Create Incident

```
POST /incidents
```

Request:
```json
{
  "title": "High Latency in Payment Service",
  "description": "Users reporting payment processing delays exceeding 10 seconds",
  "severity": "high",
  "affected_components": ["payment-service", "transaction-api"],
  "source": "user_report"
}
```

Response:
```json
{
  "id": "incident-124",
  "title": "High Latency in Payment Service",
  "description": "Users reporting payment processing delays exceeding 10 seconds",
  "status": "open",
  "severity": "high",
  "created_at": "2023-06-15T14:00:00Z",
  "updated_at": "2023-06-15T14:00:00Z",
  "affected_components": ["payment-service", "transaction-api"],
  "source": "user_report",
  "analysis_status": "pending"
}
```

#### Update Incident

```
PATCH /incidents/{incident_id}
```

Request:
```json
{
  "status": "in_progress",
  "severity": "critical",
  "description": "Updated description with new information about the issue"
}
```

Response:
```json
{
  "id": "incident-123",
  "title": "Pod OOM Killed in production-api",
  "description": "Updated description with new information about the issue",
  "status": "in_progress",
  "severity": "critical",
  "created_at": "2023-06-15T12:00:00Z",
  "updated_at": "2023-06-15T14:15:00Z",
  "affected_components": ["production-api", "database"],
  "source": "kubernetes_events",
  "analysis_status": "in_progress"
}
```

### Analysis

#### Get Analysis Results

```
GET /analysis/{analysis_id}
```

Response:
```json
{
  "id": "analysis-456",
  "incident_id": "incident-123",
  "status": "completed",
  "created_at": "2023-06-15T12:05:00Z",
  "updated_at": "2023-06-15T12:15:00Z",
  "findings": [
    {
      "agent": "logs_agent",
      "confidence": 0.85,
      "description": "Found connection pool exhaustion errors in database logs",
      "evidence": [
        {
          "source": "logs",
          "component": "database",
          "message": "Connection pool reached maximum capacity (100 connections)",
          "timestamp": "2023-06-15T11:55:00Z"
        }
      ]
    },
    {
      "agent": "resources_agent",
      "confidence": 0.92,
      "description": "Memory usage in production-api spiked to 95% before OOM event",
      "evidence": [
        {
          "source": "metrics",
          "component": "production-api",
          "data": {
            "memory_usage_bytes": 1572864000,
            "memory_limit_bytes": 1610612736
          },
          "timestamp": "2023-06-15T11:58:00Z"
        }
      ]
    }
  ],
  "root_causes": [
    {
      "confidence": 0.88,
      "description": "Database connection pool exhaustion leading to connection queuing in production-api",
      "contributing_factors": [
        "High request volume exceeding connection pool capacity",
        "Connections not being properly released back to pool",
        "No circuit breaker implemented for database connectivity"
      ]
    },
    {
      "confidence": 0.65,
      "description": "Memory leak in production-api process",
      "contributing_factors": [
        "Memory usage gradually increasing over time",
        "No memory limit graceful handling"
      ]
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "description": "Increase database connection pool size",
      "implementation": "Update the production-api deployment to set DB_POOL_SIZE=150"
    },
    {
      "priority": "high",
      "description": "Implement connection release monitoring",
      "implementation": "Add connection tracking to identify unreleased connections"
    },
    {
      "priority": "medium",
      "description": "Implement circuit breaker for database connections",
      "implementation": "Add resilience4j circuit breaker to the database client"
    },
    {
      "priority": "medium",
      "description": "Increase memory limit for production-api pods",
      "implementation": "Update memory limit to 2Gi in deployment manifest"
    }
  ]
}
```

#### Request New Analysis

```
POST /analysis
```

Request:
```json
{
  "incident_id": "incident-124",
  "time_range": {
    "start": "2023-06-15T13:45:00Z",
    "end": "2023-06-15T14:15:00Z"
  },
  "focus_components": ["payment-service", "transaction-api"],
  "priority": "high"
}
```

Response:
```json
{
  "id": "analysis-457",
  "incident_id": "incident-124",
  "status": "in_progress",
  "created_at": "2023-06-15T14:20:00Z",
  "updated_at": "2023-06-15T14:20:00Z",
  "estimated_completion": "2023-06-15T14:25:00Z"
}
```

### Agent Data

#### Get Agent Status

```
GET /agents
```

Response:
```json
{
  "agents": [
    {
      "id": "logs_agent",
      "status": "active",
      "version": "1.2.0",
      "last_heartbeat": "2023-06-15T14:19:55Z",
      "data_sources": ["elasticsearch", "loki"],
      "active_tasks": 2
    },
    {
      "id": "events_agent",
      "status": "active",
      "version": "1.1.5",
      "last_heartbeat": "2023-06-15T14:19:58Z",
      "data_sources": ["kubernetes_events"],
      "active_tasks": 1
    },
    {
      "id": "resources_agent",
      "status": "active",
      "version": "1.3.1",
      "last_heartbeat": "2023-06-15T14:19:52Z",
      "data_sources": ["prometheus", "metrics_server"],
      "active_tasks": 3
    }
  ]
}
```

#### Get Agent Findings

```
GET /agents/{agent_id}/findings
```

Query Parameters:
- `incident_id` (string, optional): Filter findings by incident
- `since` (ISO8601 date, optional): Return findings after this date
- `limit` (integer, optional): Maximum number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

Response:
```json
{
  "findings": [
    {
      "id": "finding-789",
      "agent_id": "logs_agent",
      "incident_id": "incident-123",
      "timestamp": "2023-06-15T12:08:23Z",
      "confidence": 0.85,
      "description": "Found connection pool exhaustion errors in database logs",
      "evidence": [
        {
          "source": "logs",
          "component": "database",
          "message": "Connection pool reached maximum capacity (100 connections)",
          "timestamp": "2023-06-15T11:55:00Z"
        }
      ]
    },
    ...
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### Knowledge Base

#### Query Knowledge Base

```
GET /knowledge
```

Query Parameters:
- `query` (string, required): Search query
- `categories` (array, optional): Filter by categories (incidents, patterns, solutions)
- `limit` (integer, optional): Maximum number of results (default: 20)
- `offset` (integer, optional): Pagination offset (default: 0)

Response:
```json
{
  "results": [
    {
      "type": "pattern",
      "id": "pattern-345",
      "title": "Database Connection Pool Exhaustion",
      "description": "Pattern of connection pool exhaustion leading to application OOM",
      "symptoms": [
        "Connection pool capacity warnings in database logs",
        "Increasing memory usage in dependent services",
        "Eventual OOM termination of pods"
      ],
      "related_incidents": ["incident-123", "incident-098"]
    },
    {
      "type": "solution",
      "id": "solution-567",
      "title": "Managing Database Connection Pools",
      "description": "Best practices for sizing and managing database connection pools",
      "steps": [
        "Size pool based on max concurrent users × average connections per user",
        "Implement connection timeouts to prevent leaks",
        "Add monitoring for pool utilization",
        "Implement circuit breakers for database connections"
      ],
      "references": [
        {
          "title": "Database Connection Pool Best Practices",
          "url": "https://example.com/db-pool-practices"
        }
      ]
    },
    ...
  ],
  "total": 8,
  "limit": 20,
  "offset": 0
}
```

### System Configuration

#### Get Configuration

```
GET /config
```

Response:
```json
{
  "version": "1.5.2",
  "components": {
    "orchestrator": {
      "enabled": true,
      "version": "1.5.2",
      "max_concurrent_incidents": 10,
      "default_timeout": 300
    },
    "agents": {
      "logs_agent": {
        "enabled": true,
        "version": "1.2.0",
        "data_sources": ["elasticsearch", "loki"],
        "elasticsearch_indexes": ["kubernetes-*"]
      },
      "events_agent": {
        "enabled": true,
        "version": "1.1.5",
        "data_sources": ["kubernetes_events"],
        "namespaces": ["default", "production", "staging"]
      },
      "resources_agent": {
        "enabled": true,
        "version": "1.3.1",
        "data_sources": ["prometheus", "metrics_server"],
        "metrics_retention": "7d"
      }
    },
    "analysis_engine": {
      "enabled": true,
      "version": "1.4.0",
      "confidence_threshold": 0.6,
      "max_analysis_time": 300,
      "max_root_causes": 3
    }
  },
  "global": {
    "log_level": "info",
    "telemetry_enabled": true,
    "environment": "production"
  }
}
```

#### Update Configuration

```
PATCH /config
```

Request:
```json
{
  "components": {
    "logs_agent": {
      "elasticsearch_indexes": ["kubernetes-*", "application-*"]
    },
    "analysis_engine": {
      "confidence_threshold": 0.7
    }
  },
  "global": {
    "log_level": "debug"
  }
}
```

Response:
```json
{
  "message": "Configuration updated successfully",
  "changes": [
    "components.logs_agent.elasticsearch_indexes",
    "components.analysis_engine.confidence_threshold",
    "global.log_level"
  ],
  "requires_restart": ["logs_agent"]
}
```

## Webhooks

### Register Webhook

```
POST /webhooks
```

Request:
```json
{
  "url": "https://your-service.example.com/rca-notifications",
  "events": ["incident.created", "incident.updated", "analysis.completed"],
  "secret": "your-webhook-secret"
}
```

Response:
```json
{
  "id": "webhook-123",
  "url": "https://your-service.example.com/rca-notifications",
  "events": ["incident.created", "incident.updated", "analysis.completed"],
  "created_at": "2023-06-15T15:00:00Z",
  "status": "active"
}
```

### Webhook Payload Example

When an incident is created:

```json
{
  "id": "webhook-event-456",
  "timestamp": "2023-06-15T15:05:00Z",
  "event": "incident.created",
  "payload": {
    "incident": {
      "id": "incident-125",
      "title": "API Gateway 5xx Errors Spike",
      "status": "open",
      "severity": "high",
      "created_at": "2023-06-15T15:05:00Z"
    }
  }
}
```

## Error Responses

### Error Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "severity",
        "message": "severity must be one of: critical, high, medium, low"
      }
    ]
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `authentication_required` | 401 | Authentication credentials missing |
| `invalid_credentials` | 401 | Invalid authentication credentials |
| `permission_denied` | 403 | User lacks permission for the action |
| `not_found` | 404 | Resource not found |
| `invalid_request` | 400 | Invalid request parameters |
| `conflict` | 409 | Request conflicts with current state |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Internal server error |

## Rate Limits

The API implements rate limiting to protect the service:

| Endpoint | Rate Limit |
|----------|------------|
| `/incidents` (GET) | 120 requests per minute |
| `/incidents` (POST) | 30 requests per minute |
| `/analysis` (POST) | 10 requests per minute |
| `/knowledge` (GET) | 60 requests per minute |
| Other endpoints | 60 requests per minute |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 115
X-RateLimit-Reset: 1623766800
```

## API Versioning

The API uses URL versioning (e.g., `/api/v1/incidents`). When a new, incompatible API version is released, the previous version will be maintained for at least 6 months with a deprecation notice.

## SDK Libraries

The API is supported by official client libraries for common languages:

- Python: [rca-client-python](https://github.com/example/rca-client-python)
- Go: [rca-client-go](https://github.com/example/rca-client-go)
- JavaScript: [rca-client-js](https://github.com/example/rca-client-js)

Example usage (Python):

```python
from rca_client import RCAClient

client = RCAClient(
    base_url="https://rca-api.example.com/api/v1",
    api_key="your-api-key"
)

# List open incidents
incidents = client.list_incidents(status="open", limit=10)
for incident in incidents:
    print(f"{incident.id}: {incident.title} - {incident.severity}")

# Get analysis for an incident
analysis = client.get_analysis("analysis-456")
for root_cause in analysis.root_causes:
    print(f"Root cause ({root_cause.confidence}): {root_cause.description}")
```

## Related Resources

- [System Architecture](../architecture/system_overview.md)
- [Deployment Guide](../deployment/deployment_guide.md)
- [Security Guide](../deployment/security.md)
- [API Changelog](api_changelog.md) 