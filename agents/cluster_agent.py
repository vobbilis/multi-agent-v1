"""
Cluster Specialist Agent for Kubernetes Root Cause Analysis
"""
import json
import logging
import os
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI

# Import models (these would be defined elsewhere in a real implementation)
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

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClusterClient:
    """Client for interacting with Kubernetes cluster components"""
    
    def __init__(self):
        """Initialize the cluster client with configuration from environment variables"""
        self.namespace = os.environ.get("INVESTIGATION_NAMESPACE", "default")
        self.kubeconfig = os.environ.get("KUBECONFIG", "")
        self.kubectl_path = os.environ.get("KUBECTL_PATH", "kubectl")
        self.mock_mode = os.environ.get("MOCK_K8S", "false").lower() == "true"
        
    def _run_kubectl(self, cmd: List[str]) -> Tuple[str, bool]:
        """
        Run a kubectl command and return the output
        
        Args:
            cmd: The kubectl command arguments as a list
            
        Returns:
            Tuple[str, bool]: Output and success status
        """
        if self.mock_mode:
            logger.info(f"MOCK: kubectl {' '.join(cmd)}")
            return self._mock_kubectl_response(cmd), True
            
        try:
            full_cmd = [self.kubectl_path] + cmd
            if self.kubeconfig:
                full_cmd = full_cmd + ["--kubeconfig", self.kubeconfig]
                
            logger.info(f"Running: {' '.join(full_cmd)}")
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Command failed with exit code {result.returncode}: {result.stderr}")
                return result.stderr, False
            
            return result.stdout, True
        except Exception as e:
            logger.error(f"Error executing kubectl command: {e}")
            return str(e), False
            
    def _mock_kubectl_response(self, cmd: List[str]) -> str:
        """
        Generate mock response for kubectl commands in test environments
        
        Args:
            cmd: The kubectl command arguments as a list
            
        Returns:
            str: Mocked output
        """
        # Very basic mocking for common commands
        if cmd[0] == "get" and cmd[1] == "componentstatuses":
            return json.dumps({
                "kind": "ComponentStatusList",
                "apiVersion": "v1",
                "items": [
                    {
                        "kind": "ComponentStatus",
                        "apiVersion": "v1",
                        "metadata": {"name": "scheduler"},
                        "conditions": [{"type": "Healthy", "status": "True"}]
                    },
                    {
                        "kind": "ComponentStatus",
                        "apiVersion": "v1",
                        "metadata": {"name": "controller-manager"},
                        "conditions": [{"type": "Healthy", "status": "True"}]
                    },
                    {
                        "kind": "ComponentStatus",
                        "apiVersion": "v1",
                        "metadata": {"name": "etcd-0"},
                        "conditions": [{"type": "Healthy", "status": "True"}]
                    }
                ]
            })
        elif cmd[0] == "get" and cmd[1] == "nodes":
            return json.dumps({
                "kind": "NodeList",
                "apiVersion": "v1",
                "items": [
                    {
                        "kind": "Node",
                        "apiVersion": "v1",
                        "metadata": {
                            "name": "node-1",
                            "labels": {"node-role.kubernetes.io/control-plane": ""}
                        },
                        "status": {
                            "conditions": [
                                {"type": "Ready", "status": "True"}
                            ]
                        }
                    }
                ]
            })
        elif cmd[0] == "get" and cmd[1] == "--raw" and cmd[2] == "/healthz":
            return "ok"
        elif cmd[0] == "get" and cmd[1] == "--raw" and cmd[2] == "/healthz/etcd":
            return "ok"
        elif cmd[0] == "top" and cmd[1] == "nodes":
            return "node-1   250m   12%    1.5Gi    20%"
        elif cmd[0] == "top" and cmd[1] == "pods":
            return "pod-1    100m    512Mi   namespace"
        elif cmd[0] == "describe" and cmd[1] == "pod":
            return "Name:       pod-1\nNamespace:  default\nStatus:     Running\nEvents:     <none>"
        
        # Default fallback for unimplemented commands
        return json.dumps({"kind": "List", "apiVersion": "v1", "items": []})
    
    def get_control_plane_status(self) -> Dict[str, Any]:
        """
        Get status of control plane components
        
        Returns:
            Dict: Status of control plane components
        """
        control_plane_data = {}
        
        # Get component statuses
        output, success = self._run_kubectl(["get", "componentstatuses", "-o", "json"])
        if success:
            try:
                control_plane_data["componentstatuses"] = json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse component statuses output")
        
        # Get nodes with control plane roles
        output, success = self._run_kubectl(["get", "nodes", "--selector", "node-role.kubernetes.io/control-plane=", "-o", "json"])
        if success:
            try:
                control_plane_data["control_plane_nodes"] = json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse control plane nodes output")
                
        # Check API server health
        output, success = self._run_kubectl(["get", "--raw", "/healthz"])
        control_plane_data["api_health"] = {"status": output.strip(), "healthy": success and "ok" in output.lower()}
        
        # Get etcd health if possible
        output, success = self._run_kubectl(["get", "--raw", "/healthz/etcd"])
        control_plane_data["etcd_health"] = {"status": output.strip(), "healthy": success and "ok" in output.lower()}
        
        return control_plane_data
    
    def get_cluster_events(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recent events from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter events
            
        Returns:
            Dict: Recent events
        """
        cmd = ["get", "events", "--sort-by=.lastTimestamp"]
        if namespace:
            cmd.extend(["-n", namespace])
        cmd.extend(["-o", "json"])
        
        output, success = self._run_kubectl(cmd)
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse events output")
        
        return {"items": []}
    
    def get_pods(self, namespace: Optional[str] = None, selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Get pods from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter pods
            selector: Optional label selector
            
        Returns:
            Dict: Pod list
        """
        cmd = ["get", "pods"]
        if namespace:
            cmd.extend(["-n", namespace])
        if selector:
            cmd.extend(["--selector", selector])
        cmd.extend(["-o", "json"])
        
        output, success = self._run_kubectl(cmd)
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse pods output")
        
        return {"items": []}
    
    def get_pod_details(self, pod_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific pod
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            
        Returns:
            Dict: Pod details
        """
        ns = namespace or self.namespace
        output, success = self._run_kubectl(["get", "pod", pod_name, "-n", ns, "-o", "json"])
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse pod {pod_name} output")
        
        return {}
    
    def get_services(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get services from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter services
            
        Returns:
            Dict: Service list
        """
        cmd = ["get", "services"]
        if namespace:
            cmd.extend(["-n", namespace])
        cmd.extend(["-o", "json"])
        
        output, success = self._run_kubectl(cmd)
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse services output")
        
        return {"items": []}
    
    def get_ingresses(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ingresses from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter ingresses
            
        Returns:
            Dict: Ingress list
        """
        cmd = ["get", "ingresses"]
        if namespace:
            cmd.extend(["-n", namespace])
        cmd.extend(["-o", "json"])
        
        output, success = self._run_kubectl(cmd)
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse ingresses output")
        
        return {"items": []}
    
    def get_workloads(self, namespace: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get various workload resources from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter workloads
            
        Returns:
            Dict: Dictionary of workload types and their lists
        """
        workload_types = ["deployments", "replicasets", "statefulsets", "daemonsets", "jobs", "cronjobs"]
        result = {}
        
        for workload_type in workload_types:
            cmd = ["get", workload_type]
            if namespace:
                cmd.extend(["-n", namespace])
            cmd.extend(["-o", "json"])
            
            output, success = self._run_kubectl(cmd)
            if success:
                try:
                    result[workload_type] = json.loads(output)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse {workload_type} output")
                    result[workload_type] = {"items": []}
            else:
                result[workload_type] = {"items": []}
        
        return result
    
    def get_config_objects(self, namespace: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get various configuration objects from the cluster or specified namespace
        
        Args:
            namespace: Optional namespace to filter objects
            
        Returns:
            Dict: Dictionary of config object types and their lists
        """
        config_types = ["configmaps", "secrets", "resourcequotas", "limitranges", "horizontalpodautoscalers"]
        result = {}
        
        for config_type in config_types:
            cmd = ["get", config_type]
            if namespace:
                cmd.extend(["-n", namespace])
            cmd.extend(["-o", "json"])
            
            output, success = self._run_kubectl(cmd)
            if success:
                try:
                    result[config_type] = json.loads(output)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse {config_type} output")
                    result[config_type] = {"items": []}
            else:
                result[config_type] = {"items": []}
        
        return result
    
    def get_node_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for all nodes
        
        Returns:
            Dict: Node metrics
        """
        output, success = self._run_kubectl(["top", "nodes", "--no-headers"])
        if not success:
            return {"nodes": []}
        
        # Parse the output
        nodes_metrics = []
        lines = output.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 5:
                node_name = parts[0]
                cpu = parts[1]
                cpu_percent = parts[2]
                memory = parts[3]
                memory_percent = parts[4]
                
                nodes_metrics.append({
                    "name": node_name,
                    "cpu": cpu,
                    "cpu_percent": cpu_percent,
                    "memory": memory,
                    "memory_percent": memory_percent
                })
        
        return {"nodes": nodes_metrics}
    
    def get_pod_metrics(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for pods
        
        Args:
            namespace: Optional namespace to filter pods
            
        Returns:
            Dict: Pod metrics
        """
        cmd = ["top", "pods", "--no-headers"]
        if namespace:
            cmd.extend(["-n", namespace])
            
        output, success = self._run_kubectl(cmd)
        if not success:
            return {"pods": []}
        
        # Parse the output
        pods_metrics = []
        lines = output.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 5:
                pod_name = parts[0]
                cpu = parts[1]
                memory = parts[2]
                
                pods_metrics.append({
                    "name": pod_name,
                    "namespace": namespace or "unknown",
                    "cpu": cpu,
                    "memory": memory
                })
        
        return {"pods": pods_metrics}
        
    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Run kubectl describe on a pod
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod (optional)
            
        Returns:
            str: Output of kubectl describe
        """
        cmd = ["describe", "pod", pod_name]
        if namespace:
            cmd.extend(["-n", namespace])
            
        output, success = self._run_kubectl(cmd)
        if success:
            return output
        return ""
        
    def get_logs(self, pod_name: str, container: Optional[str] = None, 
               namespace: Optional[str] = None, tail: int = 100) -> str:
        """
        Get logs from a pod
        
        Args:
            pod_name: Name of the pod
            container: Container name (optional)
            namespace: Namespace of the pod (optional)
            tail: Number of lines to retrieve
            
        Returns:
            str: Pod logs
        """
        cmd = ["logs", pod_name]
        if container:
            cmd.extend(["-c", container])
        if namespace:
            cmd.extend(["-n", namespace])
        cmd.extend(["--tail", str(tail)])
        
        output, success = self._run_kubectl(cmd)
        if success:
            return output
        return ""

class ClusterAgent:
    """
    Cluster specialist agent for the Kubernetes root cause analysis system.
    This agent focuses on analyzing the state of Kubernetes control plane components
    and cluster objects to identify issues with the core infrastructure.
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0):
        """
        Initialize the cluster agent with LLM settings and cluster client
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.cluster_client = ClusterClient()
        
        self.system_prompt = """
        You are a Kubernetes cluster specialist agent in a root cause analysis system.
        Your job is to analyze the state of Kubernetes control plane components and
        cluster objects to identify issues with the core infrastructure.
        
        You need to:
        1. Check the health of control plane components (API Server, Scheduler, Controller Manager, ETCD)
        2. Analyze the state of Kubernetes objects (Pods, Services, Deployments, etc.)
        3. Identify any issues with the control plane or cluster objects
        4. Look for correlations between cluster state and reported symptoms
        5. Determine if there are architectural issues or misconfigurations
        
        Based on the evidence collected, identify potential cluster-level issues
        and determine the likelihood that these issues are causing the reported symptoms.
        """
    
    def collect_cluster_evidence(self, task: Task) -> List[Evidence]:
        """
        Collect cluster-related evidence from the Kubernetes cluster
        
        Args:
            task: The investigation task
            
        Returns:
            List[Evidence]: Collected evidence items
        """
        logger.info(f"Collecting cluster evidence for task: {task.description}")
        evidence = []
        namespace = os.environ.get("INVESTIGATION_NAMESPACE", "default")
        
        # Get control plane status
        control_plane_status = self.cluster_client.get_control_plane_status()
        evidence.append(Evidence(
            resource_type="ControlPlaneStatus",
            raw_data=control_plane_status,
            analysis="Status of Kubernetes control plane components"
        ))
        
        # Get cluster events
        cluster_events = self.cluster_client.get_cluster_events()
        evidence.append(Evidence(
            resource_type="ClusterEvents",
            raw_data=cluster_events,
            analysis="Recent events from across the cluster"
        ))
        
        # Get namespace events if namespace is specified
        if namespace != "default":
            namespace_events = self.cluster_client.get_cluster_events(namespace)
            evidence.append(Evidence(
                resource_type="NamespaceEvents",
                raw_data=namespace_events,
                analysis=f"Recent events from the {namespace} namespace"
            ))
        
        # Get workloads
        workloads = self.cluster_client.get_workloads(namespace)
        evidence.append(Evidence(
            resource_type="Workloads",
            raw_data=workloads,
            analysis=f"Workload resources in the {namespace} namespace"
        ))
        
        # Get configuration objects
        config_objects = self.cluster_client.get_config_objects(namespace)
        evidence.append(Evidence(
            resource_type="ConfigObjects",
            raw_data=config_objects,
            analysis=f"Configuration objects in the {namespace} namespace"
        ))
        
        # Get pods with issues
        pods = self.cluster_client.get_pods(namespace)
        pod_issues = self._identify_pod_issues(pods)
        if pod_issues["problematic_pods"]:
            evidence.append(Evidence(
                resource_type="PodIssues",
                raw_data=pod_issues,
                analysis="Pods with potential issues"
            ))
            
            # Get detailed information about problematic pods
            for pod in pod_issues["problematic_pods"][:5]:  # Limit to first 5 problematic pods
                pod_name = pod.get("name")
                pod_details = self.cluster_client.get_pod_details(pod_name, namespace)
                pod_describe = self.cluster_client.describe_pod(pod_name, namespace)
                
                evidence.append(Evidence(
                    resource_type="ProblemPodDetails",
                    raw_data={"pod_json": pod_details, "pod_describe": pod_describe, "pod_name": pod_name},
                    analysis=f"Detailed information about problematic pod {pod_name}"
                ))
        
        # Get services
        services = self.cluster_client.get_services(namespace)
        evidence.append(Evidence(
            resource_type="Services",
            raw_data=services,
            analysis=f"Services in the {namespace} namespace"
        ))
        
        # Get ingresses
        ingresses = self.cluster_client.get_ingresses(namespace)
        evidence.append(Evidence(
            resource_type="Ingresses",
            raw_data=ingresses,
            analysis=f"Ingresses in the {namespace} namespace"
        ))
        
        return evidence
    
    def _identify_pod_issues(self, pods_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pods to identify those with issues
        
        Args:
            pods_data: Pod data as returned by the API
            
        Returns:
            Dict: Analysis of problematic pods
        """
        problematic_pods = []
        
        for pod in pods_data.get("items", []):
            issues = []
            pod_name = pod.get("metadata", {}).get("name", "unknown")
            phase = pod.get("status", {}).get("phase", "")
            
            # Check pod phase
            if phase != "Running" and phase != "Succeeded":
                issues.append(f"Pod in {phase} phase")
            
            # Check container statuses
            for container_status in pod.get("status", {}).get("containerStatuses", []):
                if not container_status.get("ready", False):
                    container_name = container_status.get("name", "unknown")
                    issues.append(f"Container {container_name} not ready")
                
                restart_count = container_status.get("restartCount", 0)
                if restart_count > 5:
                    container_name = container_status.get("name", "unknown")
                    issues.append(f"Container {container_name} has restarted {restart_count} times")
                
                # Check waiting reason
                if "waiting" in container_status.get("state", {}):
                    waiting = container_status["state"]["waiting"]
                    reason = waiting.get("reason", "")
                    message = waiting.get("message", "")
                    
                    if reason:
                        container_name = container_status.get("name", "unknown")
                        issues.append(f"Container {container_name} waiting: {reason} - {message}")
            
            # Check pod conditions
            for condition in pod.get("status", {}).get("conditions", []):
                if condition.get("type") == "Ready" and condition.get("status") != "True":
                    issues.append(f"Pod not ready: {condition.get('reason', '')} - {condition.get('message', '')}")
            
            if issues:
                problematic_pods.append({
                    "name": pod_name,
                    "namespace": pod.get("metadata", {}).get("namespace", "default"),
                    "phase": phase,
                    "issues": issues
                })
        
        return {
            "problematic_pods": problematic_pods,
            "total_pods": len(pods_data.get("items", [])),
            "problem_count": len(problematic_pods)
        }
    
    def analyze_evidence(self, evidence: List[Evidence], task: Task) -> Finding:
        """
        Analyze the collected cluster evidence to produce findings
        
        Args:
            evidence: Collected evidence items
            task: The investigation task
            
        Returns:
            Finding: Analysis results
        """
        logger.info(f"Analyzing cluster evidence for task: {task.description}")
        
        template = self.system_prompt + """
        ## Task Description
        {task_description}
        
        ## Evidence Collected
        
        {evidence_json}
        
        ## Analysis Instructions
        
        Based on this cluster evidence:
        1. Identify any issues with control plane components
        2. Analyze the state of cluster objects (Pods, Services, etc.)
        3. Look for misconfigurations or architectural issues
        4. Correlate observed issues with reported symptoms
        5. Determine if there are resource constraints or scheduling issues
        
        Output your analysis in the following JSON format:
        ```json
        {{
          "analysis": "detailed analysis of the cluster evidence",
          "potential_issues": ["list of potential cluster issues identified"],
          "confidence": 0.0-1.0 (confidence that cluster issues are causing the symptoms),
          "further_investigation": ["areas that need further investigation"],
          "control_plane_health": "assessment of control plane health"
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
            agent_type="cluster",
            evidence=evidence,
            analysis=result.get("analysis", ""),
            confidence=result.get("confidence", 0.0),
            potential_issues=result.get("potential_issues", [])
        )
        
        return finding
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and investigate cluster issues
        
        Args:
            state: Current investigation state
            
        Returns:
            Dict: Updated investigation state with cluster findings
        """
        logger.info("Cluster agent activated")
        
        # Extract task information from state
        investigation_phase = state.get("investigation_phase", "")
        current_hypothesis = state.get("current_hypothesis", {})
        symptoms = state.get("initial_symptoms", "")
        
        # Create a task based on the current state
        task_description = f"Investigate Kubernetes cluster components and objects related to {current_hypothesis.get('focus', 'general symptoms')}"
        if symptoms:
            task_description += f" with symptoms: {symptoms}"
            
        task = Task(
            description=task_description,
            type="cluster_investigation",
            priority="high" if "control plane" in current_hypothesis.get("focus", "").lower() else "medium"
        )
        
        # Collect evidence
        evidence = self.collect_cluster_evidence(task)
        
        # Analyze evidence
        finding = self.analyze_evidence(evidence, task)
        
        # Update the state with new evidence and findings
        updated_evidence = state.get("evidence", []) + [e.to_dict() for e in evidence]
        updated_findings = state.get("findings", {})
        updated_findings["cluster"] = finding.to_dict()
        
        # Create confidence scores for cluster categories
        cluster_confidence = finding.confidence
        confidence_scores = state.get("confidence_scores", {})
        
        # Update confidence scores
        if cluster_confidence > 0.7:
            # If high confidence, specify subcategories
            confidence_scores["cluster"] = cluster_confidence
            
            # Check if specific issues have been identified
            for issue in finding.potential_issues:
                if "control plane" in issue.lower() or "api server" in issue.lower() or "etcd" in issue.lower():
                    confidence_scores["control_plane"] = cluster_confidence
                elif "pod" in issue.lower() or "deployment" in issue.lower():
                    confidence_scores["workloads"] = cluster_confidence
                elif "service" in issue.lower() or "ingress" in issue.lower():
                    confidence_scores["networking_objects"] = cluster_confidence
                elif "config" in issue.lower() or "secret" in issue.lower():
                    confidence_scores["configuration"] = cluster_confidence
                elif "node" in issue.lower() or "schedule" in issue.lower():
                    confidence_scores["nodes"] = cluster_confidence
        else:
            # Just update general cluster confidence
            confidence_scores["cluster"] = cluster_confidence
        
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
    # Configure sample environment variables
    os.environ["INVESTIGATION_NAMESPACE"] = "default"
    
    cluster_agent = ClusterAgent()
    
    # Sample state with hypothesis
    sample_state = {
        "investigation_phase": "hypothesis_testing",
        "initial_symptoms": """
        Several pods in the production namespace keep restarting with CrashLoopBackOff status.
        The application logs show connection timeouts when trying to reach the database service.
        Some nodes are reporting disk pressure.
        """,
        "current_hypothesis": {
            "focus": "control plane issues",
            "type": "cluster"
        }
    }
    
    # Process the state
    result = cluster_agent(sample_state)
    
    # Print the result
    print(json.dumps(result, indent=2)) 