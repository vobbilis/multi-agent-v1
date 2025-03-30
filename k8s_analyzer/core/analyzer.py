import logging
import json
import subprocess
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from ..llm.openai import OpenAILLM
from ..llm.gemini import GeminiLLM
from ..react.agent import ReActAgent
from ..tools.kubectl import KubectlTool
from .config import LLM_PROVIDER, LLM_MODEL
from .exceptions import LLMConfigError, AnalyzerError
from ..tools import ToolRegistry, BaseTool, ToolRegistryError
# Import the new concrete tools
from ..tools.health_tools import CheckNodeStatusTool, CheckClusterEventsTool
from ..tools.workload_tools import CheckPodStatusTool
# (Add imports for other concrete tools as they are created)

console = Console()

@dataclass
class PressurePoint:
    """Represents a resource pressure point in the cluster."""
    resource_name: str
    resource_type: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    
    @property
    def pressure_ratio(self) -> float:
        """Calculate the pressure ratio."""
        return self.current_value / self.threshold if self.threshold > 0 else 1.0
    
    def __str__(self) -> str:
        return f"{self.resource_name} ({self.resource_type}) - {self.metric_name}: {self.current_value}/{self.threshold} ({self.severity})"


@dataclass
class AnalysisResult:
    """Results of a cluster analysis."""
    success: bool = True
    answer: str = ""
    error: str = ""
    pressure_points: List[PressurePoint] = None
    critical_points: List[str] = None
    metadata: Dict[str, Any] = None
    context: Dict[str, Any] = None
    interactions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.pressure_points is None:
            self.pressure_points = []
        if self.critical_points is None:
            self.critical_points = []
        if self.metadata is None:
            self.metadata = {}
        if self.context is None:
            self.context = {}
        if self.interactions is None:
            self.interactions = []


