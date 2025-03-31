#!/usr/bin/env python3
"""
Test script to verify template formatting with escaped JSON curly braces
"""
from langchain_core.prompts import ChatPromptTemplate
import json

def test_master_agent_templates():
    """Test the master agent's templates with escaped JSON formatting"""
    print("Testing master agent templates...")
    
    # Test assessment prompt template
    assessment_template = """
    ## Initial Symptoms
    {symptoms}
    
    ## Task
    Perform an initial assessment of these symptoms.
    
    Output your analysis in the following JSON format:
    ```json
    {{
      "investigation_phase": "initial_assessment",
      "initial_hypothesis": {{
        "possible_causes": ["cause1", "cause2"],
        "priority_areas": ["area1", "area2"]
      }},
      "specialist_agents_to_activate": ["agent1", "agent2"],
      "confidence_scores": {{
        "area1": 0.8,
        "area2": 0.6
      }}
    }}
    ```
    """
    
    # Create and format the prompt
    assessment_prompt = ChatPromptTemplate.from_template(assessment_template)
    formatted = assessment_prompt.format(symptoms="Test symptoms")
    
    print("Assessment prompt formatting successful!")
    
    # Test hypothesis prompt template
    hypothesis_template = """
    ## Investigation State
    Current phase: {phase}
    
    Output your analysis in the following JSON format:
    ```json
    {{
      "investigation_phase": "hypothesis_testing",
      "current_hypothesis": {{
        "most_likely_causes": ["cause1", "cause2"],
        "focus_areas": ["area1", "area2"],
        "type": "network"
      }},
      "specialist_agents_to_activate": ["network", "metrics"],
      "confidence_scores": {{
        "area1": 0.7,
        "area2": 0.5
      }}
    }}
    ```
    """
    
    # Create and format the prompt
    hypothesis_prompt = ChatPromptTemplate.from_template(hypothesis_template)
    formatted = hypothesis_prompt.format(phase="hypothesis_testing")
    
    print("Hypothesis prompt formatting successful!")
    
    print("All master agent templates passed!")

def test_cluster_agent_templates():
    """Test the cluster agent's templates with escaped JSON formatting"""
    print("Testing cluster agent templates...")
    
    # Test analysis template
    analysis_template = """
    ## Task Description
    {task_description}
    
    ## Evidence Collected
    {evidence_json}
    
    Output your analysis in the following JSON format:
    ```json
    {{
      "analysis": "detailed analysis of the cluster evidence",
      "potential_issues": ["issue1", "issue2"],
      "confidence": 0.8,
      "further_investigation": ["area1", "area2"],
      "control_plane_health": "healthy"
    }}
    ```
    """
    
    # Create and format the prompt
    analysis_prompt = ChatPromptTemplate.from_template(analysis_template)
    formatted = analysis_prompt.format(
        task_description="Test task",
        evidence_json=json.dumps([{"type": "test"}])
    )
    
    print("Cluster agent template formatting successful!")

def test_network_agent_templates():
    """Test the network agent's templates with escaped JSON formatting"""
    print("Testing network agent templates...")
    
    # Test analysis template
    analysis_template = """
    ## Task Description
    {task_description}
    
    ## Evidence Collected
    {evidence_json}
    
    Output your analysis in the following JSON format:
    ```json
    {{
      "analysis": "detailed analysis of the network evidence",
      "potential_issues": ["issue1", "issue2"],
      "confidence": 0.7,
      "further_investigation": ["area1", "area2"]
    }}
    ```
    """
    
    # Create and format the prompt
    analysis_prompt = ChatPromptTemplate.from_template(analysis_template)
    formatted = analysis_prompt.format(
        task_description="Test task",
        evidence_json=json.dumps([{"type": "test"}])
    )
    
    print("Network agent template formatting successful!")

def test_metrics_agent_templates():
    """Test the metrics agent's templates with escaped JSON formatting"""
    print("Testing metrics agent templates...")
    
    # Test analysis template
    analysis_template = """
    ## Task Description
    {task_description}
    
    ## Evidence Collected
    {evidence_json}
    
    Output your analysis in the following JSON format:
    ```json
    {{
      "analysis": "detailed analysis of the metrics evidence",
      "potential_issues": ["issue1", "issue2"],
      "confidence": 0.6,
      "further_investigation": ["area1", "area2"],
      "resource_constraints": ["resource1", "resource2"]
    }}
    ```
    """
    
    # Create and format the prompt
    analysis_prompt = ChatPromptTemplate.from_template(analysis_template)
    formatted = analysis_prompt.format(
        task_description="Test task",
        evidence_json=json.dumps([{"type": "test"}])
    )
    
    print("Metrics agent template formatting successful!")

if __name__ == "__main__":
    print("Testing template formatting with escaped JSON curly braces...")
    try:
        test_master_agent_templates()
        test_cluster_agent_templates()
        test_network_agent_templates()
        test_metrics_agent_templates()
        print("\nAll templates passed formatting tests!")
    except Exception as e:
        print(f"Error in template tests: {e}") 