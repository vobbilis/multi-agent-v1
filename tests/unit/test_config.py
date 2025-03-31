"""Unit tests for configuration management."""

import os
import pytest
from typing import Dict, Any
from k8s_analyzer.tools.config import (
    ToolConfig,
    get_tool_config,
    validate_tool_config
)
from k8s_analyzer.llm.config import (
    LLMConfig,
    get_llm_config,
    validate_llm_config
)
from k8s_analyzer.react.config import (
    AgentConfig,
    get_agent_config,
    validate_agent_config
)
from k8s_analyzer.core.config import (
    AnalyzerConfig,
    get_analyzer_config,
    validate_analyzer_config
)
from k8s_analyzer.tools.exceptions import ToolConfigError
from k8s_analyzer.llm.exceptions import LLMConfigError
from k8s_analyzer.react.exceptions import AgentConfigError
from k8s_analyzer.core.exceptions import AnalyzerConfigError

@pytest.fixture
def test_env():
    """Set up test environment variables."""
    original_env = {}
    test_vars = {
        # Tool configuration
        "TOOL_TIMEOUT": "30",
        "KUBECTL_BINARY": "/usr/local/bin/kubectl",
        "KUBECONFIG": "~/.kube/config",
        "DEFAULT_NAMESPACE": "default",
        "ALLOWED_NAMESPACES": "default,kube-system",
        "RESTRICTED_RESOURCES": "secrets,configmaps",
        "DRY_RUN": "true",
        "DEBUG_MODE": "true",
        "CACHE_TTL": "300",
        "MAX_RETRIES": "3",
        "RETRY_DELAY": "1",
        
        # LLM configuration
        "LLM_MODEL": "test-model",
        "LLM_TEMPERATURE": "0.7",
        "LLM_MAX_TOKENS": "1000",
        "LLM_TIMEOUT": "60",
        "LLM_API_KEY": "test-key",
        "LLM_API_BASE": "https://api.test.com",
        "LLM_CACHE_DIR": "/tmp/llm-cache",
        
        # Agent configuration
        "AGENT_MAX_ITERATIONS": "10",
        "AGENT_TIMEOUT": "300",
        "AGENT_CACHE_TTL": "3600",
        "AGENT_DEBUG_MODE": "true",
        "AGENT_INTERACTIVE_MODE": "true",
        
        # Analyzer configuration
        "ANALYZER_ENVIRONMENT": "test",
        "ANALYZER_LOG_LEVEL": "DEBUG",
        "ANALYZER_CACHE_DIR": "/tmp/analyzer-cache",
        "ANALYZER_MAX_WORKERS": "4",
        "ANALYZER_TIMEOUT": "600"
    }
    
    # Save original environment
    for key in test_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original environment
    for key in test_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]

class TestToolConfig:
    """Test cases for tool configuration."""
    
    def test_tool_config_loading(self, test_env):
        """TC8_001: Test tool config loading."""
        config = get_tool_config()
        
        assert isinstance(config, ToolConfig)
        assert config.timeout == 30
        assert config.kubectl_binary == "/usr/local/bin/kubectl"
        assert config.kubeconfig == "~/.kube/config"
        assert config.default_namespace == "default"
        assert "default" in config.allowed_namespaces
        assert "secrets" in config.restricted_resources
        assert config.dry_run is True
        assert config.debug_mode is True
    
    def test_tool_config_validation(self):
        """TC8_002: Test tool config validation."""
        # Valid config
        config = ToolConfig(
            timeout=30,
            kubectl_binary="/usr/local/bin/kubectl",
            kubeconfig="~/.kube/config",
            default_namespace="default",
            allowed_namespaces=["default"],
            restricted_resources=["secrets"],
            dry_run=True,
            debug_mode=True
        )
        validate_tool_config(config)  # Should not raise
        
        # Invalid config
        with pytest.raises(ToolConfigError):
            config = ToolConfig(
                timeout=-1,  # Invalid timeout
                kubectl_binary="",  # Invalid binary path
                kubeconfig="",  # Invalid kubeconfig
                default_namespace="",  # Invalid namespace
                allowed_namespaces=[],  # Invalid namespaces
                restricted_resources=[],
                dry_run=True,
                debug_mode=True
            )
            validate_tool_config(config)
    
    def test_tool_config_environment_override(self, test_env):
        """TC8_003: Test tool config environment override."""
        # Override with environment variables
        os.environ["TOOL_TIMEOUT"] = "60"
        os.environ["KUBECTL_BINARY"] = "/custom/kubectl"
        
        config = get_tool_config()
        assert config.timeout == 60
        assert config.kubectl_binary == "/custom/kubectl"

