"""
Network Specialist Agent for Kubernetes Root Cause Analysis
"""
import json
import logging
from typing import Dict, List, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI

# Import models (these would be defined elsewhere)
class Evidence:
    def __init__(self, resource_type: str, raw_data: Any, analysis: str, confidence: float = 0.5):
        self.resource_type = resource_type
        self.raw_data = raw_data
        self.analysis = analysis
        self.confidence = confidence
        self.timestamp = None
        self.related_resources = []
        
    def to_dict(self):
        return {
            "resource_type": self.resource_type,
            "analysis": self.analysis,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "related_resources": self.related_resources
        }

class Finding:
    def __init__(self, agent_type: str, evidence: List[Evidence], analysis: str, 
                 confidence: float, potential_issues: List[str]):
        self.agent_type = agent_type
        self.evidence = evidence
        self.analysis = analysis
        self.confidence = confidence
        self.potential_issues = potential_issues
        
    def to_dict(self):
        return {
            "agent_type": self.agent_type,
            "evidence": [e.to_dict() for e in self.evidence],
            "analysis": self.analysis,
            "confidence": self.confidence,
            "potential_issues": self.potential_issues
        }

class Task:
    def __init__(self, description: str, type: str, priority: str):
        self.description = description
        self.type = type
        self.priority = priority
        
    def to_dict(self):
        return {
            "description": self.description,
            "type": self.type,
            "priority": self.priority
        }

# Mock Kubernetes clients (these would be real implementations)
class ServiceClient:
    def list_services(self, namespace=None):
        """Mock method to list services"""
        return [
            {"name": "frontend", "namespace": "default", "type": "ClusterIP", "ports": [80]},
            {"name": "backend", "namespace": "default", "type": "ClusterIP", "ports": [8080]},
            {"name": "database", "namespace": "default", "type": "ClusterIP", "ports": [5432]}
        ]
    
    def get_service_endpoints(self, name, namespace):
        """Mock method to get service endpoints"""
        if name == "database":
            return {"endpoints": [], "ready": False}
        return {"endpoints": ["10.0.0.1", "10.0.0.2"], "ready": True}

class PodClient:
    def list_pods(self, namespace=None, label_selector=None):
        """Mock method to list pods"""
        return [
            {"name": "frontend-5d8b9c7f68-abcde", "namespace": "default", "status": "Running", "ip": "10.1.0.1"},
            {"name": "backend-6f7b8d9c5e-fghij", "namespace": "default", "status": "Running", "ip": "10.1.0.2"},
            {"name": "database-7c8d9e0f1a-klmno", "namespace": "default", "status": "Running", "ip": "10.1.0.3"}
        ]
    
    def check_pod_connectivity(self, source_pod=None, target_service=None):
        """Mock method to check pod connectivity"""
        if target_service == "database":
            return {"status": "failed", "error": "connection timeout", "latency": None}
        return {"status": "success", "error": None, "latency": "2ms"}

