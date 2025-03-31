"""Configuration settings for K8s Analyzer tools."""

import os
from typing import Dict, Any

# Tool Registry Configuration
TOOL_REGISTRY_CACHE_TTL: int = int(os.getenv("TOOL_REGISTRY_CACHE_TTL", "300"))  # seconds
TOOL_REGISTRY_REFRESH_ON_ERROR: bool = os.getenv("TOOL_REGISTRY_REFRESH_ON_ERROR", "true").lower() == "true"

# Tool Execution Configuration
TOOL_EXECUTION_TIMEOUT: int = int(os.getenv("TOOL_EXECUTION_TIMEOUT", "60"))  # seconds
TOOL_MAX_RETRIES: int = int(os.getenv("TOOL_MAX_RETRIES", "3"))
TOOL_RETRY_DELAY: int = int(os.getenv("TOOL_RETRY_DELAY", "5"))  # seconds
TOOL_DRY_RUN_DEFAULT: bool = os.getenv("TOOL_DRY_RUN_DEFAULT", "false").lower() == "true"

# Kubectl Tool Configuration
KUBECTL_PATH: str = os.getenv("KUBECTL_PATH", "kubectl")
KUBECTL_CONTEXT: str = os.getenv("KUBECTL_CONTEXT", "kind-orchestrator")
KUBECTL_NAMESPACE: str = os.getenv("KUBECTL_NAMESPACE", "default")
KUBECTL_TIMEOUT: int = int(os.getenv("KUBECTL_TIMEOUT", "30"))  # seconds
KUBECTL_MAX_LINES: int = int(os.getenv("KUBECTL_MAX_LINES", "1000"))

# Resource Limits
TOOL_MEMORY_LIMIT: int = int(os.getenv("TOOL_MEMORY_LIMIT", "512"))  # MB
TOOL_CPU_LIMIT: float = float(os.getenv("TOOL_CPU_LIMIT", "1.0"))  # cores

# Security Configuration
TOOL_ALLOWED_NAMESPACES: list[str] = os.getenv("TOOL_ALLOWED_NAMESPACES", "default").split(",")
TOOL_RESTRICTED_RESOURCES: list[str] = os.getenv("TOOL_RESTRICTED_RESOURCES", "secrets,nodes").split(",")
TOOL_REQUIRE_TLS: bool = os.getenv("TOOL_REQUIRE_TLS", "true").lower() == "true"

# Environment-specific Configuration
TOOL_ENVIRONMENT: str = os.getenv("TOOL_ENVIRONMENT", "production")
TOOL_ENV_CONFIGS: Dict[str, Dict[str, Any]] = {
    "development": {
        "dry_run": True,
        "debug_logging": True,
        "timeout_multiplier": 2.0,
        "retry_count": 5
    },
    "staging": {
        "dry_run": False,
        "debug_logging": True,
        "timeout_multiplier": 1.5,
        "retry_count": 3
    },
    "production": {
        "dry_run": False,
        "debug_logging": False,
        "timeout_multiplier": 1.0,
        "retry_count": 3
    }
}

def get_environment_config() -> Dict[str, Any]:
    """Get configuration for current environment."""
    return TOOL_ENV_CONFIGS.get(TOOL_ENVIRONMENT, TOOL_ENV_CONFIGS["production"])

def validate_config() -> None:
    """
    Validate the configuration settings.
    
    Raises:
        ValueError: If configuration is invalid
    """
    if TOOL_ENVIRONMENT not in TOOL_ENV_CONFIGS:
        raise ValueError(f"Invalid TOOL_ENVIRONMENT: {TOOL_ENVIRONMENT}")
        
    if not KUBECTL_PATH:
        raise ValueError("KUBECTL_PATH must be set")
        
    if TOOL_MAX_RETRIES < 0:
        raise ValueError("TOOL_MAX_RETRIES must be non-negative")
        
    if TOOL_RETRY_DELAY < 0:
        raise ValueError("TOOL_RETRY_DELAY must be non-negative")
        
    if TOOL_MEMORY_LIMIT < 64:
        raise ValueError("TOOL_MEMORY_LIMIT must be at least 64MB")
        
    if TOOL_CPU_LIMIT <= 0:
        raise ValueError("TOOL_CPU_LIMIT must be positive")
