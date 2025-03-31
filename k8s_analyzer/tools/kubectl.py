"""Kubectl tool implementation for K8s Analyzer."""

import subprocess
import shlex
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .base import BaseTool, ToolContext
from .exceptions import (
    ToolExecutionError,
    ToolValidationError,
    ToolPermissionError
)
from .config import (
    KUBECTL_PATH,
    KUBECTL_CONTEXT,
    KUBECTL_NAMESPACE,
    KUBECTL_TIMEOUT,
    KUBECTL_MAX_LINES,
    TOOL_ALLOWED_NAMESPACES,
    TOOL_RESTRICTED_RESOURCES
)
from .result import ToolResult

@dataclass
class KubectlConfig:
    """Configuration for kubectl tool."""
    context: str = KUBECTL_CONTEXT
    namespace: str = KUBECTL_NAMESPACE
    timeout: int = KUBECTL_TIMEOUT
    max_lines: int = KUBECTL_MAX_LINES
    path: str = KUBECTL_PATH

class KubectlTool(BaseTool[KubectlConfig]):
    """Tool for executing kubectl commands."""
    
    @property
    def name(self) -> str:
        return "kubectl"
    
    @property
    def description(self) -> str:
        return "Execute kubectl commands to interact with Kubernetes cluster"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["get", "list", "watch"]  # Basic read permissions by default
    
    @property
    def is_dangerous(self) -> bool:
        return False  # Base kubectl tool is read-only
    
    def _initialize(self) -> None:
        """Initialize kubectl configuration."""
        self._config = self._config or KubectlConfig()
        
        # Verify kubectl is available
        try:
            version = subprocess.run(
                [self._config.path, "version", "--client", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if version.returncode != 0:
                raise ToolExecutionError(f"kubectl not available: {version.stderr}")
            self.logger.info("Kubectl tool initialized successfully")
        except subprocess.TimeoutExpired:
            raise ToolExecutionError("Timeout checking kubectl version")
        except Exception as e:
            raise ToolExecutionError(f"Failed to initialize kubectl: {e}")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate kubectl command parameters."""
        if "command" not in parameters:
            raise ToolValidationError("Command parameter is required")
            
        command = parameters["command"]
        if not isinstance(command, str):
            raise ToolValidationError("Command must be a string")
            
        # Parse command to validate
        try:
            parts = shlex.split(command)
        except Exception as e:
            raise ToolValidationError(f"Invalid command format: {e}")
            
        if not parts:
            raise ToolValidationError("Empty command")
            
        # Check for dangerous operations
        dangerous_verbs = ["delete", "exec", "edit", "patch", "replace", "scale"]
        if any(verb in parts for verb in dangerous_verbs):
            raise ToolValidationError(
                f"Command contains dangerous operations: {command}"
            )
            
        # Validate namespace if specified
        if "-n" in parts or "--namespace" in parts:
            try:
                ns_index = parts.index("-n" if "-n" in parts else "--namespace")
                namespace = parts[ns_index + 1]
                if namespace not in TOOL_ALLOWED_NAMESPACES:
                    raise ToolValidationError(
                        f"Namespace {namespace} not in allowed namespaces: {TOOL_ALLOWED_NAMESPACES}"
                    )
            except IndexError:
                raise ToolValidationError("Namespace flag without value")
                
        # Check for restricted resources
        for resource in TOOL_RESTRICTED_RESOURCES:
            if resource in parts:
                raise ToolValidationError(
                    f"Access to resource {resource} is restricted"
                )
    
    def _execute(self, context: ToolContext) -> ToolResult:
        """Execute kubectl command."""
        command = context.parameters.get("command")
        resource = context.parameters.get("resource")
        namespace = context.parameters.get("namespace", self._config.namespace)
        output_format = context.parameters.get("output", "json")
        json_output = output_format.lower() == "json"
        
        # Build full command with context and namespace
        cmd_parts = [self._config.path]
        
        if self._config.context:
            cmd_parts.extend(["--context", self._config.context])
            
        if namespace:
            cmd_parts.extend(["-n", namespace])
            
        # Add the command and resource
        if command:
            cmd_parts.append(command)
        if resource:
            cmd_parts.append(resource)

        # Add output format based on the json_output flag
        # This should override any -o/-output in other parameters below
        if json_output:
            cmd_parts.extend(["-o", "json"])
        elif output_format and output_format != "json": # Handle other explicit formats if needed
            cmd_parts.extend(["-o", output_format])

        # Add any other parameters (flags, options)
        # Ensure we don't re-add handled params or the flag derived from 'output'/'json_output'
        handled_params = {"command", "resource", "namespace", "output", "json_output"}
        for key, value in context.parameters.items():
            if key not in handled_params:
                # Handle boolean flags (like --all-namespaces)
                if isinstance(value, bool) and value:
                    cmd_parts.append(f"--{key}")
                # Handle key-value options (like --field-selector)
                elif not isinstance(value, bool) and value is not None:
                     # Basic quoting for safety, might need refinement
                     quoted_value = shlex.quote(str(value))
                     cmd_parts.append(f"--{key}={quoted_value}")

        # Log the command for debugging
        full_cmd = " ".join(cmd_parts)
        self.logger.debug(f"Executing kubectl command: {full_cmd}")
        
        # Execute command
        try:
            start_time = datetime.now()
            process = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self._config.timeout
            )
            execution_time = (datetime.now() - start_time).total_seconds()

            # Check return code for errors
            if process.returncode != 0:
                error_output = process.stderr.strip() if process.stderr else process.stdout.strip()
                error_msg = f"kubectl command failed with exit code {process.returncode}: {error_output}"
                self.logger.error(f"Kubectl error for command '{full_cmd}': {error_msg}")
                # Raise ToolExecutionError for the agent to handle
                raise ToolExecutionError(error_msg)

            # Parse JSON output if requested
            output = process.stdout.strip()
            if json_output and output:
                try:
                    data = json.loads(output)
                except json.JSONDecodeError as json_err:
                    # Log the problematic output before raising
                    self.logger.error(f"Failed to parse kubectl JSON output for command '{full_cmd}'. Error: {json_err}. Output:\n{output[:500]}...")
                    raise ToolExecutionError(f"Failed to parse kubectl output as JSON: {json_err}")
            else:
                data = output

            return ToolResult(
                success=True,
                data=data,
                error=None,
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={"tool": "kubectl", "command": full_cmd}
            )

        except subprocess.TimeoutExpired:
            execution_time = self._config.timeout
            error_msg = f"kubectl command timed out after {self._config.timeout} seconds"
            self.logger.error(f"Timeout error for command '{full_cmd}': {error_msg}")
            raise ToolExecutionError(error_msg)

        except ToolExecutionError as tee: # Re-raise specific execution errors
             raise tee
        except Exception as e:
            # Catch any other unexpected exceptions during execution/parsing
            execution_time = (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0
            error_msg = f"Unexpected error executing kubectl command '{full_cmd}': {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ToolExecutionError(error_msg)
    
    def check_permissions(self, verbs: Optional[List[str]] = None) -> bool:
        """
        Check if current user has required permissions.
        
        Args:
            verbs: Optional list of verbs to check
            
        Returns:
            True if all permissions are available
            
        Raises:
            ToolPermissionError: If permission check fails
        """
        verbs = verbs or self.required_permissions
        
        try:
            cmd_parts = [
                self._config.path,
                "auth",
                "can-i",
                "--list",
                "-o",
                "json"
            ]
            
            if self._config.context:
                cmd_parts.extend(["--context", self._config.context])
                
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self._config.timeout
            )
            
            if result.returncode != 0:
                raise ToolPermissionError(
                    f"Failed to check permissions: {result.stderr}"
                )
                
            permissions = json.loads(result.stdout)
            
            # Check if all required verbs are allowed
            for verb in verbs:
                if not any(
                    rule.get("verbs", []).get(verb, False)
                    for rule in permissions.get("rules", [])
                ):
                    return False
                    
            return True
            
        except Exception as e:
            raise ToolPermissionError(f"Error checking permissions: {e}")
            
    def get_available_resources(self) -> List[str]:
        """
        Get list of available API resources.
        
        Returns:
            List of resource names
            
        Raises:
            ToolExecutionError: If resource list fails
        """
        try:
            cmd_parts = [
                self._config.path,
                "api-resources",
                "-o",
                "json"
            ]
            
            if self._config.context:
                cmd_parts.extend(["--context", self._config.context])
                
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self._config.timeout
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    f"Failed to get API resources: {result.stderr}"
                )
                
            resources = json.loads(result.stdout)
            return [
                resource["name"]
                for resource in resources.get("resources", [])
            ]
            
        except Exception as e:
            raise ToolExecutionError(f"Error getting API resources: {e}")
            
    def get_current_context(self) -> str:
        """
        Get current kubectl context.
        
        Returns:
            Current context name
            
        Raises:
            ToolExecutionError: If context check fails
        """
        try:
            result = subprocess.run(
                [self._config.path, "config", "current-context"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    f"Failed to get current context: {result.stderr}"
                )
                
            return result.stdout.strip()
            
        except Exception as e:
            raise ToolExecutionError(f"Error getting current context: {e}") 