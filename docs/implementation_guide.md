# Implementation Guide
## Kubernetes Root Cause Analysis Multi-Agent System

This document provides implementation guidance and code structure for the LangGraph and LangSmith based Kubernetes root cause analysis system.

## Project Structure

```
smagent/
├── main.py                    # Entry point for the application
├── docs/                      # Documentation
├── config/                    # Configuration files
├── k8s/                       # Kubernetes deployment manifests
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── master_agent.py        # Master coordinator agent
│   ├── cluster_agent.py       # Cluster infrastructure agent
│   ├── network_agent.py       # Networking specialist agent
│   ├── workload_agent.py      # Workload specialist agent
│   ├── config_agent.py        # Configuration specialist agent
│   ├── resource_agent.py      # Resource management specialist agent
│   ├── state_agent.py         # Cluster state specialist agent
│   ├── logs_agent.py          # Logs and events specialist agent
│   └── security_agent.py      # Security specialist agent
├── models/                    # Data models and schemas
│   ├── __init__.py
│   ├── evidence.py            # Evidence data models
│   ├── findings.py            # Agent findings models
│   ├── recommendations.py     # Recommendation models
│   └── tasks.py               # Task definition models
├── graph/                     # LangGraph implementation
│   ├── __init__.py
│   ├── workflow.py            # Main workflow definition
│   ├── nodes.py               # Graph node definitions
│   └── decision_trees.py      # Decision tree implementations
├── k8s_client/                # Kubernetes client wrappers
│   ├── __init__.py
│   ├── cluster.py             # Cluster API client
│   ├── pods.py                # Pod API client
│   ├── services.py            # Service API client
│   └── events.py              # Events API client
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── visualizations.py      # Visualization utilities
│   ├── langsmith_logger.py    # LangSmith integration
│   └── evidence_collector.py  # Evidence collection utilities
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_agents/           # Agent tests
    ├── test_graph/            # Graph tests
    └── test_k8s_client/       # Kubernetes client tests
```

## Key Implementation Components

### 1. LangGraph Workflow Implementation

The core of the system is implemented using LangGraph to create a directed graph of agent interactions:

```python
# graph/workflow.py
from typing import Dict, List, Any
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from agents.master_agent import MasterAgent
from agents.cluster_agent import ClusterAgent
from agents.network_agent import NetworkAgent
# Import other specialist agents

# Define the state structure
class AgentState:
    initial_symptoms: str
    investigation_phase: str
    findings: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    current_hypothesis: Dict[str, Any]
    confidence_scores: Dict[str, float]
    next_actions: List[str]
    
# Create master and specialist agents
master_agent = MasterAgent()
cluster_agent = ClusterAgent()
network_agent = NetworkAgent()
# Initialize other specialist agents

# Define the workflow graph
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("master", master_agent)
workflow.add_node("cluster_analysis", cluster_agent)
workflow.add_node("network_analysis", network_agent)
# Add other specialist agent nodes

# Define conditional routing based on investigation phase
def route_by_phase(state):
    phase = state["investigation_phase"]
    if phase == "initial_assessment":
        return ["cluster_analysis", "network_analysis"] # Parallel initial assessment
    elif phase == "hypothesis_testing":
        # Route based on current hypothesis
        if state["current_hypothesis"]["type"] == "network":
            return "network_analysis"
        elif state["current_hypothesis"]["type"] == "cluster":
            return "cluster_analysis"
        # Add other conditional routing
    elif phase == "root_cause_determination":
        return "master"
    elif phase == "recommendation_generation":
        return END
    
# Add conditional edges
workflow.add_conditional_edges("master", route_by_phase)
workflow.add_edge("cluster_analysis", "master")
workflow.add_edge("network_analysis", "master")
# Add other edges

# Set entry point
workflow.set_entry_point("master")

# Compile the graph
k8s_rca_app = workflow.compile()
```

### 2. Master Coordinator Agent Implementation

The master agent orchestrates the investigation process:

