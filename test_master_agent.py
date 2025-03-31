#!/usr/bin/env python3
"""
Test script for the enhanced Master Agent with reasoning explanation.
"""
import sys
import json
import logging
import traceback
from agents.master_agent import MasterAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_confidence_scores(confidence_scores):
    """Format confidence scores for better readability."""
    if not confidence_scores:
        return "No confidence scores available"
    
    result = []
    for area, score in sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True):
        result.append(f"- {area}: {int(score * 100)}%")
    
    return "\n".join(result)

def format_investigation_result(result):
    """Format the investigation result for better readability."""
    output = []
    
    # Add investigation phase
    output.append(f"Investigation Phase: {result.get('investigation_phase', 'Unknown')}")
    output.append("")
    
    # Add confidence scores
    output.append("Confidence Scores:")
    output.append(format_confidence_scores(result.get('confidence_scores', {})))
    output.append("")
    
    # Add specialist agents to activate
    agents = result.get('specialist_agents_to_activate', [])
    if agents:
        output.append("Specialist Agents to Activate:")
        for agent in agents:
            output.append(f"- {agent}")
        output.append("")
    
    # Add hypothesis information
    hypothesis = result.get('current_hypothesis', {})
    if hypothesis:
        output.append("Current Hypothesis:")
        likely_causes = hypothesis.get('most_likely_causes', [])
        if likely_causes:
            output.append("  Most Likely Causes:")
            for cause in likely_causes:
                output.append(f"  - {cause}")
            output.append("")
        
        focus_areas = hypothesis.get('focus_areas', [])
        if focus_areas:
            output.append("  Focus Areas:")
            for area in focus_areas:
                output.append(f"  - {area}")
            output.append("")
    
    # Add root causes
    root_causes = result.get('root_causes', [])
    if root_causes:
        output.append("Root Causes:")
        for rc in root_causes:
            output.append(f"- {rc.get('category', 'Unknown')}: {rc.get('component', 'Unknown')}")
            output.append(f"  Description: {rc.get('description', 'No description')}")
            output.append(f"  Confidence: {int(rc.get('confidence', 0) * 100)}%")
            output.append("")
    
    # Add recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        output.append("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            output.append(f"{i}. {rec.get('action', 'Unknown action')}")
            output.append(f"   Component: {rec.get('component', 'Unknown')}")
            output.append(f"   Priority: {rec.get('priority', 'Unknown')}")
            output.append(f"   Impact: {rec.get('impact', 'Unknown')}")
            output.append("")
    
    return "\n".join(output)

def main():
    """Run a test of the master agent with explanation."""
    # Process command line arguments
    debug_mode = False
    symptoms = None
    
    # Check for debug flag
    if "--debug" in sys.argv:
        debug_mode = True
        sys.argv.remove("--debug")
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled")
    
    # Get symptoms from command line arguments
    if len(sys.argv) > 1:
        symptoms = " ".join(sys.argv[1:])
    else:
        symptoms = """
        My NodePort service internal-proxy-info-app-service is responding very slowly with high latency.
        Network policies were recently updated, and now connection times have increased by 300%.
        There are active chaos experiments running in the chaos-testing namespace.
        """
    
    try:
        # Create master agent with explanation enabled
        master_agent = MasterAgent(explain_reasoning=True)
        
        # Initial state with symptoms
        initial_state = {
            "investigation_phase": "initial_assessment",
            "initial_symptoms": symptoms
        }
        
        # Process initial state
        result = master_agent(initial_state)
        
        # Print the final result
        print("\nFINAL INVESTIGATION RESULT:")
        print("=" * 80)
        print(format_investigation_result(result))
        print("=" * 80)
        
        # Save as JSON for reference
        if debug_mode:
            print("\nRaw JSON result:")
            print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError occurred during test: {str(e)}")
        if debug_mode:
            traceback.print_exc()
    
if __name__ == "__main__":
    main() 