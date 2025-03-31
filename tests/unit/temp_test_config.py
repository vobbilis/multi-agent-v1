"""Unit tests for configuration management."""

import os
import pytest
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

# Mock configuration classes for testing
@dataclass
class ToolConfig:
    """Configuration for tools."""
    timeout: int = 30
    kubectl_binary: str = "/usr/local/bin/kubectl"
    kubeconfig: str = "~/.kube/config"
    default_namespace: str = "default"
    allowed_namespaces: List[str] = field(default_factory=lambda: ["default", "kube-system"])
    restricted_resources: List[str] = field(default_factory=lambda: ["secrets", "configmaps"])
    dry_run: bool = False
    debug_mode: bool = False
    cache_ttl: int = 300
    max_retries: int = 3
    retry_delay: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolConfig':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class LLMConfig:
    """Configuration for language models."""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 60
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    cache_dir: str = "/tmp/llm-cache"
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class AgentConfig:
    """Configuration for agents."""
    max_iterations: int = 10
    timeout: int = 300
    cache_ttl: int = 3600
    debug_mode: bool = False
    interactive_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class AnalyzerConfig:
    """Configuration for analyzers."""
    environment: str = "production"
    log_level: str = "INFO"
    cache_dir: str = "/tmp/analyzer-cache"
    max_workers: int = 4
    timeout: int = 600
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyzerConfig':
        """Create instance from dictionary."""
        return cls(**data)


# Mock exceptions for testing
class ToolConfigError(Exception):
    """Error in tool configuration."""
    pass


class LLMConfigError(Exception):
    """Error in LLM configuration."""
    pass


class AgentConfigError(Exception):
    """Error in agent configuration."""
    pass


class AnalyzerConfigError(Exception):
    """Error in analyzer configuration."""
    pass


