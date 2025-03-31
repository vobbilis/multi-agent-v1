"""
Main entry point for Kubernetes Root Cause Analysis Engine
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the workflow
from graph.workflow import run_investigation
from utils.visualizations import generate_investigation_graph
from bin.run_investigation import analyze_symptoms, get_symptom_preset, SYMPTOM_CATEGORIES

def setup_langsmith():
    """Set up LangSmith for tracing and debugging"""
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY")
    if not langsmith_api_key:
        logger.warning("LANGSMITH_API_KEY not set. Tracing will be disabled.")
        return False
    
    # Set project name
    os.environ["LANGCHAIN_PROJECT"] = os.environ.get(
        "LANGCHAIN_PROJECT", "kubernetes-root-cause-analysis"
    )
    
    # Set tracing to true
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
    logger.info("LangSmith tracing enabled")
    return True

def configure_metrics_source(metrics_source, prometheus_url=None, auth_type=None, 
                           oauth_client_id=None, oauth_client_secret=None, 
                           oauth_token_url=None, username=None, password=None):
    """
    Configure the metrics source for the investigation
    
    Args:
        metrics_source: 'kubernetes' or 'prometheus'
        prometheus_url: URL of Prometheus API (if metrics_source is 'prometheus')
        auth_type: 'none', 'basic', or 'oauth2' (if metrics_source is 'prometheus')
        oauth_client_id: OAuth2 client ID (if auth_type is 'oauth2')
        oauth_client_secret: OAuth2 client secret (if auth_type is 'oauth2')
        oauth_token_url: OAuth2 token URL (if auth_type is 'oauth2')
        username: Basic auth username (if auth_type is 'basic')
        password: Basic auth password (if auth_type is 'basic')
    """
    # Set metrics source
    os.environ["METRICS_SOURCE"] = metrics_source
    
    if metrics_source.lower() == "prometheus":
        if not prometheus_url:
            logger.warning("Prometheus URL not provided. Metrics collection may fail.")
            return False
        
        os.environ["PROMETHEUS_URL"] = prometheus_url
        os.environ["PROMETHEUS_AUTH_TYPE"] = auth_type or "none"
        
        if auth_type == "oauth2":
            if not all([oauth_client_id, oauth_client_secret, oauth_token_url]):
                logger.warning("OAuth2 credentials incomplete. Authentication may fail.")
                return False
                
            os.environ["PROMETHEUS_OAUTH_CLIENT_ID"] = oauth_client_id
            os.environ["PROMETHEUS_OAUTH_CLIENT_SECRET"] = oauth_client_secret
            os.environ["PROMETHEUS_OAUTH_TOKEN_URL"] = oauth_token_url
            logger.info("Configured Prometheus with OAuth2 authentication")
            
        elif auth_type == "basic":
            if not all([username, password]):
                logger.warning("Basic auth credentials incomplete. Authentication may fail.")
                return False
                
            os.environ["PROMETHEUS_USERNAME"] = username
            os.environ["PROMETHEUS_PASSWORD"] = password
            logger.info("Configured Prometheus with Basic authentication")
            
        else:
            logger.info("Configured Prometheus without authentication")
        
        return True
    else:
        logger.info("Using Kubernetes Metrics API for metrics collection")
        return True

def configure_cluster_access(kubeconfig=None, kubectl_path=None):
    """
    Configure access to the Kubernetes cluster for the cluster agent
    
    Args:
        kubeconfig: Path to kubeconfig file for cluster access
        kubectl_path: Path to kubectl binary
    """
    if kubeconfig:
        os.environ["KUBECONFIG"] = kubeconfig
        logger.info(f"Using kubeconfig from: {kubeconfig}")
    
    if kubectl_path:
        os.environ["KUBECTL_PATH"] = kubectl_path
        logger.info(f"Using kubectl from: {kubectl_path}")
    else:
        # Try to find kubectl in PATH
        import shutil
        kubectl = shutil.which("kubectl")
        if kubectl:
            logger.info(f"Found kubectl at: {kubectl}")
        else:
            logger.warning("kubectl not found in PATH. Cluster agent may not work properly.")
    
    return True

def save_report(result, output_path):
    """
    Save the investigation report to a markdown file
    
    Args:
        result: Investigation results
        output_path: Path to save report
    """
    logger.info(f"Saving report to {output_path}")
    
    with open(output_path, "w") as f:
        f.write("# Kubernetes Root Cause Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Initial Symptoms\n\n")
        f.write(f"{result.get('initial_symptoms', 'No symptoms provided')}\n\n")
        
        f.write("## Root Cause Analysis\n\n")
        root_causes = result.get("root_causes", [])
        if root_causes:
            for cause in root_causes:
                confidence = cause.get("confidence", 0) * 100
                category = cause.get("category", "Unknown").capitalize()
                component = cause.get("component", "Unknown")
                
                f.write(f"### {category} Issue in {component} (Confidence: {confidence:.1f}%)\n\n")
                f.write(f"{cause.get('description', 'No description provided')}\n\n")
                
                # Supporting evidence
                if "supporting_evidence" in cause:
                    f.write("**Supporting Evidence:**\n\n")
                    for evidence in cause.get("supporting_evidence", []):
                        f.write(f"- {evidence}\n")
                    f.write("\n")
        else:
            f.write("No definitive root causes identified.\n\n")
            
        f.write("## Recommended Actions\n\n")
        recommendations = result.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                priority = rec.get("priority", "medium").upper()
                action = rec.get("action", "No action provided")
                component = rec.get("component", "Unknown")
                
                f.write(f"### {priority}: {action} on {component}\n\n")
                f.write(f"{rec.get('instructions', 'No detailed instructions provided')}\n\n")
                
                f.write(f"**Impact:** {rec.get('impact', 'Unknown')}\n\n")
                f.write(f"**Effort:** {rec.get('effort', 'Unknown')}\n\n")
        
        next_actions = result.get("next_actions", [])
        if next_actions and not recommendations:
            f.write("### Next Actions\n\n")
            for i, action in enumerate(next_actions, 1):
                f.write(f"{i}. {action}\n")
            f.write("\n")
        
        # Prevention measures
        prevention = result.get("prevention_measures", [])
        if prevention:
            f.write("## Prevention Measures\n\n")
            for measure in prevention:
                f.write(f"- {measure}\n")
            f.write("\n")
        
        # Evidence summary
        f.write("## Evidence Collected\n\n")
        evidence = result.get("evidence", [])
        if evidence:
            for item in evidence:
                resource_type = item.get("resource_type", "Unknown")
                analysis = item.get("analysis", "No analysis provided")
                confidence = item.get("confidence", 0) * 100
                
                f.write(f"### {resource_type} (Confidence: {confidence:.1f}%)\n\n")
                f.write(f"{analysis}\n\n")
        else:
            f.write("No evidence was collected during the investigation.\n\n")
        
        # Add confidence scores
        f.write("## Confidence Summary\n\n")
        f.write("| Area | Confidence |\n")
        f.write("|------|------------|\n")
        
        confidence_scores = result.get("confidence_scores", {})
        for area, score in confidence_scores.items():
            f.write(f"| {area.replace('_', ' ').capitalize()} | {score*100:.1f}% |\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Kubernetes Root Cause Analysis Tool"
    )
    
    # Define symptom input methods
    symptoms_group = parser.add_mutually_exclusive_group(required=True)
    symptoms_group.add_argument(
        "--symptoms", "-s", type=str,
        help="Description of the Kubernetes issue symptoms"
    )
    symptoms_group.add_argument(
        "--symptoms-file", "-f", type=str,
        help="Path to file containing symptoms description"
    )
    symptoms_group.add_argument(
        "--preset", "-p", type=str, choices=list(SYMPTOM_CATEGORIES.keys()),
        help="Use predefined symptom preset"
    )
    
    # Define other options
    parser.add_argument(
        "--namespace", "-n", type=str, default="default",
        help="Kubernetes namespace to investigate"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="output/investigation.json",
        help="Path to save investigation results"
    )
    parser.add_argument(
        "--visualize", "-v", action="store_true",
        help="Generate visualization of the investigation"
    )
    parser.add_argument(
        "--analyze", "-a", action="store_true",
        help="Analyze user input to identify symptom category and enhance description"
    )
    parser.add_argument(
        "--debug", "-d", action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up LangSmith for tracing
    setup_langsmith()
    
    # Get symptoms from command line, file, or preset
    symptoms = None
    category = "custom"
    
    if args.symptoms:
        symptoms = args.symptoms
        if args.analyze:
            logger.info("Analyzing symptoms using NLP...")
            category, enhanced_symptoms = analyze_symptoms(symptoms)
            logger.info(f"Symptoms categorized as: {category}")
            
            # Print analysis results
            print(f"\nSymptom Analysis Results:")
            print(f"Category: {category.upper()}")
            print(f"Enhanced description: {enhanced_symptoms}\n")
            
            # Ask if user wants to use enhanced description
            use_enhanced = input("Use enhanced symptom description? (y/n): ").lower().strip()
            if use_enhanced == 'y' or use_enhanced == 'yes':
                symptoms = enhanced_symptoms
                print(f"Using enhanced description: {symptoms}\n")
            else:
                print(f"Using original description: {symptoms}\n")
    
    elif args.symptoms_file:
        try:
            with open(args.symptoms_file, 'r') as f:
                symptoms = f.read().strip()
            logger.info(f"Read symptoms from file: {args.symptoms_file}")
            
            if args.analyze:
                logger.info("Analyzing symptoms from file using NLP...")
                category, enhanced_symptoms = analyze_symptoms(symptoms)
                logger.info(f"Symptoms categorized as: {category}")
                
                # Print analysis results
                print(f"\nSymptom Analysis Results:")
                print(f"Category: {category.upper()}")
                print(f"Enhanced description: {enhanced_symptoms}\n")
                
                # Ask if user wants to use enhanced description
                use_enhanced = input("Use enhanced symptom description? (y/n): ").lower().strip()
                if use_enhanced == 'y' or use_enhanced == 'yes':
                    symptoms = enhanced_symptoms
                    print(f"Using enhanced description: {symptoms}\n")
                else:
                    print(f"Using original description: {symptoms}\n")
                
        except Exception as e:
            logger.error(f"Error reading symptoms file: {e}")
            print(f"Error reading symptoms file: {e}")
            sys.exit(1)
    
    elif args.preset:
        category = args.preset
        symptoms = get_symptom_preset(args.preset)
        logger.info(f"Using preset symptoms for category: {category}")
        print(f"Using preset symptoms: {symptoms}\n")
    
    # Check if symptoms were properly loaded
    if not symptoms:
        logger.error("No symptoms provided")
        print("Error: No symptoms provided. Please provide symptoms via --symptoms, --symptoms-file, or --preset")
        sys.exit(1)
    
    logger.info(f"Starting investigation with symptoms: {symptoms[:100]}...")
    print(f"Starting investigation...\n")
    
    try:
        # Run the investigation
        result = run_investigation(symptoms)
        
        # Add metadata
        result["timestamp"] = datetime.now().isoformat()
        result["symptom_category"] = category
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        
        # Save the results
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Investigation completed and saved to {args.output}")
        
        # Print summary
        print("\nInvestigation Results:")
        print(f"Category: {category.upper()}")
        
        # Print root causes
        print("\nRoot Causes:")
        if "root_causes" in result and result["root_causes"]:
            for i, cause in enumerate(result["root_causes"], 1):
                print(f"{i}. {cause['cause']} (Confidence: {cause['confidence']}%)")
        else:
            print("No root causes identified")
        
        # Print recommended actions
        print("\nRecommended Actions:")
        if "recommended_actions" in result and result["recommended_actions"]:
            for i, action in enumerate(result["recommended_actions"], 1):
                print(f"{i}. {action}")
        else:
            print("No recommended actions")
        
        # Generate visualization if requested
        if args.visualize:
            vis_output = f"{os.path.splitext(args.output)[0]}_graph.html"
            generate_investigation_graph(result, vis_output)
            logger.info(f"Visualization generated and saved to {vis_output}")
            print(f"\nVisualization saved to {vis_output}")
        
        # Also save raw JSON for debugging
        debug_output = f"{os.path.splitext(args.output)[0]}_raw.json"
        with open(debug_output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Raw investigation results saved to {debug_output}")
        
        print(f"\nAll results saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Error during investigation: {e}")
        logger.error(traceback.format_exc())
        print(f"Error during investigation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 