```python
# agents/master_agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.llms import ChatOpenAI
from models.evidence import Evidence
from models.findings import Finding
from models.tasks import Task
from models.recommendations import Recommendation

class MasterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        self.system_prompt = """
        You are the master coordinator agent in a Kubernetes root cause analysis system.
        Your job is to:
        1. Assess initial symptoms
        2. Formulate investigation plans
        3. Direct specialist agents
        4. Analyze findings
        5. Determine root causes
        6. Generate recommendations
        
        Based on the current state of the investigation and evidence collected,
        determine the next steps and update the investigation state.
        """
        
    def _create_prompt(self, state):
        # Create dynamic prompt based on the current state
        template = self.system_prompt + """
        Current investigation phase: {phase}
        Initial symptoms: {symptoms}
        
        Evidence collected so far:
        {evidence}
        
        Current hypothesis:
        {hypothesis}
        
        Findings from specialist agents:
        {findings}
        
        Based on this information:
        1. Update the investigation phase if needed
        2. Determine the next investigation steps
        3. Update the current hypothesis
        4. Assign confidence scores to potential root causes
        5. If appropriate, generate recommendations
        
        Output your analysis in JSON format.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        return prompt
    
    def __call__(self, state):
        # Parse the current state
        phase = state.get("investigation_phase", "initial_assessment")
        symptoms = state.get("initial_symptoms", "")
        evidence = state.get("evidence", [])
        hypothesis = state.get("current_hypothesis", {})
        findings = state.get("findings", {})
        
        # Create the prompt
        prompt = self._create_prompt(state)
        
        # Generate analysis
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Run the chain
        result = chain.invoke({
            "phase": phase,
            "symptoms": symptoms,
            "evidence": evidence,
            "hypothesis": hypothesis,
            "findings": findings
        })
        
        # Update the state with the analysis results
        return {
            "investigation_phase": result.get("investigation_phase", phase),
            "current_hypothesis": result.get("current_hypothesis", hypothesis),
            "confidence_scores": result.get("confidence_scores", {}),
            "next_actions": result.get("next_actions", []),
            # Preserve existing state elements
            "initial_symptoms": symptoms,
            "evidence": evidence,
            "findings": findings
        }
```

### 3. Specialist Agent Implementation Example

Each specialist agent follows a similar pattern but focuses on its domain:

```python
# agents/network_agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.llms import ChatOpenAI
from k8s_client.services import ServiceClient
from k8s_client.pods import PodClient
from models.evidence import Evidence
from models.findings import Finding

class NetworkAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        self.service_client = ServiceClient()
        self.pod_client = PodClient()
        self.system_prompt = """
        You are a Kubernetes networking specialist agent.
        Your job is to investigate network-related issues in a Kubernetes cluster.
        
        You need to:
        1. Examine network policies
        2. Check DNS resolution
        3. Verify service connectivity
        4. Identify ingress/egress problems
        5. Check for pod-to-pod communication issues
        
        Based on the task assigned to you, collect and analyze relevant evidence.
        """
        
    def collect_network_evidence(self, task):
        """Collect network-related evidence from the Kubernetes cluster"""
        evidence = []
        
        # Collect service information
        services = self.service_client.list_services()
        evidence.append(Evidence(
            resource_type="Service",
            raw_data=services,
            analysis="Services configuration and status collected"
        ))
        
        # Check for pod connectivity issues
        connectivity_issues = self.pod_client.check_pod_connectivity()
        evidence.append(Evidence(
            resource_type="PodConnectivity",
            raw_data=connectivity_issues,
            analysis="Pod connectivity check completed"
        ))
        
        # Add more evidence collection based on the task
        
        return evidence
    
    def analyze_evidence(self, evidence, task):
        """Analyze the collected evidence to draw findings"""
        template = self.system_prompt + """
        Task description: {task_description}
        
        Evidence collected:
        {evidence}
        
        Based on this evidence:
        1. Identify potential networking issues
        2. Determine the likelihood that networking is causing the reported symptoms
        3. Provide detailed analysis of network configurations
        4. Suggest specific areas for further investigation
        
        Output your analysis in JSON format.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Run the chain
        result = chain.invoke({
            "task_description": task.description,
            "evidence": evidence
        })
        
        return Finding(
            agent_type="network",
            evidence=evidence,
            analysis=result.get("analysis", ""),
            confidence=result.get("confidence", 0.0),
            potential_issues=result.get("potential_issues", [])
        )
    
    def __call__(self, state):
        # Extract task information from state
        investigation_phase = state.get("investigation_phase", "")
        current_hypothesis = state.get("current_hypothesis", {})
        
        # Create a task based on the current state
        task = Task(
            description=f"Investigate network issues related to {current_hypothesis.get('focus', 'general symptoms')}",
            type="network_investigation",
            priority="high" if current_hypothesis.get("type") == "network" else "medium"
        )
        
        # Collect evidence
        evidence = self.collect_network_evidence(task)
        
        # Analyze evidence
        finding = self.analyze_evidence(evidence, task)
        
        # Update the state with new evidence and findings
        updated_evidence = state.get("evidence", []) + evidence
        updated_findings = state.get("findings", {})
        updated_findings["network"] = finding
        
        return {
            "evidence": updated_evidence,
            "findings": updated_findings,
            # Preserve other state elements
            "investigation_phase": state.get("investigation_phase", ""),
            "initial_symptoms": state.get("initial_symptoms", ""),
            "current_hypothesis": state.get("current_hypothesis", {}),
            "confidence_scores": state.get("confidence_scores", {}),
            "next_actions": state.get("next_actions", [])
        }
```

