import logging
from typing import Dict, Any, List, Optional

from .base import BaseTool, ToolContext, ToolResult, ToolExecutionError, ToolValidationError
from .kubectl import KubectlTool


class CheckPodStatusTool(BaseTool):
    """Tool to check the status of Kubernetes pods in a specific namespace."""

    @property
    def name(self) -> str:
        return "check_pod_status"

    @property
    def description(self) -> str:
        return (
            "Checks the status (Running, Pending, Failed, etc.) of pods \""
            "within a specified namespace. If no namespace is provided, \""
            "it defaults to the 'default' namespace."
        )

    @property
    def required_permissions(self) -> List[str]:
        # Needs permissions to list pods in the target namespace(s)
        return ["pods/list"] 

    @property
    def is_dangerous(self) -> bool:
        return False # Reads information only

    def _initialize(self) -> None:
        """Initialize logging and KubectlTool."""
        self.logger = logging.getLogger(f"k8s_analyzer.tools.{self.name}")
        self.kubectl = KubectlTool()
        self.logger.info(f"Initialized {self.name}")

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate parameters. Requires an optional 'namespace' string."""
        namespace = parameters.get('namespace')
        
        if namespace is not None and not isinstance(namespace, str):
            raise ToolValidationError('Invalid type for parameter "namespace": expected string.')
            
        if namespace == "": # Disallow empty string namespace
             raise ToolValidationError('Parameter "namespace" cannot be an empty string.')

        # Check for unexpected parameters
        allowed_params = {'namespace'}
        extra_params = set(parameters.keys()) - allowed_params
        if extra_params:
             raise ToolValidationError(f"Unexpected parameters for {self.name}: {extra_params}")
             
        self.logger.debug(f"Parameters validated for {self.name}: {parameters}")

    def _execute(self, context: ToolContext) -> Dict[str, Any]:
        """Execute the pod status check using kubectl."""
        namespace = context.parameters.get('namespace', 'default') # Default to 'default'
        self.logger.info(f"Executing {self.name} for namespace '{namespace}'")
        
        try:
            # Prepare kubectl arguments
            kubectl_args = {
                "command": "get",
                "resource": "pods",
                "namespace": namespace,
                "json_output": True
            }
            
            result_data = self.kubectl.execute(**kubectl_args)
            self.logger.info(f"{self.name} executed successfully for namespace '{namespace}'.")
            return result_data
        except Exception as e:
            self.logger.error(f"Error executing {self.name} for namespace '{namespace}': {e}", exc_info=True)
            raise ToolExecutionError(f"Failed to get pod status in namespace '{namespace}': {e}")

# --- Add other workload-related tools below --- 