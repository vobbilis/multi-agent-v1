"""
Metrics Specialist Agent for Kubernetes Root Cause Analysis
"""
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Union

import requests
from kubernetes import client, config
from requests.auth import HTTPBasicAuth
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

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

class MetricsClient:
    """Client for collecting metrics from Kubernetes Metrics API and Prometheus"""
    
    def __init__(self):
        """Initialize the metrics client with configuration from environment variables"""
        # Metrics source configuration
        self.metrics_source = os.environ.get("METRICS_SOURCE", "kubernetes").lower()
        
        # Prometheus configuration
        self.prometheus_url = os.environ.get("PROMETHEUS_URL", "")
        self.prometheus_auth_type = os.environ.get("PROMETHEUS_AUTH_TYPE", "none").lower()
        self.prometheus_username = os.environ.get("PROMETHEUS_USERNAME", "")
        self.prometheus_password = os.environ.get("PROMETHEUS_PASSWORD", "")
        self.prometheus_oauth_client_id = os.environ.get("PROMETHEUS_OAUTH_CLIENT_ID", "")
        self.prometheus_oauth_client_secret = os.environ.get("PROMETHEUS_OAUTH_CLIENT_SECRET", "")
        self.prometheus_oauth_token_url = os.environ.get("PROMETHEUS_OAUTH_TOKEN_URL", "")
        
        # Initialize Kubernetes client if using K8s Metrics API
        self.core_v1 = None
        self.apps_v1 = None
        self.custom_api = None
        
        if self.metrics_source == "kubernetes":
            try:
                # Try to load from within cluster
                try:
                    config.load_incluster_config()
                    self.core_v1 = client.CoreV1Api()
                    self.apps_v1 = client.AppsV1Api()
                    self.custom_api = client.CustomObjectsApi()
                except config.ConfigException:
                    # Fall back to kubeconfig
                    try:
                        config.load_kube_config()
                        self.core_v1 = client.CoreV1Api()
                        self.apps_v1 = client.AppsV1Api()
                        self.custom_api = client.CustomObjectsApi()
                    except (config.ConfigException, FileNotFoundError):
                        # We're not in a K8s environment - use mock API for testing
                        logger.warning("Not in a Kubernetes environment. Using mock metrics API for testing.")
                        # Mock APIs will be used instead
            except Exception as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                # Mock APIs will be used instead
            
        # Setup OAuth session for Prometheus if configured
        self.oauth_session = None
        if self.metrics_source == "prometheus" and self.prometheus_auth_type == "oauth2":
            self._setup_oauth_session()
            
    def _setup_oauth_session(self):
        """Set up OAuth2 session for Prometheus authentication"""
        try:
            # Create OAuth2 client
            client_id = self.prometheus_oauth_client_id
            client_secret = self.prometheus_oauth_client_secret
            token_url = self.prometheus_oauth_token_url
            
            if not all([client_id, client_secret, token_url]):
                logger.error("OAuth2 credentials not properly configured")
                return
                
            # Set up client credentials flow
            oauth2_client = BackendApplicationClient(client_id=client_id)
            oauth2_session = OAuth2Session(client=oauth2_client)
            
            # Fetch token
            token = oauth2_session.fetch_token(
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret
            )
            
            self.oauth_session = oauth2_session
            logger.info("OAuth2 session established successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up OAuth2 session: {e}")
            self.oauth_session = None
    
    def get_node_metrics(self) -> Dict[str, Any]:
        """Get resource metrics for all nodes"""
        if self.metrics_source == "kubernetes":
            try:
                # Get metrics through Kubernetes Metrics API
                return self.custom_api.list_cluster_custom_object(
                    "metrics.k8s.io", "v1beta1", "nodes"
                )
            except Exception as e:
                logger.error(f"Error retrieving node metrics from K8s API: {e}")
                return {}
        elif self.metrics_source == "prometheus":
            try:
                # Construct PromQL query for node metrics
                queries = {
                    "cpu_usage": "sum by (node) (rate(node_cpu_seconds_total{mode!='idle'}[5m]))",
                    "memory_usage": "sum by (node) (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)",
                    "disk_usage": "sum by (node) (node_filesystem_size_bytes - node_filesystem_free_bytes)",
                    "network_receive": "sum by (node) (rate(node_network_receive_bytes_total[5m]))",
                    "network_transmit": "sum by (node) (rate(node_network_transmit_bytes_total[5m]))"
                }
                
                return self._execute_promql_queries(queries)
            except Exception as e:
                logger.error(f"Error retrieving node metrics from Prometheus: {e}")
                return {}
        
        return {}
    
    def get_pod_metrics(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get resource metrics for pods"""
        if self.metrics_source == "kubernetes":
            try:
                # Get metrics through Kubernetes Metrics API
                if namespace:
                    return self.custom_api.list_namespaced_custom_object(
                        "metrics.k8s.io", "v1beta1", namespace, "pods"
                    )
                else:
                    return self.custom_api.list_cluster_custom_object(
                        "metrics.k8s.io", "v1beta1", "pods"
                    )
            except Exception as e:
                logger.error(f"Error retrieving pod metrics from K8s API: {e}")
                return {}
        elif self.metrics_source == "prometheus":
            try:
                # Construct PromQL query for pod metrics
                namespace_filter = f',namespace="{namespace}"' if namespace else ''
                queries = {
                    "cpu_usage": f'sum by (pod, namespace) (rate(container_cpu_usage_seconds_total{{container!="", {namespace_filter}}}[5m]))',
                    "memory_usage": f'sum by (pod, namespace) (container_memory_working_set_bytes{{container!="", {namespace_filter}}})',
                    "network_receive": f'sum by (pod, namespace) (rate(container_network_receive_bytes_total{{{namespace_filter}}}[5m]))',
                    "network_transmit": f'sum by (pod, namespace) (rate(container_network_transmit_bytes_total{{{namespace_filter}}}[5m]))'
                }
                
                return self._execute_promql_queries(queries)
            except Exception as e:
                logger.error(f"Error retrieving pod metrics from Prometheus: {e}")
                return {}
                
        return {}
    
    def get_service_metrics(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics related to services"""
        if self.metrics_source == "prometheus":
            try:
                # Construct PromQL query for service metrics
                namespace_filter = f',namespace="{namespace}"' if namespace else ''
                queries = {
                    "request_rate": f'sum by (service, namespace) (rate(istio_requests_total{{{namespace_filter}}}[5m]))',
                    "error_rate": f'sum by (service, namespace) (rate(istio_requests_total{{response_code=~"5..", {namespace_filter}}}[5m]))',
                    "latency_p99": f'histogram_quantile(0.99, sum by (service, namespace, le) (rate(istio_request_duration_milliseconds_bucket{{{namespace_filter}}}[5m])))',
                    "latency_p50": f'histogram_quantile(0.50, sum by (service, namespace, le) (rate(istio_request_duration_milliseconds_bucket{{{namespace_filter}}}[5m])))'
                }
                
                return self._execute_promql_queries(queries)
            except Exception as e:
                logger.error(f"Error retrieving service metrics from Prometheus: {e}")
                return {}
        else:
            # Kubernetes metrics API doesn't provide service-level metrics
            logger.warning("Service metrics are only available when using Prometheus as the metrics source")
            return {}
    
    def get_database_metrics(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get database-specific metrics"""
        if self.metrics_source == "prometheus":
            try:
                # Construct PromQL queries for common database metrics
                namespace_filter = f',namespace="{namespace}"' if namespace else ''
                queries = {
                    # General database metrics (works for various DB types)
                    "connection_count": f'sum by (pod, namespace) (pg_stat_activity_count{{{namespace_filter}}})',
                    "active_queries": f'sum by (pod, namespace) (pg_stat_activity_count{{state="active", {namespace_filter}}})',
                    "query_duration": f'max by (pod, namespace) (pg_stat_activity_max_tx_duration{{{namespace_filter}}})',
                    
                    # MySQL/MariaDB metrics
                    "mysql_connections": f'mysql_global_status_threads_connected{{{namespace_filter}}}',
                    "mysql_queries": f'rate(mysql_global_status_queries{{{namespace_filter}}}[5m])',
                    
                    # MongoDB metrics
                    "mongodb_connections": f'mongodb_connections{{{namespace_filter}}}',
                    "mongodb_ops": f'rate(mongodb_op_counters_total{{{namespace_filter}}}[5m])'
                }
                
                return self._execute_promql_queries(queries)
            except Exception as e:
                logger.error(f"Error retrieving database metrics from Prometheus: {e}")
                return {}
        else:
            # Kubernetes metrics API doesn't provide database-specific metrics
            logger.warning("Database metrics are only available when using Prometheus as the metrics source")
            return {}
    
    def _execute_promql_queries(self, queries: Dict[str, str]) -> Dict[str, Any]:
        """Execute multiple PromQL queries and return the combined results"""
        if not self.prometheus_url:
            logger.error("Prometheus URL is not configured")
            return {}
            
        results = {}
        
        for metric_name, query in queries.items():
            try:
                response = self._query_prometheus(query)
                if response and 'data' in response and 'result' in response['data']:
                    results[metric_name] = response['data']['result']
            except Exception as e:
                logger.error(f"Error executing PromQL query '{metric_name}': {e}")
                
        return results
    
    def _query_prometheus(self, query: str) -> Dict[str, Any]:
        """Execute a PromQL query against Prometheus"""
        endpoint = f"{self.prometheus_url.rstrip('/')}/api/v1/query"
        params = {'query': query, 'time': time.time()}
        
        try:
            if self.prometheus_auth_type == "basic":
                response = requests.get(
                    endpoint, 
                    params=params,
                    auth=HTTPBasicAuth(self.prometheus_username, self.prometheus_password),
                    timeout=10
                )
            elif self.prometheus_auth_type == "oauth2" and self.oauth_session:
                response = self.oauth_session.get(
                    endpoint,
                    params=params,
                    timeout=10
                )
            else:
                # No authentication
                response = requests.get(
                    endpoint,
                    params=params,
                    timeout=10
                )
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Prometheus: {e}")
            return {}

class MetricsAgent:
    """
    Metrics specialist agent for the Kubernetes root cause analysis system.
    This agent focuses on collecting and analyzing metrics from Kubernetes
    clusters to identify resource constraints, performance issues, and
    anomalies.
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0):
        """
        Initialize the metrics agent with LLM settings and metrics client
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.metrics_client = MetricsClient()
        
        self.system_prompt = """
        You are a Kubernetes metrics specialist agent in a root cause analysis system.
        Your job is to collect and analyze metrics data from a Kubernetes cluster to identify
        potential resource constraints, performance issues, and other anomalies.
        
        You need to:
        1. Examine node resource utilization (CPU, memory, disk)
        2. Analyze pod resource usage and constraints
        3. Investigate service performance metrics
        4. Identify potential bottlenecks and resource contention
        5. Look for correlations between metrics and reported symptoms
        
        Based on the evidence collected, identify potential performance or resource issues 
        and determine the likelihood that metrics-related problems are causing the reported symptoms.
        """
    
    def collect_metrics_evidence(self, task: Task) -> List[Evidence]:
        """
        Collect metrics-related evidence from the Kubernetes cluster
        
        Args:
            task: The investigation task
            
        Returns:
            List[Evidence]: Collected evidence items
        """
        logger.info(f"Collecting metrics evidence for task: {task.description}")
        evidence = []
        namespace = os.environ.get("INVESTIGATION_NAMESPACE", "default")
        
        # Collect node metrics
        node_metrics = self.metrics_client.get_node_metrics()
        evidence.append(Evidence(
            resource_type="NodeMetrics",
            raw_data=node_metrics,
            analysis="Node resource utilization metrics"
        ))
        
        # Collect pod metrics
        pod_metrics = self.metrics_client.get_pod_metrics(namespace)
        evidence.append(Evidence(
            resource_type="PodMetrics",
            raw_data=pod_metrics,
            analysis="Pod resource usage metrics"
        ))
        
        # Collect service metrics if using Prometheus
        if self.metrics_client.metrics_source == "prometheus":
            service_metrics = self.metrics_client.get_service_metrics(namespace)
            evidence.append(Evidence(
                resource_type="ServiceMetrics",
                raw_data=service_metrics,
                analysis="Service performance metrics"
            ))
            
            # Collect database metrics if database-related task
            if "database" in task.description.lower():
                db_metrics = self.metrics_client.get_database_metrics(namespace)
                evidence.append(Evidence(
                    resource_type="DatabaseMetrics",
                    raw_data=db_metrics,
                    analysis="Database performance metrics"
                ))
        
        return evidence
    
    def analyze_evidence(self, evidence: List[Evidence], task: Task) -> Finding:
        """
        Analyze the collected metrics evidence to produce findings
        
        Args:
            evidence: Collected evidence items
            task: The investigation task
            
        Returns:
            Finding: Analysis results
        """
        logger.info(f"Analyzing metrics evidence for task: {task.description}")
        
        template = self.system_prompt + """
        ## Task Description
        {task_description}
        
        ## Evidence Collected
        
        {evidence_json}
        
        ## Analysis Instructions
        
        Based on this metrics evidence:
        1. Identify any resource constraints (CPU, memory, disk)
        2. Analyze performance bottlenecks and high utilization patterns
        3. Check for correlations between resource usage and reported symptoms
        4. Look for resource quotas or limits that might be causing issues
        5. Identify any unusual patterns or anomalies in the metrics
        
        Output your analysis in the following JSON format:
        ```json
        {{
          "analysis": "detailed analysis of the metrics evidence",
          "potential_issues": ["list of potential resource or performance issues identified"],
          "confidence": 0.0-1.0 (confidence that metrics issues are causing the symptoms),
          "further_investigation": ["areas that need further investigation"],
          "resource_constraints": ["specific resources that appear constrained"]
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
            agent_type="metrics",
            evidence=evidence,
            analysis=result.get("analysis", ""),
            confidence=result.get("confidence", 0.0),
            potential_issues=result.get("potential_issues", [])
        )
        
        return finding
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and investigate metrics issues
        
        Args:
            state: Current investigation state
            
        Returns:
            Dict: Updated investigation state with metrics findings
        """
        logger.info("Metrics agent activated")
        
        # Extract task information from state
        investigation_phase = state.get("investigation_phase", "")
        current_hypothesis = state.get("current_hypothesis", {})
        symptoms = state.get("initial_symptoms", "")
        
        # Create a task based on the current state
        task_description = f"Investigate metrics and resource utilization related to {current_hypothesis.get('focus', 'general symptoms')}"
        if symptoms:
            task_description += f" with symptoms: {symptoms}"
            
        task = Task(
            description=task_description,
            type="metrics_investigation",
            priority="high" if current_hypothesis.get("type") == "resource" else "medium"
        )
        
        # Collect evidence
        evidence = self.collect_metrics_evidence(task)
        
        # Analyze evidence
        finding = self.analyze_evidence(evidence, task)
        
        # Update the state with new evidence and findings
        updated_evidence = state.get("evidence", []) + [e.to_dict() for e in evidence]
        updated_findings = state.get("findings", {})
        updated_findings["metrics"] = finding.to_dict()
        
        # Create confidence scores for metrics categories
        metrics_confidence = finding.confidence
        confidence_scores = state.get("confidence_scores", {})
        
        # Update confidence scores
        if metrics_confidence > 0.7:
            # If high confidence, specify subcategories
            confidence_scores["metrics"] = metrics_confidence
            
            # Check if specific issues have been identified
            for issue in finding.potential_issues:
                if "cpu" in issue.lower():
                    confidence_scores["cpu_constraint"] = metrics_confidence
                elif "memory" in issue.lower():
                    confidence_scores["memory_constraint"] = metrics_confidence
                elif "disk" in issue.lower():
                    confidence_scores["disk_constraint"] = metrics_confidence
                elif "network" in issue.lower():
                    confidence_scores["network_constraint"] = metrics_confidence
                elif "database" in issue.lower():
                    confidence_scores["database_performance"] = metrics_confidence
        else:
            # Just update general metrics confidence
            confidence_scores["metrics"] = metrics_confidence
        
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
    # Configure sample environment variables (in production these would be set externally)
    os.environ["METRICS_SOURCE"] = "kubernetes"  # or "prometheus"
    # os.environ["PROMETHEUS_URL"] = "http://prometheus.monitoring.svc.cluster.local:9090"
    # os.environ["PROMETHEUS_AUTH_TYPE"] = "oauth2"  # or "basic" or "none"
    os.environ["INVESTIGATION_NAMESPACE"] = "default"
    
    metrics_agent = MetricsAgent()
    
    # Sample state with hypothesis
    sample_state = {
        "investigation_phase": "hypothesis_testing",
        "initial_symptoms": """
        Several pods in the production namespace are showing high latency.
        CPU usage appears to be spiking during peak traffic hours.
        Some pods are being OOMKilled occasionally.
        """,
        "current_hypothesis": {
            "focus": "resource constraints",
            "type": "resource"
        }
    }
    
    # Process the state
    result = metrics_agent(sample_state)
    
    # Print the result
    print(json.dumps(result, indent=2)) 