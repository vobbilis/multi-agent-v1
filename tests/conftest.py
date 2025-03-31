"""Pytest configuration and shared fixtures."""

import os
import pytest
import logging
from typing import Dict, Any
from pathlib import Path
from unittest.mock import MagicMock

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test environment configuration
TEST_ENV = {
    "KUBECONFIG": "~/.kube/config",
    "KUBECTL_BINARY": "/usr/local/bin/kubectl",
    "DEFAULT_NAMESPACE": "default",
    "ALLOWED_NAMESPACES": "default,kube-system",
    "RESTRICTED_RESOURCES": "secrets,configmaps",
    "TOOL_TIMEOUT": "30",
    "DRY_RUN": "true",
    "DEBUG_MODE": "true",
    "CACHE_TTL": "300",
    "MAX_RETRIES": "3",
    "RETRY_DELAY": "1"
}

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    original_env = {}
    for key, value in TEST_ENV.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key in TEST_ENV:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for command execution."""
    return MagicMock(
        returncode=0,
        stdout=b'{"items": []}',
        stderr=b""
    )

@pytest.fixture
def test_data_dir():
    """Get the test data directory path."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_pod_list():
    """Sample pod list data for testing."""
    return {
        "items": [
            {
                "metadata": {
                    "name": "test-pod",
                    "namespace": "default",
                    "uid": "123",
                    "labels": {"app": "test"}
                },
                "spec": {
                    "containers": [
                        {
                            "name": "test-container",
                            "image": "test:latest",
                            "resources": {
                                "requests": {
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                },
                                "limits": {
                                    "cpu": "200m",
                                    "memory": "256Mi"
                                }
                            }
                        }
                    ]
                },
                "status": {
                    "phase": "Running",
                    "conditions": [
                        {
                            "type": "Ready",
                            "status": "True"
                        }
                    ]
                }
            }
        ]
    }

@pytest.fixture
def sample_node_list():
    """Sample node list data for testing."""
    return {
        "items": [
            {
                "metadata": {
                    "name": "test-node",
                    "uid": "456"
                },
                "status": {
                    "capacity": {
                        "cpu": "4",
                        "memory": "8Gi",
                        "pods": "110"
                    },
                    "allocatable": {
                        "cpu": "3800m",
                        "memory": "7Gi",
                        "pods": "100"
                    },
                    "conditions": [
                        {
                            "type": "Ready",
                            "status": "True"
                        }
                    ]
                }
            }
        ]
    }

@pytest.fixture
def sample_metrics():
    """Sample metrics data for testing."""
    return {
        "pods": [
            {
                "metadata": {
                    "name": "test-pod",
                    "namespace": "default"
                },
                "containers": [
                    {
                        "name": "test-container",
                        "usage": {
                            "cpu": "50m",
                            "memory": "64Mi"
                        }
                    }
                ]
            }
        ],
        "nodes": [
            {
                "metadata": {
                    "name": "test-node"
                },
                "usage": {
                    "cpu": "1000m",
                    "memory": "4Gi"
                }
            }
        ]
    }

@pytest.fixture
def mock_tool_context():
    """Mock tool context for testing."""
    return {
        "session_id": "test-session",
        "parameters": {
            "command": "get",
            "resource": "pods",
            "namespace": "default"
        },
        "environment": "test",
        "timeout": 30,
        "dry_run": True,
        "metadata": {
            "test": "value"
        }
    }

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "thought": "Analyzing cluster state",
        "action": {
            "tool": "kubectl",
            "parameters": {
                "command": "get",
                "resource": "pods",
                "namespace": "default",
                "output": "json"
            }
        },
        "observation": "Retrieved pod information",
        "final_answer": "Analysis complete"
    }

@pytest.fixture
def mock_tool_result():
    """Mock tool execution result for testing."""
    return {
        "success": True,
        "data": {"items": []},
        "error": None,
        "execution_time": 0.5,
        "metadata": {
            "tool": "test_tool",
            "environment": "test"
        }
    }

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "dangerous: mark test as potentially dangerous"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    if not config.getoption("--run-dangerous"):
        skip_dangerous = pytest.mark.skip(reason="need --run-dangerous option to run")
        for item in items:
            if "dangerous" in item.keywords:
                item.add_marker(skip_dangerous)

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--run-dangerous",
        action="store_true",
        default=False,
        help="run potentially dangerous tests"
    ) 