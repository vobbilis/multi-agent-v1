"""
Logs Specialist Agent for Kubernetes Root Cause Analysis
"""
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI

# Models
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

class LogsClient:
    """Client for collecting and analyzing logs from Kubernetes pods"""
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize the logs client
        
        Args:
            use_mock: Whether to use mock data instead of actual K8s client
        """
        self.use_mock = use_mock
        
        # Initialize Kubernetes client if not using mock
        self.core_v1 = None
        
        if not self.use_mock:
            try:
                # Import kubernetes client - we do this dynamically to avoid
                # requiring the package if only using mock mode
                from kubernetes import client, config
                
                try:
                    # Try to load from default kubeconfig
                    config.load_kube_config()
                    self.core_v1 = client.CoreV1Api()
                    logger.info("Successfully initialized Kubernetes client from kubeconfig")
                except Exception as e:
                    # If that fails, try in-cluster config (for running in a pod)
                    try:
                        config.load_incluster_config()
                        self.core_v1 = client.CoreV1Api()
                        logger.info("Successfully initialized Kubernetes client from in-cluster config")
                    except Exception as e2:
                        logger.error(f"Failed to initialize Kubernetes client: {e2}")
                        logger.warning("Falling back to mock mode")
                        self.use_mock = True
            except ImportError:
                logger.error("Kubernetes client module not installed, falling back to mock mode")
                self.use_mock = True
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", container_name: Optional[str] = None, 
                    tail_lines: int = 100, previous: bool = False) -> str:
        """
        Get logs from a specific pod
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            container_name: Name of the container (if pod has multiple containers)
            tail_lines: Number of lines to retrieve from the end of the logs
            previous: Whether to get logs from previous container instance
            
        Returns:
            String containing the pod logs
        """
        if self.use_mock:
            return self._mock_pod_logs(pod_name, namespace, container_name)
        
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail_lines,
                previous=previous
            )
            return logs
        except Exception as e:
            logger.error(f"Error getting logs for pod {pod_name} in namespace {namespace}: {e}")
            return f"Error: {str(e)}"
    
    def _mock_pod_logs(self, pod_name: str, namespace: str, container_name: Optional[str] = None) -> str:
        """Provide mock logs for testing"""
        # Common error patterns for different types of pods
        mock_logs = {
            "database": (
                "2023-04-15T10:00:00.000Z ERROR: could not connect to database\n"
                "2023-04-15T10:00:05.000Z ERROR: connection refused\n"
                "2023-04-15T10:00:10.000Z ERROR: max connections reached\n"
                "2023-04-15T10:01:00.000Z WARN: slow query detected, execution time: 5.2s\n"
                "2023-04-15T10:02:00.000Z ERROR: out of memory\n"
                "2023-04-15T10:02:05.000Z ERROR: terminating connection due to administrator command\n"
            ),
            "web": (
                "2023-04-15T10:00:00.000Z INFO: Server starting on port 8080\n"
                "2023-04-15T10:00:05.000Z ERROR: Failed to connect to backend service: connection timeout\n"
                "2023-04-15T10:00:10.000Z WARN: High response time detected: 2500ms\n"
                "2023-04-15T10:01:00.000Z ERROR: 500 Internal Server Error: /api/users\n"
                "2023-04-15T10:02:00.000Z ERROR: Out of memory error\n"
                "2023-04-15T10:02:05.000Z INFO: Graceful shutdown initiated\n"
            ),
            "api": (
                "2023-04-15T10:00:00.000Z INFO: API server started\n"
                "2023-04-15T10:00:05.000Z WARN: Rate limit exceeded for client 192.168.1.100\n"
                "2023-04-15T10:00:10.000Z ERROR: Database connection pool exhausted\n"
                "2023-04-15T10:01:00.000Z ERROR: Unable to process request: timeout waiting for resource\n"
                "2023-04-15T10:02:00.000Z ERROR: Circuit breaker opened for dependency: auth-service\n"
                "2023-04-15T10:02:05.000Z INFO: Readiness probe failed, service not yet ready\n"
            ),
            "cache": (
                "2023-04-15T10:00:00.000Z INFO: Cache service started\n"
                "2023-04-15T10:00:05.000Z WARN: Memory usage at 85%\n"
                "2023-04-15T10:00:10.000Z ERROR: Eviction of keys started due to memory pressure\n"
                "2023-04-15T10:01:00.000Z ERROR: Out of memory, unable to allocate new entries\n"
                "2023-04-15T10:02:00.000Z ERROR: Connection to master lost\n"
                "2023-04-15T10:02:05.000Z WARN: Operating in degraded mode\n"
            ),
            "default": (
                "2023-04-15T10:00:00.000Z INFO: Pod started\n"
                "2023-04-15T10:00:05.000Z WARN: Resource usage high\n"
                "2023-04-15T10:00:10.000Z ERROR: Connection failed to dependent service\n"
                "2023-04-15T10:01:00.000Z ERROR: Unexpected error occurred\n"
                "2023-04-15T10:02:00.000Z ERROR: Process terminated with exit code 1\n"
                "2023-04-15T10:02:05.000Z INFO: Restarting container\n"
            ),
        }
        
        # Try to match the pod name to a mock log type
        log_type = "default"
        for key in mock_logs.keys():
            if key in pod_name.lower():
                log_type = key
                break
        
        return mock_logs[log_type]
    
    def get_pod_list(self, namespace: str = "", label_selector: str = "") -> List[Dict[str, Any]]:
        """
        Get list of pods to investigate
        
        Args:
            namespace: Namespace to filter by
            label_selector: Label selector to filter by
            
        Returns:
            List of pod dictionaries
        """
        if self.use_mock:
            return self._mock_pod_list(namespace, label_selector)
        
        try:
            if namespace:
                # Get pods in a specific namespace
                pod_list = self.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector or None
                )
            else:
                # Get pods across all namespaces
                pod_list = self.core_v1.list_pod_for_all_namespaces(
                    label_selector=label_selector or None
                )
            
            # Convert to simplified dictionary format
            pods = []
            for pod in pod_list.items:
                pod_dict = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "containers": [container.name for container in pod.spec.containers],
                    "node": pod.spec.node_name if pod.spec.node_name else None,
                    "labels": pod.metadata.labels if pod.metadata.labels else {},
                    "creation_time": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                }
                pods.append(pod_dict)
            
            return pods
        except Exception as e:
            logger.error(f"Error getting pod list: {e}")
            return []
    
    def _mock_pod_list(self, namespace: str, label_selector: str) -> List[Dict[str, Any]]:
        """Provide mock pod list for testing"""
        mock_pods = [
            {
                "name": "frontend-5d8b9c7f68-abcde",
                "namespace": "default",
                "status": "Running",
                "containers": ["frontend"],
                "node": "worker-1",
                "labels": {"app": "frontend", "pod-template-hash": "5d8b9c7f68"},
                "creation_time": "2023-04-15T09:00:00Z"
            },
            {
                "name": "backend-6f7b8d9c5e-fghij",
                "namespace": "default",
                "status": "Running",
                "containers": ["backend"],
                "node": "worker-2",
                "labels": {"app": "backend", "pod-template-hash": "6f7b8d9c5e"},
                "creation_time": "2023-04-15T09:00:00Z"
            },
            {
                "name": "database-7c8d9e0f1a-klmno",
                "namespace": "default",
                "status": "CrashLoopBackOff",
                "containers": ["database"],
                "node": "worker-1",
                "labels": {"app": "database", "pod-template-hash": "7c8d9e0f1a"},
                "creation_time": "2023-04-15T09:00:00Z"
            },
            {
                "name": "cache-8d9e0f1b2c-pqrst",
                "namespace": "default",
                "status": "Running",
                "containers": ["cache", "metrics-sidecar"],
                "node": "worker-2",
                "labels": {"app": "cache", "pod-template-hash": "8d9e0f1b2c"},
                "creation_time": "2023-04-15T09:00:00Z"
            },
            {
                "name": "api-9e0f1b2c3d-uvwxy",
                "namespace": "api",
                "status": "Error",
                "containers": ["api"],
                "node": "worker-1",
                "labels": {"app": "api", "pod-template-hash": "9e0f1b2c3d"},
                "creation_time": "2023-04-15T09:00:00Z"
            }
        ]
        
        # Filter by namespace if provided
        if namespace:
            mock_pods = [pod for pod in mock_pods if pod["namespace"] == namespace]
        
        # Filter by labels if provided
        if label_selector:
            # Simple label selector parsing
            if "=" in label_selector:
                key, value = label_selector.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                mock_pods = [pod for pod in mock_pods if pod["labels"].get(key) == value]
        
        return mock_pods

class LogsAgent:
    """
    Logs specialist agent for the Kubernetes root cause analysis system.
    This agent focuses on analyzing logs from pods to identify:
    - Error patterns
    - Exceptions
    - Warnings
    - Connection issues
    - Resource constraints
    - Application-specific errors
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0, use_mock: bool = False):
        """
        Initialize the logs agent with LLM settings
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
            use_mock: Whether to use mock data
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.logs_client = LogsClient(use_mock=use_mock)
        
        self.system_prompt = """
        You are a Kubernetes logs specialist agent in a root cause analysis system.
        Your job is to analyze logs from pods to identify errors and issues.
        
        You need to:
        1. Identify error patterns in logs
        2. Detect application exceptions
        3. Recognize resource constraint indicators
        4. Find connection issues between services
        5. Spot configuration problems
        
        Based on the log analysis, identify potential issues and their likely causes.
        Look for patterns that may indicate the root cause of the reported symptoms.
        """
    
    def collect_logs_evidence(self, task: Task) -> List[Evidence]:
        """
        Collect logs-related evidence from the Kubernetes cluster
        
        Args:
            task: The investigation task
            
        Returns:
            List[Evidence]: Collected evidence items
        """
        logger.info(f"Collecting logs evidence for task: {task.description}")
        evidence = []
        
        # Extract pod name and namespace if present in the task description
        pod_name_match = re.search(r'pod[s]?\s+([a-zA-Z0-9-]+)', task.description)
        namespace_match = re.search(r'namespace[s]?\s+([a-zA-Z0-9-]+)', task.description)
        
        pod_name = pod_name_match.group(1) if pod_name_match else None
        namespace = namespace_match.group(1) if namespace_match else "default"
        
        # If pod name is explicitly mentioned, get logs for that pod
        if pod_name:
            logs = self.logs_client.get_pod_logs(pod_name, namespace)
            evidence.append(Evidence(
                resource_type="PodLogs",
                raw_data=logs,
                analysis=f"Logs from pod {pod_name} in namespace {namespace}"
            ))
            
            # Also get logs from previous container if it's restarting
            logs_previous = self.logs_client.get_pod_logs(pod_name, namespace, previous=True)
            if logs_previous and logs_previous != "Error":
                evidence.append(Evidence(
                    resource_type="PreviousPodLogs",
                    raw_data=logs_previous,
                    analysis=f"Logs from previous instance of pod {pod_name} in namespace {namespace}"
                ))
        else:
            # Otherwise get a list of pods and collect logs from pods with issues
            pods = self.logs_client.get_pod_list(namespace)
            problematic_pods = [pod for pod in pods if pod["status"] not in ["Running", "Succeeded"]]
            
            # If there are no problematic pods, check a sample of running pods
            if not problematic_pods and pods:
                sample_pods = pods[:3]  # Take up to 3 pods for analysis
                for pod in sample_pods:
                    logs = self.logs_client.get_pod_logs(pod["name"], pod["namespace"])
                    evidence.append(Evidence(
                        resource_type="PodLogs",
                        raw_data=logs,
                        analysis=f"Logs from pod {pod['name']} in namespace {pod['namespace']}"
                    ))
            else:
                # Focus on problematic pods
                for pod in problematic_pods:
                    logs = self.logs_client.get_pod_logs(pod["name"], pod["namespace"])
                    evidence.append(Evidence(
                        resource_type="PodLogs",
                        raw_data=logs,
                        analysis=f"Logs from problematic pod {pod['name']} in namespace {pod['namespace']} with status {pod['status']}"
                    ))
                    
                    # Also get logs from previous container if it's restarting
                    logs_previous = self.logs_client.get_pod_logs(pod["name"], pod["namespace"], previous=True)
                    if logs_previous and logs_previous != "Error":
                        evidence.append(Evidence(
                            resource_type="PreviousPodLogs",
                            raw_data=logs_previous,
                            analysis=f"Logs from previous instance of pod {pod['name']} in namespace {pod['namespace']}"
                        ))
        
        return evidence
    
    def analyze_evidence(self, evidence: List[Evidence], task: Task) -> Finding:
        """
        Analyze the collected log evidence to produce findings
        
        Args:
            evidence: Collected evidence items
            task: The investigation task
            
        Returns:
            Finding: Analysis results
        """
        logger.info(f"Analyzing logs evidence for task: {task.description}")
        
        # Build the analysis prompt
        template = self.system_prompt + """
        ## Task Description
        {task_description}
        
        ## Log Evidence
        {log_evidence}
        
        ## Your Task
        Analyze these logs to identify patterns, errors, and issues that might be related to the task.
        Look for error messages, exceptions, warnings, and other indicators of problems.
        Pay special attention to:
        - Exceptions and stack traces
        - Resource constraint messages (OOM, CPU throttling)
        - Connection errors and timeouts
        - Authentication and authorization issues
        - Configuration problems
        
        ## Output Format
        Provide your analysis in the following JSON format:
        ```json
        {{
          "analysis": "Overall analysis of the logs and what they indicate",
          "confidence": "Float between 0.0 and 1.0 indicating confidence in the analysis",
          "potential_issues": ["List of potential issues identified from the logs"],
          "error_patterns": [
            {{
              "pattern": "The error pattern observed",
              "frequency": "How often it appears",
              "severity": "High/Medium/Low",
              "description": "What this error pattern indicates"
            }}
          ],
          "related_components": ["List of related components or services mentioned in logs"]
        }}
        ```
        """
        
        # Format the log evidence for the prompt
        log_evidence_str = ""
        for i, ev in enumerate(evidence):
            # Limit log size to avoid overwhelming the LLM
            raw_data = ev.raw_data
            if isinstance(raw_data, str) and len(raw_data) > 2000:
                raw_data = raw_data[:2000] + "... [truncated]"
                
            log_evidence_str += f"--- Log Evidence #{i+1}: {ev.analysis} ---\n{raw_data}\n\n"
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create parser for structured output
        parser = JsonOutputParser()
        
        # Create the chain
        chain = prompt | self.llm | parser
        
        # Execute the chain with parameters
        try:
            result = chain.invoke({
                "task_description": task.description,
                "log_evidence": log_evidence_str
            })
        except Exception as e:
            logger.error(f"Error analyzing logs evidence: {e}")
            result = {
                "analysis": f"Error analyzing logs: {str(e)}",
                "confidence": 0.1,
                "potential_issues": ["Error during log analysis"],
                "error_patterns": [],
                "related_components": []
            }
        
        # Convert the result to a Finding
        return Finding(
            agent_type="logs",
            evidence=evidence,
            analysis=result.get("analysis", "No analysis available"),
            confidence=float(result.get("confidence", 0.5)),
            potential_issues=result.get("potential_issues", [])
        )
    
    def investigate(self, task: Task) -> Finding:
        """
        Perform a logs investigation for the given task
        
        Args:
            task: The investigation task
            
        Returns:
            Finding: Investigation results
        """
        logger.info(f"Starting logs investigation for task: {task.description}")
        
        # Collect evidence
        evidence = self.collect_logs_evidence(task)
        
        # If no evidence was collected, return a default finding
        if not evidence:
            return Finding(
                agent_type="logs",
                evidence=[],
                analysis="No log evidence was collected. Possible reasons include: pods not logging, "
                         "no pods matching the criteria, or log collection failures.",
                confidence=0.1,
                potential_issues=["Unable to collect logs", "Possible log collection permission issues"]
            )
        
        # Analyze the evidence
        return self.analyze_evidence(evidence, task) 