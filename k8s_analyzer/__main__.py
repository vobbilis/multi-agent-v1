import sys
import argparse
import logging
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .core.config import LOG_FORMAT, LOG_FILE
from .core.analyzer import EnhancedClusterAnalyzer, AnalysisResult
from .react.exceptions import ReActAbortError
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

console = Console()

def main():
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description='Enhanced Kubernetes Cluster Analyzer')
    parser.add_argument('-q', '--question', type=str,
                       help='Question to analyze (if not provided, runs in interactive mode)')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('-f', '--format', type=str, choices=['full', 'simple', 'json'],
                       default='full', help='Output format (full, simple, or json)')
    parser.add_argument('--log-dir', type=str, default='logs',
                       help='Directory to store execution logs')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Ensure log directory exists
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)
    
    try:
        if len(sys.argv) == 1 or not args.question:
            # No question provided, run in interactive mode
            try:
                analyzer = EnhancedClusterAnalyzer(
                    llm_provider=os.getenv("LLM_PROVIDER", None),
                    llm_model=os.getenv("LLM_MODEL", None)
                )
                analyzer.run_interactive_mode()
            except Exception as e:
                console.print(f"\n[bold red]Fatal error: {str(e)}[/bold red]")
                return 1
        else:
            # Question provided, run in analysis mode
            analyzer = EnhancedClusterAnalyzer(
                llm_provider=os.getenv("LLM_PROVIDER", None),
                llm_model=os.getenv("LLM_MODEL", None)
            )
            
            try:
                console.print("\n[bold blue]Analyzing question...[/bold blue]")
                context = {
                    "initial_namespace": os.getenv("KUBECTL_NAMESPACE", "default")
                }
                result = analyzer.analyze_question(args.question, context=context, log_dir=args.log_dir)
                
                if result.error:
                    console.print(f"\n[bold red]Error: {result.error}[/bold red]")
                    return 1
                else:
                    # If using simple format, display minimal output
                    if args.format == 'simple':
                        if result.success:
                            console.print(result.answer or "Analysis complete, no specific answer generated.")
                        else:
                            console.print(f"Error: {result.error}")
                    # If using JSON format, output JSON
                    elif args.format == 'json':
                        try:
                            result_dict = {
                                "success": result.success,
                                "answer": result.answer,
                                "error": result.error,
                                "pressure_points": [p.to_dict() for p in result.pressure_points] if result.pressure_points else [],
                                "critical_points": [p.to_dict() for p in result.critical_points] if result.critical_points else [],
                                "metadata": result.metadata,
                                "context": result.context,
                                "interactions": result.interactions
                            }
                            console.print(json.dumps(result_dict, indent=2))
                        except TypeError as e:
                            console.print(json.dumps({"success": False, "error": f"Result serialization failed: {e}"}, indent=2))
                    # Otherwise use the full rich display
                    else:
                        display_analysis_result(result, console)
                    
                    # Print location of execution log if it exists
                    if hasattr(result, 'metadata') and result.metadata.get('log_file'):
                        console.print(f"\n[bold cyan]Detailed execution log saved to: {result.metadata['log_file']}[/bold cyan]")
                    else:
                        # Try to find the log file based on session ID if possible
                        session_id = result.metadata.get('session_id')
                        if session_id:
                            log_file_path = os.path.join(args.log_dir, f"react_execution_{session_id}.log")
                            if os.path.exists(log_file_path):
                                console.print(f"\n[bold cyan]Detailed execution log saved to: {log_file_path}[/bold cyan]")
                    
                    return 0
            except ReActAbortError:
                console.print("\n[bold yellow]Analysis aborted by user[/bold yellow]")
                return 0
                
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {str(e)}[/bold red]")
        return 1
    
    return 0

def display_analysis_result(result: AnalysisResult, console: Console):
    """Display the AnalysisResult object using Rich components."""
    console.print("\n[bold green]--- Analysis Result ---[/bold green]")

    if result.success:
        if result.answer:
            console.print(Panel(result.answer, title="[bold]Answer[/bold]", border_style="green"))
        else:
            console.print("[yellow]Analysis successful, but no specific answer provided.[/yellow]")
    else:
        console.print(Panel(result.error or "Unknown error", title="[bold red]Error[/bold red]", border_style="red"))

    if result.pressure_points:
        pass
    if result.critical_points:
        pass
    if result.interactions:
        pass
    if result.metadata:
        pass

if __name__ == "__main__":
    sys.exit(main()) 