class TestLLMConfig:
    """Test cases for LLM configuration."""
    
    def test_llm_config_loading(self, test_env):
        """TC8_004: Test LLM config loading."""
        config = get_llm_config()
        
        assert isinstance(config, LLMConfig)
        assert config.model == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 60
        assert config.api_key == "test-key"
        assert config.api_base == "https://api.test.com"
    
    def test_llm_config_validation(self):
        """TC8_005: Test LLM config validation."""
        # Valid config
        config = LLMConfig(
            model="test-model",
            temperature=0.7,
            max_tokens=1000,
            timeout=60,
            api_key="test-key",
            api_base="https://api.test.com"
        )
        validate_llm_config(config)  # Should not raise
        
        # Invalid config
        with pytest.raises(LLMConfigError):
            config = LLMConfig(
                model="",  # Invalid model
                temperature=2.0,  # Invalid temperature
                max_tokens=-1,  # Invalid token count
                timeout=0,  # Invalid timeout
                api_key="",  # Invalid API key
                api_base="invalid-url"  # Invalid URL
            )
            validate_llm_config(config)

class TestAgentConfig:
    """Test cases for agent configuration."""
    
    def test_agent_config_loading(self, test_env):
        """TC8_006: Test agent config loading."""
        config = get_agent_config()
        
        assert isinstance(config, AgentConfig)
        assert config.max_iterations == 10
        assert config.timeout == 300
        assert config.cache_ttl == 3600
        assert config.debug_mode is True
        assert config.interactive_mode is True
    
    def test_agent_config_validation(self):
        """TC8_007: Test agent config validation."""
        # Valid config
        config = AgentConfig(
            max_iterations=10,
            timeout=300,
            cache_ttl=3600,
            debug_mode=True,
            interactive_mode=True
        )
        validate_agent_config(config)  # Should not raise
        
        # Invalid config
        with pytest.raises(AgentConfigError):
            config = AgentConfig(
                max_iterations=0,  # Invalid iterations
                timeout=-1,  # Invalid timeout
                cache_ttl=0,  # Invalid TTL
                debug_mode=True,
                interactive_mode=True
            )
            validate_agent_config(config)

class TestAnalyzerConfig:
    """Test cases for analyzer configuration."""
    
    def test_analyzer_config_loading(self, test_env):
        """TC8_008: Test analyzer config loading."""
        config = get_analyzer_config()
        
        assert isinstance(config, AnalyzerConfig)
        assert config.environment == "test"
        assert config.log_level == "DEBUG"
        assert config.cache_dir == "/tmp/analyzer-cache"
        assert config.max_workers == 4
        assert config.timeout == 600
    
    def test_analyzer_config_validation(self):
        """TC8_009: Test analyzer config validation."""
        # Valid config
        config = AnalyzerConfig(
            environment="test",
            log_level="DEBUG",
            cache_dir="/tmp/cache",
            max_workers=4,
            timeout=600
        )
        validate_analyzer_config(config)  # Should not raise
        
        # Invalid config
        with pytest.raises(AnalyzerConfigError):
            config = AnalyzerConfig(
                environment="",  # Invalid environment
                log_level="INVALID",  # Invalid log level
                cache_dir="",  # Invalid cache dir
                max_workers=0,  # Invalid workers
                timeout=-1  # Invalid timeout
            )
            validate_analyzer_config(config)

def test_config_environment_handling():
    """TC8_010: Test config environment handling."""
    environments = ["development", "staging", "production"]
    
    for env in environments:
        os.environ["ANALYZER_ENVIRONMENT"] = env
        config = get_analyzer_config()
        
        assert config.environment == env
        
        if env == "production":
            assert not config.debug_mode
            assert config.log_level == "INFO"
        else:
            assert config.debug_mode
            assert config.log_level == "DEBUG"

def test_config_serialization():
    """TC8_011: Test config serialization."""
    configs = [
        get_tool_config(),
        get_llm_config(),
        get_agent_config(),
        get_analyzer_config()
    ]
    
    for config in configs:
        # Convert to dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        
        # Convert to JSON
        import json
        config_json = json.dumps(config_dict)
        assert json.loads(config_json)
        
        # Create from dict
        new_config = type(config).from_dict(config_dict)
        assert new_config == config 