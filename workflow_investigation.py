#!/usr/bin/env python3
"""
Run a Kubernetes Root Cause Analysis investigation with the LangGraph workflow.

This script uses the actual LangGraph workflow to perform investigations
rather than using mock data. It can be used as a drop-in replacement for
the run_investigation.py script but with the real multi-agent workflow.
"""

import sys
import os
import json
import argparse
import re
import logging
import datetime
from typing import Tuple, Dict, Any, List, Optional

# Import the workflow
from graph.workflow import run_investigation as run_workflow_investigation

# Import utilities for output generation
from run_live_cluster import (
    ensure_output_dirs, 
    format_summary, 
    generate_investigation_graph,
    generate_confidence_heatmap,
    generate_output_files
)

# Import symptom categories and templates
from run_investigation import (
    SYMPTOM_CATEGORIES,
    SYMPTOM_TEMPLATES,
    DEFAULT_VALUES,
    analyze_symptoms,
    get_symptom_preset
)

# Import interaction tracer
from utils.interaction import tracer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_investigation(symptoms: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Run a Kubernetes root cause analysis investigation using the LangGraph workflow
    
    Args:
        symptoms: Description of the symptoms or issues
        verbose: Whether to print verbose output
        
    Returns:
        Dict: Investigation results
    """
    logger.info(f"Starting LangGraph workflow investigation with symptoms: {symptoms}")
    
    if verbose:
        # Set logging to DEBUG level for verbose output
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Run the workflow-based investigation
    try:
        result = run_workflow_investigation(symptoms)
        logger.info("Workflow investigation completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during workflow investigation: {e}", exc_info=True)
        # Create a minimal result with the error information
        return {
            "investigation_phase": "error",
            "initial_symptoms": symptoms,
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }

def main():
    """Run a workflow-based investigation with symptoms provided via command line."""
    # Configure command-line argument parser
    parser = argparse.ArgumentParser(description="Kubernetes Root Cause Analysis with LangGraph Workflow")
    
    # Add supported arguments
    symptoms_group = parser.add_mutually_exclusive_group()
    symptoms_group.add_argument(
        "--symptoms", 
        type=str, 
        default=None,
        help="Custom symptoms to investigate. Use '-' to read from stdin."
    )
    symptoms_group.add_argument(
        "--preset", 
        type=str, 
        choices=list(SYMPTOM_CATEGORIES.keys()),
        help="Use a preset symptom category"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true", 
        help="Analyze symptoms using NLP to extract key details"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode with detailed logging"
    )
    parser.add_argument(
        "--help-extended", 
        action="store_true", 
        help="Show extended help with examples"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled")
    
    # Show extended help if requested
    if args.help_extended:
        print("\nKubernetes Root Cause Analysis - Extended Help")
        print("==============================================\n")
        print("This tool analyzes Kubernetes clusters for issues and recommends solutions.\n")
        
        print("Examples:")
        print("  # Run with preset symptom category:")
        print("  python workflow_investigation.py --preset pod-pending\n")
        
        print("  # Run with custom symptoms:")
        print("  python workflow_investigation.py --symptoms \"My pods are stuck in Pending state\"\n")
        
        print("  # Run with NLP analysis of symptoms:")
        print("  python workflow_investigation.py --symptoms \"Service unreachable in default namespace\" --analyze\n")
        
        print("  # Run with verbose output:")
        print("  python workflow_investigation.py --preset general-health --verbose\n")
        
        print("Available symptom presets:")
        for category in SYMPTOM_CATEGORIES.keys():
            print(f"  - {category}")
        
        print("\nOutput:")
        print("  Results are saved to output/investigations/ directory")
        print("  Visualizations are saved to output/visualizations/ directory")
        print("  Agent interactions are saved to output/logs/ directory")
        print("  Summary dashboard is available at output/index.html")
        
        sys.exit(0)
    
    # Check if symptoms are provided from stdin
    if args.symptoms == '-':
        args.symptoms = sys.stdin.read().strip()
    
    # Validate args - need either symptoms or preset
    if not args.symptoms and not args.preset:
        parser.print_help()
        print("\nError: Either --symptoms or --preset must be provided.")
        sys.exit(1)
    
    # Generate symptoms based on preset if provided
    if args.preset:
        symptoms = get_symptom_preset(args.preset)
        category = args.preset
    else:
        symptoms = args.symptoms
        
        # If analyze flag is set, use NLP to categorize and enhance the symptoms
        if args.analyze:
            print("\nAnalyzing your symptom description...\n")
            category, enhanced_symptoms = analyze_symptoms(symptoms)
            
            print(f"Your issue was categorized as: {category.upper()}")
            print(f"Enhanced description: {enhanced_symptoms}\n")
            
            # Ask user if they want to use the enhanced description
            if not args.verbose:  # In non-verbose mode, ask for confirmation
                use_enhanced = input("Use enhanced symptom description? (y/n): ").lower().strip()
                if use_enhanced == 'y' or use_enhanced == 'yes':
                    symptoms = enhanced_symptoms
        else:
            category = "custom"
    
    print(f"\nStarting workflow investigation with symptoms:\n{symptoms}\n")
    
    # Run the investigation
    try:
        result = run_investigation(symptoms, verbose=args.verbose or args.debug)
        
        # Add analysis category to result
        result['symptom_category'] = category
        
        # Generate output files
        output_files = generate_output_files(result)
        
        # Print summary
        print(f"\nInvestigation completed!")
        print(f"Symptom category: {category}")
        print(f"Summary saved to: {output_files['summary_path']}")
        print(f"JSON saved to: {output_files['json_path']}")
        print(f"Graph visualization: {output_files['graph_path']}")
        print(f"Heatmap visualization: {output_files['heatmap_path']}")
        print(f"Agent interaction logs: {tracer.log_file}")
        print("\nBrowse all investigations at: output/index.html")
        
    except Exception as e:
        logger.error(f"Error during investigation: {e}", exc_info=True)
        print(f"Error during investigation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 