### 4. Decision Tree Implementation

The decision tree component provides conditional execution paths:

```python
# graph/decision_trees.py
from typing import Dict, List, Any

class DecisionNode:
    def __init__(self, condition_fn, true_branch, false_branch):
        self.condition_fn = condition_fn
        self.true_branch = true_branch
        self.false_branch = false_branch
        
    def evaluate(self, state):
        if self.condition_fn(state):
            return self.true_branch
        return self.false_branch

class DecisionTree:
    def __init__(self, root_node):
        self.root_node = root_node
        
    def evaluate(self, state):
        current_node = self.root_node
        
        # Follow the decision path until we reach a leaf (string or END)
        while not isinstance(current_node, (str, type(None))):
            current_node = current_node.evaluate(state)
            
        return current_node

# Example decision tree for the root cause analysis workflow
def build_investigation_decision_tree():
    # Leaf nodes (specialist agents)
    cluster_leaf = "cluster_analysis"
    network_leaf = "network_analysis"
    workload_leaf = "workload_analysis"
    config_leaf = "config_analysis"
    master_leaf = "master"
    end_leaf = "END"
    
    # Condition functions
    def is_initial_phase(state):
        return state.get("investigation_phase") == "initial_assessment"
    
    def is_network_issue(state):
        confidence_scores = state.get("confidence_scores", {})
        return confidence_scores.get("network", 0) > 0.6
    
    def is_cluster_issue(state):
        confidence_scores = state.get("confidence_scores", {})
        return confidence_scores.get("cluster", 0) > 0.6
    
    def is_config_issue(state):
        confidence_scores = state.get("confidence_scores", {})
        return confidence_scores.get("config", 0) > 0.6
    
    def is_determination_phase(state):
        return state.get("investigation_phase") == "root_cause_determination"
    
    def is_recommendation_phase(state):
        return state.get("investigation_phase") == "recommendation_generation"
    
    # Build the tree from bottom up
    recommendation_node = DecisionNode(
        is_recommendation_phase,
        end_leaf,
        master_leaf
    )
    
    determination_node = DecisionNode(
        is_determination_phase,
        recommendation_node,
        master_leaf
    )
    
    config_issue_node = DecisionNode(
        is_config_issue,
        config_leaf,
        determination_node
    )
    
    cluster_issue_node = DecisionNode(
        is_cluster_issue,
        cluster_leaf,
        config_issue_node
    )
    
    network_issue_node = DecisionNode(
        is_network_issue,
        network_leaf,
        cluster_issue_node
    )
    
    root_node = DecisionNode(
        is_initial_phase,
        master_leaf,
        network_issue_node
    )
    
    return DecisionTree(root_node)
```

### 5. LangSmith Integration for Tracing and Monitoring

```python
# utils/langsmith_logger.py
from langsmith import Client, traceable
from langsmith.run_trees import RunTree
import os

class LangSmithLogger:
    def __init__(self):
        self.client = Client(
            api_key=os.environ.get("LANGSMITH_API_KEY"),
            api_url=os.environ.get("LANGSMITH_API_URL", "https://api.smith.langchain.com")
        )
        
    @traceable(run_type="investigation", name="kubernetes_rca")
    def trace_investigation(self, symptoms, workflow_instance):
        """Trace a complete investigation workflow"""
        result = workflow_instance.invoke({"initial_symptoms": symptoms})
        return result
    
    @traceable(run_type="agent", name="master_coordinator")
    def trace_master_agent(self, state):
        """Trace master agent execution"""
        pass
    
    @traceable(run_type="agent", name="specialist_agent")
    def trace_specialist_agent(self, agent_type, state):
        """Trace specialist agent execution"""
        pass
    
    def log_evidence(self, evidence, run_id):
        """Log collected evidence to LangSmith"""
        self.client.create_dataset("kubernetes_evidence", description="Evidence collected during K8s RCA")
        self.client.create_example(
            inputs={"investigation_id": run_id},
            outputs={"evidence": evidence},
            dataset_name="kubernetes_evidence"
        )
        
    def log_decision_path(self, decision_path, run_id):
        """Log the decision path taken during the investigation"""
        self.client.create_dataset("decision_paths", description="Decision paths in K8s RCA")
        self.client.create_example(
            inputs={"investigation_id": run_id},
            outputs={"path": decision_path},
            dataset_name="decision_paths"
        )
```

### 6. Kubernetes Client Implementation