# Mock configuration functions
def get_tool_config() -> ToolConfig:
    """Get tool configuration from environment variables."""
    return ToolConfig(
        timeout=int(os.getenv("TOOL_TIMEOUT", "30")),
        kubectl_binary=os.getenv("KUBECTL_BINARY", "/usr/local/bin/kubectl"),
        kubeconfig=os.getenv("KUBECONFIG", "~/.kube/config"),
        default_namespace=os.getenv("DEFAULT_NAMESPACE", "default"),
        allowed_namespaces=os.getenv("ALLOWED_NAMESPACES", "default,kube-system").split(","),
        restricted_resources=os.getenv("RESTRICTED_RESOURCES", "secrets,configmaps").split(","),
        dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
        cache_ttl=int(os.getenv("CACHE_TTL", "300")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_delay=int(os.getenv("RETRY_DELAY", "5"))
    )


def validate_tool_config(config: ToolConfig) -> None:
    """Validate tool configuration."""
    if config.timeout <= 0:
        raise ToolConfigError("Tool timeout must be positive")
    
    if not config.kubectl_binary:
        raise ToolConfigError("kubectl binary path must be specified")
    
    if not config.kubeconfig:
        raise ToolConfigError("Kubeconfig path must be specified")
    
    if not config.default_namespace:
        raise ToolConfigError("Default namespace must be specified")
    
    if not config.allowed_namespaces:
        raise ToolConfigError("At least one allowed namespace must be specified")


def get_llm_config() -> LLMConfig:
    """Get LLM configuration from environment variables."""
    return LLMConfig(
        model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
        timeout=int(os.getenv("LLM_TIMEOUT", "60")),
        api_key=os.getenv("LLM_API_KEY", ""),
        api_base=os.getenv("LLM_API_BASE", "https://api.openai.com/v1"),
        cache_dir=os.getenv("LLM_CACHE_DIR", "/tmp/llm-cache"),
        debug_mode=os.getenv("LLM_DEBUG_MODE", "false").lower() == "true"
    )


def validate_llm_config(config: LLMConfig) -> None:
    """Validate LLM configuration."""
    if not config.model:
        raise LLMConfigError("Model name must be specified")
    
    if config.temperature < 0 or config.temperature > 1:
        raise LLMConfigError("Temperature must be between 0 and 1")
    
    if config.max_tokens <= 0:
        raise LLMConfigError("Max tokens must be positive")
    
    if config.timeout <= 0:
        raise LLMConfigError("Timeout must be positive")
    
    if not config.api_key:
        raise LLMConfigError("API key must be specified")
    
    if not config.api_base.startswith(("http://", "https://")):
        raise LLMConfigError("API base must be a valid URL")


def get_agent_config() -> AgentConfig:
    """Get agent configuration from environment variables."""
    return AgentConfig(
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        timeout=int(os.getenv("AGENT_TIMEOUT", "300")),
        cache_ttl=int(os.getenv("AGENT_CACHE_TTL", "3600")),
        debug_mode=os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true",
        interactive_mode=os.getenv("AGENT_INTERACTIVE_MODE", "false").lower() == "true"
    )


def validate_agent_config(config: AgentConfig) -> None:
    """Validate agent configuration."""
    if config.max_iterations <= 0:
        raise AgentConfigError("Max iterations must be positive")
    
    if config.timeout <= 0:
        raise AgentConfigError("Timeout must be positive")
    
    if config.cache_ttl <= 0:
        raise AgentConfigError("Cache TTL must be positive")


def get_analyzer_config() -> AnalyzerConfig:
    """Get analyzer configuration from environment variables."""
    environment = os.getenv("ANALYZER_ENVIRONMENT", "production")
    
    # Default log level based on environment
    default_log_level = "DEBUG" if environment != "production" else "INFO"
    debug_mode = environment != "production"
    
    return AnalyzerConfig(
        environment=environment,
        log_level=os.getenv("ANALYZER_LOG_LEVEL", default_log_level),
        cache_dir=os.getenv("ANALYZER_CACHE_DIR", "/tmp/analyzer-cache"),
        max_workers=int(os.getenv("ANALYZER_MAX_WORKERS", "4")),
        timeout=int(os.getenv("ANALYZER_TIMEOUT", "600")),
        debug_mode=os.getenv("ANALYZER_DEBUG_MODE", str(debug_mode).lower()).lower() == "true"
    )


def validate_analyzer_config(config: AnalyzerConfig) -> None:
    """Validate analyzer configuration."""
    valid_environments = ["development", "staging", "production", "test"]
    if not config.environment or config.environment not in valid_environments:
        raise AnalyzerConfigError(f"Environment must be one of: {', '.join(valid_environments)}")
    
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if not config.log_level or config.log_level not in valid_log_levels:
        raise AnalyzerConfigError(f"Log level must be one of: {', '.join(valid_log_levels)}")
    
    if not config.cache_dir:
        raise AnalyzerConfigError("Cache directory must be specified")
    
    if config.max_workers <= 0:
        raise AnalyzerConfigError("Max workers must be positive")
    
    if config.timeout <= 0:
        raise AnalyzerConfigError("Timeout must be positive")


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
        original_timeout = os.environ["TOOL_TIMEOUT"]
        original_binary = os.environ["KUBECTL_BINARY"]
        
        try:
            os.environ["TOOL_TIMEOUT"] = "60"
            os.environ["KUBECTL_BINARY"] = "/custom/kubectl"
            
            config = get_tool_config()
            assert config.timeout == 60
            assert config.kubectl_binary == "/custom/kubectl"
        finally:
            # Restore original values
            os.environ["TOOL_TIMEOUT"] = original_timeout
            os.environ["KUBECTL_BINARY"] = original_binary


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
    
    original_env = os.environ.get("ANALYZER_ENVIRONMENT")
    
    try:
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
    finally:
        # Restore original environment
        if original_env:
            os.environ["ANALYZER_ENVIRONMENT"] = original_env
        else:
            del os.environ["ANALYZER_ENVIRONMENT"]


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
        config_json = json.dumps(config_dict)
        assert json.loads(config_json)
        
        # Create from dict
        new_config = type(config).from_dict(config_dict)
        assert isinstance(new_config, type(config))
        assert new_config.to_dict() == config_dict 