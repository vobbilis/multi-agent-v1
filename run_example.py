#!/usr/bin/env python3
"""
Example runner for Kubernetes Root Cause Analysis system
"""
import os
import json
import logging
from datetime import datetime
import shutil

# Configure environment
os.environ["METRICS_SOURCE"] = "kubernetes"
os.environ["INVESTIGATION_NAMESPACE"] = "default" 
os.environ["MOCK_K8S"] = "true"  # Use mock mode for demonstration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure output directories exist
OUTPUT_DIRS = {
    "base": "output",
    "investigations": "output/investigations",
    "visualizations": "output/visualizations",
    "graphs": "output/visualizations/graphs",
    "heatmaps": "output/visualizations/heatmaps"
}

def ensure_output_dirs():
    """Ensure all output directories exist"""
    for dir_path in OUTPUT_DIRS.values():
        os.makedirs(dir_path, exist_ok=True)
    logger.info("Output directories created")

def print_mock_investigation():
    """
    Print a mock investigation result to demonstrate the output format
    without requiring API calls
    """
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Sample investigation result
    mock_result = {
        "investigation_phase": "recommendation_generation",
        "initial_symptoms": """
        Several pods in the production namespace keep restarting with CrashLoopBackOff status.
        The application logs show connection timeouts when trying to reach the database service.
        This started approximately 30 minutes after a network policy update was applied.
        CPU usage appears to be spiking during peak traffic hours.
        Some pods are being OOMKilled occasionally.
        Control plane nodes are reporting disk pressure warnings.
        """,
        "root_causes": [
            {
                "category": "network_policy",
                "component": "allow-backend-to-database",
                "description": "The recently applied network policy is incorrectly configured and is blocking connections from backend pods to the database service.",
                "confidence": 0.85,
                "supporting_evidence": ["Network policy analysis", "Connection timeout patterns", "Temporal correlation with policy update"]
            },
            {
                "category": "resource_constraint",
                "component": "node_disk_pressure",
                "description": "Control plane nodes are experiencing disk pressure which is affecting the scheduler and API server performance.",
                "confidence": 0.78,
                "supporting_evidence": ["Control plane metrics", "Node status reports", "API server latency patterns"]
            },
            {
                "category": "memory_limit",
                "component": "pod_configuration",
                "description": "Pod memory limits are set too low for the current workload, causing OOMKilled events during peak times.",
                "confidence": 0.72,
                "supporting_evidence": ["Pod metrics analysis", "OOMKilled event patterns", "Memory usage spikes"]
            }
        ],
        "next_actions": [
            "Update the network policy to correctly allow backend pods to communicate with the database service on port 5432",
            "Increase available disk space on control plane nodes by removing unused images and logs",
            "Adjust pod memory limits to accommodate peak usage patterns",
            "Consider horizontal scaling of backend services to distribute load"
        ],
        "prevention_measures": [
            "Implement network policy testing in pre-production environment before applying to production",
            "Set up automated monitoring and alerts for disk pressure on control plane nodes",
            "Review and adjust resource quotas based on regular usage patterns analysis",
            "Implement resource limit recommendations based on historical usage data"
        ],
        "confidence_scores": {
            "network": 0.85,
            "network_policy": 0.92,
            "service_connectivity": 0.79,
            "disk_constraint": 0.82,
            "memory_constraint": 0.78,
            "control_plane": 0.76
        },
        "findings": {
            "network": {
                "agent_type": "network",
                "analysis": "Network policies are blocking required communication paths between backend and database services.",
                "confidence": 0.85,
                "potential_issues": [
                    "Restrictive network policy on database service",
                    "Missing ingress rule for backend to database communication",
                    "Incorrect port specification in network policy"
                ]
            },
            "metrics": {
                "agent_type": "metrics",
                "analysis": "Resource constraints are affecting pod stability and performance.",
                "confidence": 0.76,
                "potential_issues": [
                    "Memory limits too restrictive for workload",
                    "CPU throttling during peak times",
                    "High network latency correlating with connection timeouts"
                ]
            },
            "cluster": {
                "agent_type": "cluster",
                "analysis": "Control plane components show signs of degraded performance due to disk pressure.",
                "confidence": 0.78,
                "potential_issues": [
                    "Disk pressure on control plane nodes",
                    "API server performance degradation",
                    "Scheduling delays affecting pod placement"
                ]
            }
        },
        "confidence_history": {
            "2023-05-01T12:00:00": {"network": 0.3, "metrics": 0.2},
            "2023-05-01T12:05:00": {"network": 0.5, "metrics": 0.3, "network_policy": 0.6},
            "2023-05-01T12:10:00": {"network": 0.7, "metrics": 0.4, "network_policy": 0.8},
            "2023-05-01T12:15:00": {"network": 0.85, "metrics": 0.5, "network_policy": 0.9, "service_connectivity": 0.7}
        }
    }
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    investigation_id = f"investigation_{timestamp}"
    
    # Output the result for inspection - JSON file
    json_output_path = os.path.join(OUTPUT_DIRS["investigations"], f"{investigation_id}.json")
    with open(json_output_path, "w") as f:
        json.dump(mock_result, f, indent=2)
    logger.info(f"Investigation result saved to {json_output_path}")
    
    # Generate summary report in markdown format
    summary_output_path = os.path.join(OUTPUT_DIRS["investigations"], f"{investigation_id}_summary.md")
    with open(summary_output_path, "w") as f:
        f.write(f"# Kubernetes Root Cause Analysis Summary\n\n")
        f.write(f"**Investigation ID**: {investigation_id}\n")
        f.write(f"**Date/Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {mock_result['investigation_phase'].replace('_', ' ').title()}\n\n")
        
        f.write("## Initial Symptoms\n\n")
        f.write(f"```\n{mock_result['initial_symptoms'].strip()}\n```\n\n")
        
        f.write("## Root Causes\n\n")
        for cause in mock_result.get("root_causes", []):
            confidence = cause.get("confidence", 0) * 100
            f.write(f"### {cause.get('category').replace('_', ' ').title()}: {cause.get('component')} ({confidence:.1f}%)\n\n")
            f.write(f"{cause.get('description')}\n\n")
            f.write("**Supporting Evidence**:\n")
            for evidence in cause.get("supporting_evidence", []):
                f.write(f"- {evidence}\n")
            f.write("\n")
        
        f.write("## Recommended Actions\n\n")
        for i, action in enumerate(mock_result.get("next_actions", []), 1):
            f.write(f"{i}. {action}\n")
        f.write("\n")
        
        f.write("## Prevention Measures\n\n")
        for i, measure in enumerate(mock_result.get("prevention_measures", []), 1):
            f.write(f"{i}. {measure}\n")
        f.write("\n")
        
        f.write("## Confidence Scores\n\n")
        f.write("| Area | Confidence |\n")
        f.write("|------|------------|\n")
        for area, score in mock_result.get("confidence_scores", {}).items():
            f.write(f"| {area.replace('_', ' ').title()} | {score*100:.1f}% |\n")
        f.write("\n")
        
        f.write("## Specialist Agent Findings\n\n")
        for agent_type, finding in mock_result.get("findings", {}).items():
            f.write(f"### {agent_type.upper()} AGENT\n\n")
            f.write(f"**Analysis**: {finding.get('analysis')}\n\n")
            f.write(f"**Confidence**: {finding.get('confidence', 0)*100:.1f}%\n\n")
            f.write("**Potential Issues**:\n")
            for issue in finding.get("potential_issues", []):
                f.write(f"- {issue}\n")
            f.write("\n")
    
    logger.info(f"Investigation summary saved to {summary_output_path}")
    
    try:
        # Import visualization utilities
        from utils.visualizations import generate_investigation_graph, generate_confidence_heatmap
        
        # Generate visualizations
        logger.info("Generating visualizations...")
        
        # Investigation graph
        graph_output_path = os.path.join(OUTPUT_DIRS["graphs"], f"{investigation_id}_graph.html")
        generate_investigation_graph(mock_result, graph_output_path)
        logger.info(f"Investigation graph saved to {graph_output_path}")
        
        # Confidence heatmap
        heatmap_output_path = os.path.join(OUTPUT_DIRS["heatmaps"], f"{investigation_id}_heatmap.html")
        generate_confidence_heatmap(mock_result, heatmap_output_path)
        logger.info(f"Confidence heatmap saved to {heatmap_output_path}")
        
        # Create index file to link all visualizations
        index_path = os.path.join(OUTPUT_DIRS["visualizations"], "index.html")
        with open(index_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes RCA Visualizations</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .viz-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .viz-item {{
            flex: 1;
            min-width: 300px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            background-color: #f9f9f9;
        }}
        .viz-item h3 {{
            margin-top: 0;
            color: #3498db;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Kubernetes Root Cause Analysis Visualizations</h1>
        
        <h2>Investigation: {investigation_id}</h2>
        
        <div class="viz-list">
            <div class="viz-item">
                <h3>Investigation Graph</h3>
                <p>Visualization of the investigation workflow and findings.</p>
                <a href="./graphs/{investigation_id}_graph.html" target="_blank">View Investigation Graph</a>
            </div>
            
            <div class="viz-item">
                <h3>Confidence Heatmap</h3>
                <p>Visualization of confidence scores over time.</p>
                <a href="./heatmaps/{investigation_id}_heatmap.html" target="_blank">View Confidence Heatmap</a>
            </div>
        </div>
        
        <h2>Investigation Results</h2>
        <p>
            <a href="../investigations/{investigation_id}_summary.md" target="_blank">View Investigation Summary</a> |
            <a href="../investigations/{investigation_id}.json" target="_blank">View Raw JSON</a>
        </p>
    </div>
</body>
</html>
""")
        logger.info(f"Visualization index saved to {index_path}")
        
        # Clean up any files in the root directory if they exist
        root_files = [
            f"investigation_result_{timestamp}.json",
            f"investigation_graph_{timestamp}.html",
            f"confidence_heatmap_{timestamp}.html"
        ]
        
        for file_path in root_files:
            if os.path.exists(file_path):
                logger.info(f"Moving {file_path} to organized directory structure")
                if file_path.endswith(".json"):
                    shutil.move(file_path, os.path.join(OUTPUT_DIRS["investigations"], f"{investigation_id}.json"))
                elif "graph" in file_path:
                    shutil.move(file_path, os.path.join(OUTPUT_DIRS["graphs"], f"{investigation_id}_graph.html"))
                elif "heatmap" in file_path:
                    shutil.move(file_path, os.path.join(OUTPUT_DIRS["heatmaps"], f"{investigation_id}_heatmap.html"))
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
    
    # Print summary to console
    print("\n=== Investigation Summary ===")
    print(f"Phase: {mock_result['investigation_phase']}")
    print("\nRoot Causes:")
    for cause in mock_result.get("root_causes", []):
        confidence = cause.get("confidence", 0) * 100
        print(f"- {cause.get('category')}: {cause.get('component')} ({confidence:.1f}%)")
        print(f"  {cause.get('description')}")
    
    print("\nRecommended Actions:")
    for i, action in enumerate(mock_result.get("next_actions", []), 1):
        print(f"{i}. {action}")
    
    print("\nPrevention Measures:")
    for i, measure in enumerate(mock_result.get("prevention_measures", []), 1):
        print(f"{i}. {measure}")
    
    print("\nConfidence Scores:")
    for area, score in mock_result.get("confidence_scores", {}).items():
        print(f"- {area}: {score*100:.1f}%")
    
    print("\nFindings from Specialist Agents:")
    for agent_type, finding in mock_result.get("findings", {}).items():
        print(f"\n[{agent_type.upper()} AGENT]")
        print(f"Analysis: {finding.get('analysis')}")
        print(f"Confidence: {finding.get('confidence', 0)*100:.1f}%")
        print("Potential issues:")
        for issue in finding.get("potential_issues", []):
            print(f" - {issue}")
    
    print(f"\nAll output files were saved to organized directories under '{OUTPUT_DIRS['base']}'")
    print(f"View the visualizations by opening: {index_path}")
    
    return mock_result

if __name__ == "__main__":
    print_mock_investigation() 