```python
# k8s_client/cluster.py
from kubernetes import client, config
import logging

class ClusterClient:
    def __init__(self):
        try:
            # Try to load from within cluster
            config.load_incluster_config()
        except config.ConfigException:
            # Fall back to kubeconfig
            config.load_kube_config()
            
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
    def get_nodes(self):
        """Get information about all nodes in the cluster"""
        try:
            return self.core_v1.list_node()
        except Exception as e:
            logging.error(f"Error retrieving nodes: {e}")
            return []
            
    def get_node_metrics(self):
        """Get resource metrics for all nodes"""
        try:
            custom_api = client.CustomObjectsApi()
            return custom_api.list_cluster_custom_object(
                "metrics.k8s.io", "v1beta1", "nodes"
            )
        except Exception as e:
            logging.error(f"Error retrieving node metrics: {e}")
            return {}
            
    def get_cluster_events(self, field_selector=None):
        """Get cluster-wide events, optionally filtered"""
        try:
            return self.core_v1.list_event_for_all_namespaces(
                field_selector=field_selector
            )
        except Exception as e:
            logging.error(f"Error retrieving cluster events: {e}")
            return []
            
    def get_component_statuses(self):
        """Get status of control plane components"""
        try:
            return self.core_v1.list_component_status()
        except Exception as e:
            logging.error(f"Error retrieving component statuses: {e}")
            return []
```

### 7. Main Application Entry Point

```python
# main.py
import os
import argparse
import logging
from graph.workflow import k8s_rca_app
from utils.langsmith_logger import LangSmithLogger
from utils.visualizations import generate_investigation_graph

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Kubernetes Root Cause Analysis Engine")
    parser.add_argument("--symptoms", type=str, required=True, 
                        help="Description of the symptoms or issues being experienced")
    parser.add_argument("--namespace", type=str, default="default",
                        help="Kubernetes namespace to focus investigation on")
    parser.add_argument("--output", type=str, default="report.md",
                        help="Path to save the investigation report")
    parser.add_argument("--visualize", action="store_true",
                        help="Generate visualization of the investigation flow")
    args = parser.parse_args()
    
    # Initialize LangSmith logger
    langsmith_logger = LangSmithLogger()
    
    # Set environment variables for agents
    os.environ["INVESTIGATION_NAMESPACE"] = args.namespace
    
    # Run the investigation
    logging.info(f"Starting investigation with symptoms: {args.symptoms}")
    result = langsmith_logger.trace_investigation(args.symptoms, k8s_rca_app)
    
    # Generate report
    with open(args.output, "w") as f:
        f.write("# Kubernetes Root Cause Analysis Report\n\n")
        f.write(f"## Initial Symptoms\n{args.symptoms}\n\n")
        f.write("## Root Cause Analysis\n\n")
        
        for cause, confidence in result.get("confidence_scores", {}).items():
            if confidence > 0.6:
                f.write(f"### {cause.capitalize()} Issue (Confidence: {confidence*100:.1f}%)\n")
                # Add details from findings
                
        f.write("\n## Evidence Collected\n\n")
        for evidence in result.get("evidence", []):
            f.write(f"- {evidence.get('resource_type')}: {evidence.get('analysis')}\n")
            
        f.write("\n## Recommended Actions\n\n")
        for i, action in enumerate(result.get("next_actions", []), 1):
            f.write(f"{i}. {action}\n")
    
    logging.info(f"Investigation report saved to {args.output}")
    
    # Generate visualization if requested
    if args.visualize:
        viz_path = args.output.replace(".md", ".html")
        generate_investigation_graph(result, viz_path)
        logging.info(f"Investigation visualization saved to {viz_path}")

if __name__ == "__main__":
    main()
```

## Deployment

For Kubernetes deployment, create manifests:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-rca-engine
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8s-rca-engine
  template:
    metadata:
      labels:
        app: k8s-rca-engine
    spec:
      serviceAccountName: k8s-rca-service-account
      containers:
      - name: k8s-rca-engine
        image: k8s-rca-engine:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-credentials
              key: api-key
        - name: LANGSMITH_API_KEY
          valueFrom:
            secretKeyRef:
              name: langsmith-credentials
              key: api-key
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "500Mi"
```

## Configuration

Example configuration file:

```yaml
# config/config.yaml
agents:
  master:
    model: "gpt-4"
    temperature: 0.0
  specialist:
    model: "gpt-3.5-turbo"
    temperature: 0.0

investigation:
  default_timeout: 300
  max_evidence_items: 50
  confidence_threshold: 0.7
  
kubernetes:
  default_namespace: "default"
  resource_fetch_limit: 100
  
visualizations:
  enabled: true
  format: "html"
  
langsmith:
  project_name: "k8s-rca"
  trace_level: "detailed"
```

## Running Tests

```bash
# Run unit tests
python -m unittest discover -s tests

# Test specific components
python -m unittest tests.test_agents.test_master_agent
python -m unittest tests.test_graph.test_workflow
``` 