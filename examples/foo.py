import os
import json
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger("k8s_analyzer.analyzer")

@dataclass
class ClusterMetrics:
    cpu_usage: float
    memory_usage: float
    pod_count: int
    node_count: int

@dataclass
class ResourceStatus:
    total: float
    used: float
    available: float
    
class KubernetesCommand:
    def __init__(self):
        self.logger = logging.getLogger("k8s_analyzer.kubectl")
    
    def execute(self, cmd: List[str], json_output: bool = True) -> Any:
        """Execute a kubectl command and return the result"""
        try:
            # Ensure cmd starts with kubectl
            if not cmd[0].endswith("kubectl"):
                cmd = ["kubectl"] + cmd
            
            # Add json output format if needed
            if json_output and "-o" not in cmd and "top" not in cmd[1]:
                cmd.extend(["-o", "json"])
            
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.check_output(cmd)
            
            # Handle different output formats
            if json_output and "top" not in cmd[1]:
                try:
                    return json.loads(result)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON output: {str(e)}")
                    return result.decode()
            return result.decode()
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected error executing command: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def execute_static(cmd: List[str], json_output: bool = True) -> Any:
        """Static method for backward compatibility"""
        return KubernetesCommand().execute(cmd, json_output)

class ClusterHealthAnalyzer:
    @staticmethod
    def get_node_status() -> Dict:
        """Get detailed status of all nodes in the cluster"""
        try:
            # Get basic node info
            nodes = KubernetesCommand.execute_static(["get", "nodes"])
            
            # Get detailed node info
            detailed_nodes = {}
            for item in nodes.get("items", []):
                name = item["metadata"]["name"]
                describe = KubernetesCommand.execute_static(
                    ["describe", "node", name],
                    json_output=False
                )
                detailed_nodes[name] = {
                    "status": item["status"],
                    "description": describe
                }
            
            return {
                "basic": nodes,
                "detailed": detailed_nodes
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_node_metrics() -> Dict:
        """Get resource metrics for all nodes"""
        try:
            metrics = KubernetesCommand.execute_static(["top", "nodes"], json_output=False)
            if isinstance(metrics, str) and "error: Metrics API not available" in metrics:
                # Try alternative method using describe
                nodes = KubernetesCommand.execute_static(["get", "nodes"])
                metrics_data = {}
                for item in nodes.get("items", []):
                    name = item["metadata"]["name"]
                    metrics_data[name] = {
                        "allocatable": item["status"].get("allocatable", {}),
                        "capacity": item["status"].get("capacity", {}),
                        "conditions": item["status"].get("conditions", [])
                    }
                return {
                    "warning": "Metrics API not available, using node status information instead",
                    "node_resources": metrics_data
                }
            return {"metrics": metrics}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_cluster_events() -> Dict:
        """Get cluster-wide events with improved filtering"""
        try:
            # Get all events
            all_events = KubernetesCommand.execute_static(["get", "events", "--all-namespaces"])
            
            # Filter and categorize events
            events_by_type = {"Normal": [], "Warning": []}
            recent_events = []
            
            for event in all_events.get("items", []):
                event_type = event.get("type", "Unknown")
                if event_type in events_by_type:
                    events_by_type[event_type].append({
                        "namespace": event["metadata"]["namespace"],
                        "name": event["metadata"]["name"],
                        "reason": event.get("reason", "Unknown"),
                        "message": event.get("message", "No message"),
                        "count": event.get("count", 1),
                        "firstTimestamp": event.get("firstTimestamp", ""),
                        "lastTimestamp": event.get("lastTimestamp", "")
                    })
                
                # Add to recent events if it occurred in the last hour
                if "lastTimestamp" in event:
                    try:
                        last_time = datetime.fromisoformat(event["lastTimestamp"].replace("Z", "+00:00"))
                        if (datetime.now() - last_time).total_seconds() < 3600:
                            recent_events.append(event)
                    except ValueError:
                        pass
            
            return {
                "by_type": events_by_type,
                "recent": recent_events[:10]  # Only include the 10 most recent events
            }
        except Exception as e:
            return {"error": str(e)}

class ResourceAnalyzer:
    @staticmethod
    def get_resource_usage() -> Dict:
        """Get resource usage across the cluster"""
        return KubernetesCommand.execute_static(["top", "pods", "--all-namespaces"])
    
    @staticmethod
    def get_resource_quotas() -> Dict:
        """Get resource quotas for all namespaces"""
        return KubernetesCommand.execute_static(["get", "resourcequotas", "--all-namespaces"])
    
    @staticmethod
    def get_limit_ranges() -> Dict:
        """Get limit ranges for all namespaces"""
        return KubernetesCommand.execute_static(["get", "limitranges", "--all-namespaces"])

class NetworkAnalyzer:
    @staticmethod
    def get_services() -> Dict:
        """Get all services in the cluster"""
        return KubernetesCommand.execute_static(["get", "services", "--all-namespaces"])
    
    @staticmethod
    def get_network_policies() -> Dict:
        """Get all network policies"""
        return KubernetesCommand.execute_static(["get", "networkpolicies", "--all-namespaces"])
    
    @staticmethod
    def get_ingresses() -> Dict:
        """Get all ingresses"""
        return KubernetesCommand.execute_static(["get", "ingresses", "--all-namespaces"])

class SecurityAnalyzer:
    @staticmethod
    def get_service_accounts() -> Dict:
        """Get all service accounts"""
        return KubernetesCommand.execute_static(["get", "serviceaccounts", "--all-namespaces"])
    
    @staticmethod
    def get_roles() -> Dict:
        """Get all roles and cluster roles"""
        roles = KubernetesCommand.execute_static(["get", "roles", "--all-namespaces"])
        cluster_roles = KubernetesCommand.execute_static(["get", "clusterroles"])
        return {"roles": roles, "cluster_roles": cluster_roles}
    
    @staticmethod
    def get_security_context_constraints() -> Dict:
        """Get security context constraints"""
        return KubernetesCommand.execute_static(["get", "psp"])

class StorageAnalyzer:
    @staticmethod
    def get_persistent_volumes() -> Dict:
        """Get all persistent volumes"""
        return KubernetesCommand.execute_static(["get", "pv"])
    
    @staticmethod
    def get_storage_classes() -> Dict:
        """Get all storage classes"""
        return KubernetesCommand.execute_static(["get", "storageclasses"])
    
    @staticmethod
    def get_volume_snapshots() -> Dict:
        """Get all volume snapshots"""
        return KubernetesCommand.execute_static(["get", "volumesnapshots", "--all-namespaces"])

class WorkloadAnalyzer:
    @staticmethod
    def get_deployments() -> Dict:
        """Get all deployments"""
        return KubernetesCommand.execute_static(["get", "deployments", "--all-namespaces"])
    
    @staticmethod
    def get_jobs() -> Dict:
        """Get all jobs and cronjobs"""
        jobs = KubernetesCommand.execute_static(["get", "jobs", "--all-namespaces"])
        cronjobs = KubernetesCommand.execute_static(["get", "cronjobs", "--all-namespaces"])
        return {"jobs": jobs, "cronjobs": cronjobs}
    
    @staticmethod
    def get_pods() -> Dict:
        """Get all pods"""
        return KubernetesCommand.execute_static(["get", "pods", "--all-namespaces"])

class MaintenanceAnalyzer:
    @staticmethod
    def get_component_status() -> Dict:
        """Get status of cluster components"""
        return KubernetesCommand.execute_static(["get", "componentstatuses"])
    
    @staticmethod
    def get_api_versions() -> Dict:
        """Get supported API versions"""
        return KubernetesCommand.execute_static(["api-versions"], json_output=False)
    
    @staticmethod
    def get_cluster_info() -> Dict:
        """Get cluster information"""
        return KubernetesCommand.execute_static(["cluster-info", "dump"])

def summarize_data(data: Dict) -> Dict:
    """Summarize data to reduce token usage"""
    logger.debug("Summarizing data")
    if not isinstance(data, dict):
        logger.debug("Data is not a dictionary, returning as is")
        return data
        
    # For items list, keep only essential fields
    if "items" in data:
        logger.debug("Processing items list")
        summarized_items = []
        for item in data["items"]:
            if not isinstance(item, dict):
                continue
                
            summary = {
                "name": item.get("metadata", {}).get("name", "unknown"),
                "namespace": item.get("metadata", {}).get("namespace", "default"),
                "status": item.get("status", {}).get("phase", "unknown")
            }
            
            # Add resource-specific important fields
            if "spec" in item:
                spec = item["spec"]
                if "replicas" in spec:
                    summary["replicas"] = spec["replicas"]
                if "nodeName" in spec:
                    summary["node"] = spec["nodeName"]
                    
            # Add resource usage if available
            if "usage" in item:
                summary["usage"] = {
                    k: v for k, v in item["usage"].items()
                    if k in ["cpu", "memory"]
                }
                
            summarized_items.append(summary)
        logger.debug(f"Summarized {len(summarized_items)} items")
        return {"items": summarized_items}
    
    # Handle node status
    if "basic" in data and "detailed" in data:
        nodes_summary = {
            "total_nodes": len(data["basic"].get("items", [])),
            "nodes": {}
        }
        
        for item in data["basic"].get("items", []):
            name = item["metadata"]["name"]
            status = item["status"]
            nodes_summary["nodes"][name] = {
                "conditions": {
                    cond["type"]: cond["status"] 
                    for cond in status.get("conditions", [])
                },
                "capacity": {
                    k: v for k, v in status.get("capacity", {}).items()
                    if k in ["cpu", "memory", "pods"]
                }
            }
        return nodes_summary
    
    # Handle events
    if "by_type" in data and "recent" in data:
        return {
            "warning_count": len(data["by_type"].get("Warning", [])),
            "recent_events": [
                {
                    "type": event.get("type", "Unknown"),
                    "reason": event.get("reason", "Unknown"),
                    "message": event.get("message", "No message")[:100]  # Truncate long messages
                }
                for event in data["recent"][:5]  # Only keep last 5 events
            ]
        }
    
    return data

class ClusterAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger("k8s_analyzer.analyzer.cluster")
        self.client = OpenAI()
        self.health_analyzer = ClusterHealthAnalyzer()
        self.resource_analyzer = ResourceAnalyzer()
        self.workload_analyzer = WorkloadAnalyzer()
        self.network_analyzer = NetworkAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.storage_analyzer = StorageAnalyzer()
        self.maintenance_analyzer = MaintenanceAnalyzer()
        
        # Define question categories and their analyzers
        self.categories = {
            "cluster_health": self.analyze_cluster_health,
            "namespace_overview": self.analyze_namespace_overview,
            "resource_utilization": self.analyze_resource_utilization,
            "application_status": self.analyze_application_status,
            "network_services": self.analyze_network_services,
            "security_access": self.analyze_security_access,
            "maintenance_updates": self.analyze_maintenance_updates,
            "storage_volumes": self.analyze_storage_volumes,
            "workload_management": self.analyze_workload_management
        }
        self.logger.info("ClusterAnalyzer initialized")
    
    def collect_metadata(self) -> Dict[str, Any]:
        """Collect cluster metadata for analysis context"""
        metadata = {
            "cluster_stats": {},
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "analyzed_components": []
        }

        # Collect pod statistics
        pods = self.workload_analyzer.get_pods()
        if "items" in pods:
            pod_status = {}
            for pod in pods["items"]:
                status = pod.get("status", {}).get("phase", "Unknown")
                container_statuses = pod.get("status", {}).get("containerStatuses", [])
                
                # Check for more specific status from container statuses
                for container in container_statuses:
                    if container.get("state", {}).get("waiting", {}).get("reason") in [
                        "CrashLoopBackOff", "ImagePullBackOff", "ContainerCreating"
                    ]:
                        status = container["state"]["waiting"]["reason"]
                
                pod_status[status] = pod_status.get(status, 0) + 1

            metadata["cluster_stats"].update({
                "total_pods": len(pods["items"]),
                "pod_status": pod_status
            })

        # Collect node statistics
        nodes = self.health_analyzer.get_node_status()
        if "basic" in nodes and "items" in nodes["basic"]:
            metadata["cluster_stats"]["total_nodes"] = len(nodes["basic"]["items"])

        # Count namespaces
        namespaces = KubernetesCommand.execute_static(["get", "namespaces"])
        if "items" in namespaces:
            metadata["cluster_stats"]["namespaces"] = len(namespaces["items"])

        # Track analyzed components
        metadata["analyzed_components"] = [
            "cluster_health",
            "workload_status",
            "resource_utilization"
        ]

        return metadata

    def analyze_cluster_health(self) -> Dict:
        """Analyze overall cluster health"""
        data = {
            "nodes": self.health_analyzer.get_node_status(),
            "metrics": self.health_analyzer.get_node_metrics(),
            "events": self.health_analyzer.get_cluster_events()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_namespace_overview(self) -> Dict:
        """Analyze namespace status and resources"""
        data = {
            "pods": self.workload_analyzer.get_pods(),
            "deployments": self.workload_analyzer.get_deployments(),
            "resource_usage": self.resource_analyzer.get_resource_usage()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_resource_utilization(self) -> Dict:
        """Analyze resource utilization"""
        data = {
            "usage": self.resource_analyzer.get_resource_usage(),
            "quotas": self.resource_analyzer.get_resource_quotas(),
            "limits": self.resource_analyzer.get_limit_ranges()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_application_status(self) -> Dict:
        """Analyze application status across the cluster"""
        data = {
            "deployments": self.workload_analyzer.get_deployments(),
            "pods": self.workload_analyzer.get_pods(),
            "events": self.health_analyzer.get_cluster_events()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_network_services(self) -> Dict:
        """Analyze network and services"""
        data = {
            "services": self.network_analyzer.get_services(),
            "policies": self.network_analyzer.get_network_policies(),
            "ingresses": self.network_analyzer.get_ingresses()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_security_access(self) -> Dict:
        """Analyze security and access control"""
        data = {
            "service_accounts": self.security_analyzer.get_service_accounts(),
            "roles": self.security_analyzer.get_roles(),
            "security_constraints": self.security_analyzer.get_security_context_constraints()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_storage_volumes(self) -> Dict:
        """Analyze storage and volumes"""
        data = {
            "persistent_volumes": self.storage_analyzer.get_persistent_volumes(),
            "storage_classes": self.storage_analyzer.get_storage_classes(),
            "snapshots": self.storage_analyzer.get_volume_snapshots()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_workload_management(self) -> Dict:
        """Analyze workload management"""
        data = {
            "deployments": self.workload_analyzer.get_deployments(),
            "jobs": self.workload_analyzer.get_jobs(),
            "pods": self.workload_analyzer.get_pods()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_maintenance_updates(self) -> Dict:
        """Analyze maintenance and updates"""
        data = {
            "component_status": self.maintenance_analyzer.get_component_status(),
            "api_versions": self.maintenance_analyzer.get_api_versions(),
            "cluster_info": self.maintenance_analyzer.get_cluster_info()
        }
        return {k: summarize_data(v) for k, v in data.items()}
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the cluster based on the question and return structured response"""
        try:
            self.logger.info("Starting question analysis")
            self.logger.debug(f"Analyzing question: {question}")
            
            # Define categories and their keywords for selective data collection
            categories = {
                "health": ["health", "status", "condition", "ready", "available"],
                "resources": ["cpu", "memory", "resource", "utilization", "usage", "limit"],
                "workloads": ["pod", "deployment", "job", "container", "application"],
                "network": ["service", "ingress", "network", "connection", "endpoint"],
                "storage": ["volume", "storage", "pv", "pvc", "disk"],
                "security": ["security", "role", "permission", "access", "auth"]
            }
            
            # Determine relevant categories
            question_lower = question.lower()
            relevant_categories = []
            for category, keywords in categories.items():
                if any(keyword in question_lower for keyword in keywords):
                    relevant_categories.append(category)
            
            self.logger.info(f"Identified relevant categories: {', '.join(relevant_categories) or 'none'}")
            
            # If no specific categories are identified, include basic health and workload data
            if not relevant_categories:
                self.logger.debug("No specific categories identified, using default categories")
                relevant_categories = ["health", "workloads"]
            
            # Collect cluster data
            self.logger.debug("Starting data collection")
            cluster_data = {}
            
            if "health" in relevant_categories:
                self.logger.debug("Collecting health data")
                nodes = self.health_analyzer.get_node_status()
                cluster_data["nodes"] = summarize_data(nodes)
                cluster_data["events"] = summarize_data(self.health_analyzer.get_cluster_events())
                
            if "resources" in relevant_categories:
                self.logger.debug("Collecting resource data")
                metrics = self.health_analyzer.get_node_metrics()
                usage = self.resource_analyzer.get_resource_usage()
                cluster_data["node_metrics"] = summarize_data(metrics)
                cluster_data["resource_usage"] = summarize_data(usage)
                
            if "workloads" in relevant_categories:
                self.logger.debug("Collecting workload data")
                pods = self.workload_analyzer.get_pods()
                deployments = self.workload_analyzer.get_deployments()
                cluster_data["pods"] = summarize_data(pods)
                cluster_data["deployments"] = summarize_data(deployments)
                
            if "network" in relevant_categories:
                self.logger.debug("Collecting network data")
                services = self.network_analyzer.get_services()
                ingresses = self.network_analyzer.get_ingresses()
                cluster_data["network"] = {
                    "services": summarize_data(services),
                    "ingresses": summarize_data(ingresses)
                }
                
            if "storage" in relevant_categories:
                self.logger.debug("Collecting storage data")
                volumes = self.storage_analyzer.get_persistent_volumes()
                cluster_data["storage"] = summarize_data(volumes)
                
            if "security" in relevant_categories:
                self.logger.debug("Collecting security data")
                roles = self.security_analyzer.get_roles()
                cluster_data["security"] = summarize_data(roles)

            self.logger.info("Data collection completed")
            self.logger.debug(f"Collected data for categories: {list(cluster_data.keys())}")

            # Prepare system prompt
            self.logger.debug("Preparing OpenAI request")
            system_prompt = """You are a Kubernetes cluster analyzer. Analyze the specific aspects of the cluster data related to the question and provide a focused response. Include only relevant findings and actions. Format as JSON with:
1. main_response: Brief, focused analysis summary
2. actions: List of specific, high-impact actions (limit to 3 most important)
3. next_steps: Targeted investigation steps (limit to 2 most relevant)
Each action: {priority, component, description, command}
Each next_step: {id, category, description, rationale}"""

            # Call OpenAI API
            self.logger.debug("Sending request to OpenAI")
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}\nFocus areas: {', '.join(relevant_categories)}\nRelevant cluster data: {json.dumps(cluster_data)}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            self.logger.debug("Received response from OpenAI")
            
            # Parse response
            analysis = json.loads(response.choices[0].message.content)
            self.logger.info("Analysis completed successfully")
            self.logger.debug(f"Analysis contains {len(analysis.get('actions', []))} actions and {len(analysis.get('next_steps', []))} next steps")
            
            return analysis

        except Exception as e:
            self.logger.exception(f"Error during analysis: {str(e)}")
            return {
                "main_response": "Error analyzing cluster",
                "actions": [],
                "next_steps": [],
                "metadata": {},
                "error": str(e)
            }

    def get_pod_logs(self, namespace: str, pod_name: str, container: Optional[str] = None, previous: bool = False) -> str:
        """Get logs for a specific pod"""
        cmd = ["kubectl", "logs", "-n", namespace, pod_name]
        if container:
            cmd.extend(["-c", container])
        if previous:
            cmd.append("--previous")
        return KubernetesCommand.execute_static(cmd, json_output=False)

    def describe_resource(self, resource_type: str, name: str, namespace: Optional[str] = None) -> str:
        """Describe a Kubernetes resource"""
        cmd = ["kubectl", "describe", resource_type, name]
        if namespace:
            cmd.extend(["-n", namespace])
        return KubernetesCommand.execute_static(cmd, json_output=False)

def main():
    # Initialize the analyzer
    analyzer = ClusterAnalyzer()
    
    print("\nKubernetes Cluster Analyzer")
    print("=" * 50)
    print("Type 'exit' or 'quit' to end the session\n")
    
    while True:
        try:
            # Prompt for user input
            question = input("Ask here: > ").strip()
            
            # Check for exit command
            if question.lower() in ['exit', 'quit']:
                print("\nExiting Kubernetes Cluster Analyzer...")
                break
            
            # Skip empty input
            if not question:
                continue
            
            print("\nAnalyzing your question...")
            print("-" * 50)
            
            # Get and print analysis
            analysis = analyzer.analyze_question(question)
            print(json.dumps(analysis))
            print("\n" + "-"*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting Kubernetes Cluster Analyzer...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again with a different question.\n")

if __name__ == "__main__":
    main() 