class NetworkPolicyClient:
    def list_network_policies(self, namespace=None):
        """Mock method to list network policies"""
        return [
            {
                "name": "default-deny",
                "namespace": "default",
                "podSelector": {"matchLabels": {}},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [],
                "egress": []
            },
            {
                "name": "allow-frontend-to-backend",
                "namespace": "default",
                "podSelector": {"matchLabels": {"app": "backend"}},
                "policyTypes": ["Ingress"],
                "ingress": [
                    {
                        "from": [
                            {"podSelector": {"matchLabels": {"app": "frontend"}}}
                        ],
                        "ports": [{"port": 8080, "protocol": "TCP"}]
                    }
                ]
            },
            {
                "name": "allow-backend-to-database",
                "namespace": "default",
                "podSelector": {"matchLabels": {"app": "database"}},
                "policyTypes": ["Ingress"],
                "ingress": [
                    {
                        "from": [
                            {"podSelector": {"matchLabels": {"app": "backend"}}}
                        ],
                        "ports": [{"port": 5432, "protocol": "TCP"}]
                    }
                ]
            }
        ]

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkAgent:
    """
    Network specialist agent for the Kubernetes root cause analysis system.
    This agent focuses on investigating network-related issues such as:
    - Network policies
    - Service connectivity
    - DNS resolution
    - Ingress/egress connectivity
    - Pod-to-pod communication
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0):
        """
        Initialize the network agent with LLM settings and K8s clients
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.service_client = ServiceClient()
        self.pod_client = PodClient()
        self.network_policy_client = NetworkPolicyClient()
        
        self.system_prompt = """
        You are a Kubernetes networking specialist agent in a root cause analysis system.
        Your job is to investigate network-related issues in a Kubernetes cluster.
        
        You need to:
        1. Examine network policies
        2. Check DNS resolution
        3. Verify service connectivity
        4. Identify ingress/egress problems
        5. Check for pod-to-pod communication issues
        
        Based on the evidence collected, identify potential networking issues 
        and determine the likelihood that networking is causing the reported symptoms.
        """
    
    def collect_network_evidence(self, task: Task) -> List[Evidence]:
        """
        Collect network-related evidence from the Kubernetes cluster
        
        Args:
            task: The investigation task
            
        Returns:
            List[Evidence]: Collected evidence items
        """
        logger.info(f"Collecting network evidence for task: {task.description}")
        evidence = []
        
        # Collect service information
        services = self.service_client.list_services()
        evidence.append(Evidence(
            resource_type="Service",
            raw_data=services,
            analysis="Overview of services in the cluster"
        ))
        
        # Check for pod connectivity issues
        connectivity_issues = self.pod_client.check_pod_connectivity()
        evidence.append(Evidence(
            resource_type="PodConnectivity",
            raw_data=connectivity_issues,
            analysis="Pod connectivity check results"
        ))
        
        # Get network policies
        network_policies = self.network_policy_client.list_network_policies()
        evidence.append(Evidence(
            resource_type="NetworkPolicy",
            raw_data=network_policies,
            analysis="Network policies in the cluster"
        ))
        
        # Check specific service endpoints for task focus
        if "database" in task.description.lower():
            db_endpoints = self.service_client.get_service_endpoints("database", "default")
            evidence.append(Evidence(
                resource_type="ServiceEndpoints",
                raw_data=db_endpoints,
                analysis="Database service endpoint status"
            ))
            
            db_connectivity = self.pod_client.check_pod_connectivity(
                source_pod="backend-6f7b8d9c5e-fghij", 
                target_service="database"
            )
            evidence.append(Evidence(
                resource_type="TargetedConnectivity",
                raw_data=db_connectivity,
                analysis="Connectivity check from backend pod to database service"
            ))
        
        return evidence
    
    def analyze_evidence(self, evidence: List[Evidence], task: Task) -> Finding:
        """
        Analyze the collected evidence to produce findings
        
        Args:
            evidence: Collected evidence items
            task: The investigation task
            
        Returns:
            Finding: Analysis results
        """
        logger.info(f"Analyzing network evidence for task: {task.description}")
        
        template = self.system_prompt + """
        ## Task Description
        {task_description}
        
        ## Evidence Collected
        
        {evidence_json}
        
        ## Analysis Instructions
        
        Based on this evidence:
        1. Identify potential networking issues that could be causing the symptoms
        2. Determine the likelihood that networking is the root cause
        3. Analyze network policy configurations for potential issues
        4. Check for service connectivity problems
        5. Suggest specific areas for further network investigation
        
        Output your analysis in the following JSON format:
        ```json
        {{
          "analysis": "detailed analysis of the network evidence",
          "potential_issues": ["list of potential network issues identified"],
          "confidence": 0.0-1.0 (confidence that networking is causing the symptoms),
          "further_investigation": ["areas that need further investigation"]
        }}
        ```
        """
        
        # Convert evidence to dict format for JSON
        evidence_dicts = [e.to_dict() for e in evidence]
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(template)
        
        # Set up output parsing
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Run the analysis
        result = chain.invoke({
            "task_description": task.description,
            "evidence_json": json.dumps(evidence_dicts, indent=2)
        })
        
        # Create finding from result
        finding = Finding(
            agent_type="network",
            evidence=evidence,
            analysis=result.get("analysis", ""),
            confidence=result.get("confidence", 0.0),
            potential_issues=result.get("potential_issues", [])
        )
        
        return finding
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and investigate network issues
        
        Args:
            state: Current investigation state
            
        Returns:
            Dict: Updated investigation state with network findings
        """
        logger.info("Network agent activated")
        
        # Extract task information from state
        investigation_phase = state.get("investigation_phase", "")
        current_hypothesis = state.get("current_hypothesis", {})
        
        # Create a task based on the current state
        task_description = f"Investigate network issues related to {current_hypothesis.get('focus', 'general symptoms')}"
        if "initial_symptoms" in state:
            task_description += f" with symptoms: {state['initial_symptoms']}"
            
        task = Task(
            description=task_description,
            type="network_investigation",
            priority="high" if current_hypothesis.get("type") == "network" else "medium"
        )
        
        # Collect evidence
        evidence = self.collect_network_evidence(task)
        
        # Analyze evidence
        finding = self.analyze_evidence(evidence, task)
        
        # Update the state with new evidence and findings
        updated_evidence = state.get("evidence", []) + [e.to_dict() for e in evidence]
        updated_findings = state.get("findings", {})
        updated_findings["network"] = finding.to_dict()
        
        # Create confidence scores for network categories
        network_confidence = finding.confidence
        confidence_scores = state.get("confidence_scores", {})
        
        # Update confidence scores
        if network_confidence > 0.7:
            # If high confidence, specify subcategories
            confidence_scores["network"] = network_confidence
            
            # Check if specific issues have been identified
            for issue in finding.potential_issues:
                if "policy" in issue.lower():
                    confidence_scores["network_policy"] = network_confidence
                elif "service" in issue.lower():
                    confidence_scores["service_connectivity"] = network_confidence
                elif "dns" in issue.lower():
                    confidence_scores["dns_resolution"] = network_confidence
        else:
            # Just update general network confidence
            confidence_scores["network"] = network_confidence
        
        return {
            "evidence": updated_evidence,
            "findings": updated_findings,
            "confidence_scores": confidence_scores,
            # Preserve other state elements
            "investigation_phase": state.get("investigation_phase", ""),
            "initial_symptoms": state.get("initial_symptoms", ""),
            "current_hypothesis": state.get("current_hypothesis", {}),
            "specialist_agents_to_activate": state.get("specialist_agents_to_activate", []),
            "next_actions": state.get("next_actions", [])
        }

# Example of usage
if __name__ == "__main__":
    network_agent = NetworkAgent()
    
    # Sample state with hypothesis
    sample_state = {
        "investigation_phase": "hypothesis_testing",
        "initial_symptoms": """
        Several pods in the production namespace keep restarting with CrashLoopBackOff status.
        The application logs show connection timeouts when trying to reach the database service.
        This started approximately 30 minutes after a network policy update was applied.
        """,
        "current_hypothesis": {
            "focus": "database connectivity issues",
            "type": "network"
        }
    }
    
    # Process the state
    result = network_agent(sample_state)
    
    # Print the result
    print(json.dumps(result, indent=2)) 