class EnhancedClusterAnalyzer:
    """
    Enhanced Kubernetes cluster analyzer that uses LLMs with ReAct and HITL capabilities.
    """
    
    def __init__(self, agent=None, tools=None, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        """
        Initialize the analyzer with specified components.
        
        Args:
            agent: ReAct agent for analysis (optional, will be created if not provided)
            tools: List of tools to use (optional, will be created if not provided)
            llm_provider: Override for LLM provider (openai/gemini)
            llm_model: Override for model name
        """
        self.logger = logging.getLogger("k8s_analyzer.enhanced")
        self.logger.info("Initializing EnhancedClusterAnalyzer")
        
        if agent:
            self.agent = agent
        else:
            # Initialize ReAct agent
            # Determine LLM class based on provider
            llm_provider = llm_provider or LLM_PROVIDER
            if llm_provider == 'openai':
                LLMClass = OpenAILLM
            elif llm_provider == 'gemini':
                 LLMClass = GeminiLLM
            else:
                 raise LLMConfigError(f"Unsupported LLM provider: {llm_provider}")
            
            llm_instance = LLMClass(model=(llm_model or LLM_MODEL))
            
            # Create a new ToolRegistry for this agent instance
            tool_registry = ToolRegistry()
            
            # Register the tool classes with the new registry
            self.logger.info("Registering default tools with new agent registry...")
            successfully_registered_names = []
            # --- Use the UPDATED DEFAULT_TOOL_CLASSES --- 
            for name, tool_class in DEFAULT_TOOL_CLASSES.items():
                try:
                    # Pre-check inheritance
                    if not issubclass(tool_class, BaseTool):
                         raise TypeError(f"Tool class {tool_class.__name__} must inherit from BaseTool")
                         
                    # Attempt registration
                    tool_registry.register_tool(name=name, tool_class=tool_class)
                    self.logger.debug(f"Successfully registered tool: {name}")
                    successfully_registered_names.append(name)
                except TypeError as e:
                     # Catch inheritance errors specifically
                     self.logger.error(f"Registration Error for '{name}': {e}")
                except ToolRegistryError as e:
                     # Catch specific registry errors (like already registered)
                     self.logger.warning(f"Skipping registration for '{name}': {e}")
                     # If it was already registered, consider it successful for logging purposes
                     if "already registered" in str(e):
                          successfully_registered_names.append(name)
                except Exception as e:
                     # Catch any other unexpected errors during registration/init
                     self.logger.error(f"Failed to register/initialize tool '{name}': {e}", exc_info=True)

            # Initialize the agent with the populated registry
            self.agent = ReActAgent(
                 llm=llm_instance,
                 tools=tool_registry # Pass the populated registry
            )

        # Update logging for clarity using the tracked names
        if successfully_registered_names:
             self.logger.info(f"Analyzer agent configured with tools: {successfully_registered_names}")
        else:
             self.logger.warning("Agent initialized, but no tools were successfully registered.")

        self.logger.info("Initialization complete")
    
    def analyze_question(self, question: str, context: Optional[Dict[str, Any]] = None, log_dir: str = "logs") -> AnalysisResult:
        """
        Analyze a user question about the cluster.
        
        Args:
            question: The user's question
            context: Optional context information
            log_dir: Directory to store execution logs (defaults to 'logs')
            
        Returns:
            AnalysisResult containing the analysis
        """
        self.logger.info(f"Analyzing question: {question}")
        
        if not question:
            return AnalysisResult(
                success=False,
                error="Invalid question: Question cannot be empty"
            )
        
        try:
            # Reset agent if it's a React agent
            if hasattr(self.agent, 'reset_state'):
                self.agent.reset_state()
            elif hasattr(self.agent, 'reset'):
                self.agent.reset()
            
            # Handle context information
            analysis_context = context or {}
            
            # Prepare arguments for the agent call, including log_dir
            call_args = {
                "question": question,
                "context": analysis_context,
                "log_dir": log_dir # Pass log_dir here
            }
            
            # Use agent's analyze method or analyze_question based on what's available
            if hasattr(self.agent, 'analyze_question'): # Prefer analyze_question if available
                 raw_result = self.agent.analyze_question(**call_args)
            elif hasattr(self.agent, 'analyze'):
                 # If analyze doesn't accept log_dir, remove it from call_args or adjust analyze
                 # Assuming analyze_question is the target method based on previous work
                 # If analyze is the only method, this might need adjustment
                 # For now, assuming analyze_question exists and takes log_dir
                 del call_args['log_dir'] # Example: Remove if analyze doesn't take it
                 raw_result = self.agent.analyze(question, context=analysis_context)
            else:
                return AnalysisResult(
                    success=False,
                    error="Agent doesn't have analyze or analyze_question method"
                )
            
            # Convert raw result to AnalysisResult
            if isinstance(raw_result, dict):
                return AnalysisResult(
                    success=raw_result.get('success', True),
                    answer=raw_result.get('answer', ''),
                    error=raw_result.get('error', ''),
                    metadata=raw_result.get('metadata', {}),
                    context=analysis_context
                )
            elif isinstance(raw_result, AnalysisResult):
                return raw_result
            else:
                return AnalysisResult(
                    success=True,
                    answer=str(raw_result),
                    context=analysis_context
                )
        except Exception as e:
            self.logger.error(f"Error during question analysis: {str(e)}", exc_info=True)
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {str(e)}",
                context=context
            )
    
    def analyze_pressure_points(self) -> AnalysisResult:
        """
        Analyze resource pressure points in the cluster.
        
        Returns:
            AnalysisResult containing the pressure points
        """
        self.logger.info("Analyzing cluster pressure points")
        
        try:
            # Get kubectl tool
            kubectl_tool = None
            for tool in self.tools:
                if getattr(tool, 'name', '') == 'kubectl':
                    kubectl_tool = tool
                    break
            
            if not kubectl_tool:
                return AnalysisResult(
                    success=False,
                    error="Kubectl tool not found in analyzer tools"
                )
            
            # Get pod metrics
            metrics_result = kubectl_tool.execute(command="top", resource="pods", all_namespaces=True)
            
            pressure_points = []
            
            # Process the metrics data
            if 'items' in metrics_result:
                for pod in metrics_result['items']:
                    metadata = pod.get('metadata', {})
                    usage = pod.get('usage', {})
                    limits = pod.get('limits', {})
                    
                    # Check CPU pressure
                    if 'cpu' in usage and 'cpu' in limits:
                        cpu_usage = self._parse_cpu_value(usage['cpu'])
                        cpu_limit = self._parse_cpu_value(limits['cpu'])
                        
                        if cpu_usage > 0.8 * cpu_limit:
                            pressure_points.append(PressurePoint(
                                resource_name=metadata.get('name', 'unknown'),
                                resource_type='Pod',
                                metric_name='cpu',
                                current_value=cpu_usage,
                                threshold=cpu_limit,
                                severity='warning' if cpu_usage < cpu_limit else 'critical'
                            ))
                    
                    # Check Memory pressure
                    if 'memory' in usage and 'memory' in limits:
                        mem_usage = self._parse_memory_value(usage['memory'])
                        mem_limit = self._parse_memory_value(limits['memory'])
                        
                        if mem_usage > 0.8 * mem_limit:
                            pressure_points.append(PressurePoint(
                                resource_name=metadata.get('name', 'unknown'),
                                resource_type='Pod',
                                metric_name='memory',
                                current_value=mem_usage,
                                threshold=mem_limit,
                                severity='warning' if mem_usage < mem_limit else 'critical'
                            ))
            
            return AnalysisResult(
                success=True,
                pressure_points=pressure_points
            )
        except Exception as e:
            self.logger.error(f"Error during pressure point analysis: {str(e)}", exc_info=True)
            return AnalysisResult(
                success=False,
                error=f"Pressure point analysis failed: {str(e)}"
            )
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """Parse CPU value from a string (e.g., '200m') to a float."""
        try:
            if cpu_str.endswith('m'):
                return float(cpu_str[:-1])
            else:
                return float(cpu_str) * 1000
        except (ValueError, TypeError):
            return 0
    
    def _parse_memory_value(self, mem_str: str) -> float:
        """Parse memory value from a string (e.g., '100Mi') to a float."""
        try:
            # Remove the unit suffix
            if mem_str.endswith('Ki'):
                return float(mem_str[:-2]) * 1024
            elif mem_str.endswith('Mi'):
                return float(mem_str[:-2]) * 1024 * 1024
            elif mem_str.endswith('Gi'):
                return float(mem_str[:-2]) * 1024 * 1024 * 1024
            else:
                return float(mem_str)
        except (ValueError, TypeError):
            return 0
    
    def run_interactive_mode(self) -> AnalysisResult:
        """
        Run the analyzer in interactive mode.
        
        Returns:
            AnalysisResult containing the interactions
        """
        self.logger.info("Starting interactive mode")
        console.print("\n[bold blue]Enhanced Kubernetes Cluster Analyzer (ReAct Mode)[/bold blue]")
        console.print("=" * 60)
        console.print("Type 'exit' or 'quit' to end the session\n")
        
        interactions = []
        success = True
        error = ""
        
        try:
            while True:
                try:
                    question = input("[bold green]Ask about your cluster: > [/bold green]").strip()
                    if question.lower() in ['exit', 'quit']:
                        console.print("\n[bold yellow]Exiting...[/bold yellow]")
                        break
                    if not question:
                        continue
                    
                    console.print("\n[bold blue]Starting ReAct analysis loop...[/bold blue]")
                    result = self.analyze_question(question)
                    
                    interactions.append({
                        "question": question,
                        "result": result
                    })
                    
                    if not result.success:
                        console.print(f"\n[bold red]ERROR in ReAct loop: {result.error}[/bold red]")
                    else:
                        self._display_result(result)
                        
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]Exiting...[/bold yellow]")
                    break
                except Exception as e:
                    self.logger.error(f"Unhandled exception in interactive mode: {e}", exc_info=True)
                    console.print(f"\n[bold red]An unexpected error occurred: {str(e)}[/bold red]")
                    error = str(e)
                    success = False
            
            return AnalysisResult(
                success=success,
                error=error,
                interactions=interactions
            )
        except Exception as e:
            self.logger.error(f"Error in interactive mode: {str(e)}", exc_info=True)
            return AnalysisResult(
                success=False,
                error=f"Interactive mode failed: {str(e)}",
                interactions=interactions
            )
    
    def analyze_resource(self, resource_type: str) -> AnalysisResult:
        """
        Analyze a specific resource type.
        
        Args:
            resource_type: The resource type to analyze (pods, nodes, services, etc.)
            
        Returns:
            AnalysisResult containing the analysis
        """
        self.logger.info(f"Analyzing resource type: {resource_type}")
        
        try:
            # Get kubectl tool
            kubectl_tool = None
            for tool in self.tools:
                if getattr(tool, 'name', '') == 'kubectl':
                    kubectl_tool = tool
                    break
            
            if not kubectl_tool:
                return AnalysisResult(
                    success=False,
                    error="Kubectl tool not found in analyzer tools"
                )
            
            # Get the resources
            resources = kubectl_tool.execute(command="get", resource=resource_type, all_namespaces=True)
            
            return AnalysisResult(
                success=True,
                answer=f"Analysis of {resource_type} completed",
                metadata={"resources": resources}
            )
        except Exception as e:
            self.logger.error(f"Error analyzing resource type {resource_type}: {str(e)}", exc_info=True)
            return AnalysisResult(
                success=False,
                error=f"Resource analysis failed: {str(e)}"
            )
    
    def aggregate_results(self, results: List[AnalysisResult]) -> AnalysisResult:
        """
        Aggregate multiple analysis results.
        
        Args:
            results: List of AnalysisResult objects to aggregate
            
        Returns:
            AnalysisResult containing the aggregated results
        """
        self.logger.info(f"Aggregating {len(results)} analysis results")
        
        try:
            # Start with a success result
            aggregated = AnalysisResult(success=True)
            
            # Combine data from all results
            for result in results:
                # If any result failed, the aggregated result is failed
                if not result.success:
                    aggregated.success = False
                    aggregated.error += f"{result.error}; "
                
                # Combine answers
                if result.answer:
                    aggregated.answer += f"{result.answer}\n"
                
                # Combine pressure points
                aggregated.pressure_points.extend(result.pressure_points)
                
                # Combine critical points
                aggregated.critical_points.extend(result.critical_points)
                
                # Merge metadata
                if result.metadata:
                    aggregated.metadata.update(result.metadata)
            
            # Clean up the combined error message
            if aggregated.error:
                aggregated.error = aggregated.error.rstrip("; ")
            
            return aggregated
        except Exception as e:
            self.logger.error(f"Error aggregating results: {str(e)}", exc_info=True)
            return AnalysisResult(
                success=False,
                error=f"Results aggregation failed: {str(e)}"
            )
    
    def _display_result(self, result: AnalysisResult):
        """Display the analysis result."""
        console.print("\n[bold green]--- Analysis Result ---[/bold green]")
        
        # Display answer
        if result.answer:
            console.print(Panel(result.answer, title="[bold]Answer[/bold]", border_style="green"))
        else:
            console.print("[yellow]No answer provided.[/yellow]")
        
        # Display pressure points if any
        if result.pressure_points:
            pressure_table = Table(title="[bold]Resource Pressure Points[/bold]", border_style="red")
            pressure_table.add_column("Resource", style="cyan")
            pressure_table.add_column("Type", style="blue")
            pressure_table.add_column("Metric", style="magenta")
            pressure_table.add_column("Value", style="yellow")
            pressure_table.add_column("Threshold", style="yellow")
            pressure_table.add_column("Severity", style="red")
            
            for point in result.pressure_points:
                pressure_table.add_row(
                    point.resource_name,
                    point.resource_type,
                    point.metric_name,
                    str(point.current_value),
                    str(point.threshold),
                    point.severity
                )
            console.print(pressure_table)
        
        # Display metadata if any
        if result.metadata:
            console.print("\n[bold cyan]--- Metadata ---[/bold cyan]")
            for key, value in result.metadata.items():
                if isinstance(value, dict) or isinstance(value, list):
                    console.print(f"[cyan]{key}:[/cyan] {json.dumps(value, indent=2)}")
                else:
                    console.print(f"[cyan]{key}:[/cyan] {value}")
    
    def _display_final_answer(self, result: Dict[str, Any]):
        """Display the final analysis result from the ReAct agent."""
        console.print("\n[bold_green]--- Final Analysis ---[/bold_green]")
        
        # Display main response
        if result.get("main_response"):
            console.print(Panel(result["main_response"], title="[bold]Final Answer[/bold]", border_style="green"))
        else:
            console.print("[yellow]No final answer provided by the agent.[/yellow]")
        
        # Display recommended next steps
        if result.get("next_steps"):
            next_table = Table(title="[bold]Recommended Next Steps[/bold]", title_style="", border_style="blue")
            next_table.add_column("Description", style="cyan")
            next_table.add_column("Rationale", style="magenta")
            
            for step in result["next_steps"]:
                next_table.add_row(
                    str(step.get("description", "N/A")),
                    str(step.get("rationale", "N/A"))
                )
            if next_table.rows:
                console.print(next_table)
        
        # Display relevant metadata if included
        if result.get("metadata"):
            metadata = result["metadata"]
            if metadata.get("cluster_stats") or metadata.get("analyzed_components"):
                console.print("\n[bold cyan]--- Analysis Metadata ---[/bold cyan]")
                if metadata.get("analyzed_components"):
                    console.print(f"[cyan]Analyzed Components:[/cyan] {', '.join(metadata['analyzed_components'])}")

# --- Define UPDATED Default Tool Classes HERE ---
DEFAULT_TOOL_CLASSES = {
    "kubectl": KubectlTool, # Keep the general kubectl tool if needed elsewhere
    "check_node_status": CheckNodeStatusTool,
    "check_pod_status": CheckPodStatusTool,
    "check_cluster_events": CheckClusterEventsTool,
    # --- Add other CONCRETE tools here as they are created ---
    # e.g., "get_deployments": GetDeploymentsTool, 
}
# --- End Default Tool Classes Definition --- 