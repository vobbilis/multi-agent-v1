"""Base interface and utilities for K8s Analyzer tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic, Union
from dataclasses import dataclass, field
import logging
import subprocess
import shlex # Use shlex for safer command parsing
from datetime import datetime

from ..core.exceptions import ToolExecutionError
from .exceptions import (
    ToolError,
    ToolConfigError,
    ToolValidationError,
    ToolTimeoutError,
    ToolPermissionError
)
from .result import ToolResult

T = TypeVar('T')  # Type variable for tool-specific configurations

@dataclass
class ToolContext:
    """Context for tool execution."""
    session_id: str
    parameters: Dict[str, Any]
    environment: str
    timeout: Optional[float] = None
    dry_run: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTool(Generic[T], ABC):
    """Base class for all K8s Analyzer tools."""
    
    def __init__(self, config: Optional[T] = None, **kwargs):
        """
        Initialize the tool.
        
        Args:
            config: Optional tool-specific configuration
            **kwargs: Additional configuration parameters from environment
        """
        self.logger = logging.getLogger(f"k8s_analyzer.tools.{self.__class__.__name__.lower()}")
        self._config = config
        self._dry_run = kwargs.get('dry_run', False)
        self._debug_logging = kwargs.get('debug_logging', False)
        self._timeout_multiplier = kwargs.get('timeout_multiplier', 1.0)
        self._retry_count = kwargs.get('retry_count', 3)
        self._initialize()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the tool."""
        pass
    
    @property
    @abstractmethod
    def required_permissions(self) -> List[str]:
        """List of required permissions/roles to use this tool."""
        pass
    
    @property
    @abstractmethod
    def is_dangerous(self) -> bool:
        """Whether this tool can make dangerous changes."""
        pass
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize tool-specific resources and validate configuration."""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate parameters before execution.
        
        Args:
            parameters: Parameters to validate
            
        Raises:
            ToolValidationError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    def _execute(self, context: ToolContext) -> Dict[str, Any]:
        """
        Internal execution method to be implemented by tools.
        
        Args:
            context: Execution context
            
        Returns:
            Dict containing execution results
            
        Raises:
            ToolExecutionError: If execution fails
        """
        pass
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with provided parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult containing execution results
            
        Raises:
            ToolError: If execution fails
        """
        start_time = datetime.now()
        
        try:
            # Validate parameters
            self.validate_parameters(kwargs)
            
            # Create execution context
            context = ToolContext(
                session_id=kwargs.pop("session_id", str(start_time.timestamp())),
                parameters=kwargs,
                environment=kwargs.pop("environment", "production"),
                timeout=kwargs.pop("timeout", None),
                dry_run=kwargs.pop("dry_run", False),
                metadata=kwargs.pop("metadata", {})
            )
            
            # Check permissions
            self._check_permissions()
            
            # Execute with timeout if specified
            if context.timeout:
                # TODO: Implement timeout mechanism
                pass
            
            result = self._execute(context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                success=True,
                data=result,
                error=None,
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={
                    "tool": self.name,
                    "environment": context.environment,
                    "dry_run": context.dry_run,
                    **context.metadata
                }
            )
            
        except ToolValidationError as e:
            self.logger.error(f"Validation error: {e}")
            return self._create_error_result(str(e), start_time)
            
        except ToolExecutionError as e:
            self.logger.error(f"Execution error: {e}")
            return self._create_error_result(str(e), start_time)
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._create_error_result(f"Unexpected error: {e}", start_time)
    
    def _check_permissions(self) -> None:
        """
        Check if required permissions are available.
        
        Raises:
            ToolValidationError: If permissions are insufficient
        """
        # TODO: Implement permission checking
        pass
    
    def _create_error_result(self, error: str, start_time: datetime) -> ToolResult:
        """Create a ToolResult for an error case."""
        return ToolResult(
            success=False,
            data=None,
            error=error,
            execution_time=(datetime.now() - start_time).total_seconds(),
            timestamp=datetime.now(),
            metadata={"tool": self.name}
        )
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.name}: {self.description}"

    def _run_kubectl(self, command: str) -> Dict[str, Any]:
        """
        Execute a kubectl command safely using subprocess.
        
        Args:
            command: The kubectl command string to execute (e.g., "get pods -n default").
            
        Returns:
            Dict containing command 'output' (stdout+stderr) or 'error'.
        """
        full_command = f"kubectl {command}"
        self.logger.info(f"Executing command: {full_command}")
        try:
            # Use shlex.split for safer parsing, especially with quotes
            cmd_parts = shlex.split(full_command)

            # Basic validation: Ensure it starts with 'kubectl'
            if not cmd_parts or cmd_parts[0] != 'kubectl':
                 raise ValueError("Invalid command format. Must start with 'kubectl'.")

            # Execute the command
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=60  # Add a timeout for safety
            )

            output = result.stdout
            error_output = result.stderr

            if result.returncode != 0:
                self.logger.error(f"Command failed with return code {result.returncode}")
                self.logger.error(f"Stderr: {error_output}")
                # Combine stdout and stderr in case of error for more context
                return {"error": f"Command failed: {error_output}\nOutput: {output}"}
            else:
                self.logger.debug(f"Command successful. Output:\n{output}")
                return {"output": output} # Return only stdout on success

        except subprocess.TimeoutExpired:
             self.logger.error(f"Command timed out: {full_command}")
             raise ToolExecutionError(f"Command '{full_command}' timed out after 60 seconds.")
        except FileNotFoundError:
            self.logger.error("'kubectl' command not found. Is it installed and in PATH?")
            raise ToolExecutionError("'kubectl' command not found. Please ensure it is installed and in your system's PATH.")
        except Exception as e:
            self.logger.error(f"Failed to execute kubectl command '{full_command}': {e}", exc_info=True)
            raise ToolExecutionError(f"Failed to execute kubectl command: {e}")
