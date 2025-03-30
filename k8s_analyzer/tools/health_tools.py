import logging
from typing import Dict, Any, List

from .base import BaseTool, ToolContext, ToolResult, ToolExecutionError
from .kubectl import KubectlTool # Assuming KubectlTool might be useful or needed later


class CheckNodeStatusTool(BaseTool):
    """Tool to check the status of Kubernetes nodes."""

    @property
    def name(self) -> str:
        return "check_node_status"

    @property
    def description(self) -> str:
        return "Checks the status (Ready, NotReady, etc.) of all nodes in the Kubernetes cluster."

    @property
    def required_permissions(self) -> List[str]:
        return ["nodes/list"] # Example permission

    @property
    def is_dangerous(self) -> bool:
        return False # This tool only reads information

    def _initialize(self) -> None:
        """Initialize any resources if needed."""
        self.logger = logging.getLogger(f"k8s_analyzer.tools.{self.name}")
        self.kubectl = KubectlTool() # Instantiate KubectlTool helper
        self.logger.info(f"Initialized {self.name}")

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate parameters. This tool takes no parameters."""
        if parameters:
             raise ValueError(f"{self.name} does not accept any parameters.")
        self.logger.debug(f"Parameters validated for {self.name}")
        # Add more specific validation if parameters are introduced later

    def _execute(self, context: ToolContext) -> Dict[str, Any]:
        """Execute the node status check using kubectl."""
        self.logger.info(f"Executing {self.name}")
        try:
            # Use the instantiated KubectlTool
            result_data = self.kubectl.execute(command="get", resource="nodes", json_output=True)
            self.logger.info(f"{self.name} executed successfully.")
            return result_data # Return the dictionary output from kubectl
        except Exception as e:
            self.logger.error(f"Error executing {self.name}: {e}", exc_info=True)
            # Re-raise as ToolExecutionError for the base class handler
            raise ToolExecutionError(f"Failed to get node status: {e}")


class CheckClusterEventsTool(BaseTool):
    """Tool to fetch recent cluster-wide events."""

    @property
    def name(self) -> str:
        return "check_cluster_events"

    @property
    def description(self) -> str:
        return "Retrieves recent cluster-wide events, which can indicate issues or warnings."

    @property
    def required_permissions(self) -> List[str]:
        return ["events/list"] # Example permission

    @property
    def is_dangerous(self) -> bool:
        return False # This tool only reads information

    def _initialize(self) -> None:
        """Initialize any resources if needed."""
        self.logger = logging.getLogger(f"k8s_analyzer.tools.{self.name}")
        self.kubectl = KubectlTool() # Instantiate KubectlTool helper
        self.logger.info(f"Initialized {self.name}")

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate parameters. This tool takes no parameters."""
        if parameters:
             raise ValueError(f"{self.name} does not accept any parameters.")
        self.logger.debug(f"Parameters validated for {self.name}")

    def _execute(self, context: ToolContext) -> Dict[str, Any]:
        """Execute the cluster events check using kubectl."""
        self.logger.info(f"Executing {self.name}")
        try:
            # Use the instantiated KubectlTool
            # Consider fetching events across all namespaces or limiting scope/time
            result_data = self.kubectl.execute(command="get", resource="events", all_namespaces=True, json_output=True)
            self.logger.info(f"{self.name} executed successfully.")
            return result_data # Return the dictionary output
        except Exception as e:
            self.logger.error(f"Error executing {self.name}: {e}", exc_info=True)
            raise ToolExecutionError(f"Failed to get cluster events: {e}")

# --- Add more specific tool classes below as needed --- 