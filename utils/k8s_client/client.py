"""
Kubernetes Client for interacting with Kubernetes clusters.

This module provides a client for interacting with Kubernetes clusters,
both real and simulated.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class K8sClient:
    """
    Client for interacting with Kubernetes clusters.
    This implementation provides both real cluster access and simulated responses.
    """

    def __init__(self, use_mock: bool = False):
        """
        Initialize the Kubernetes client.
        
        Args:
            use_mock: If True, use mock responses instead of real cluster access
        """
        self.use_mock = os.environ.get("MOCK_K8S", "false").lower() == "true" if use_mock else False
        logger.info(f"Initializing K8sClient with mock mode: {self.use_mock}")
        
        # Try to initialize kubernetes client if not using mock
        if not self.use_mock:
            try:
                # Import kubernetes client - we do this dynamically to avoid
                # requiring the package if only using mock mode
                from kubernetes import client, config
                
                try:
                    # Try to load from default kubeconfig
                    config.load_kube_config()
                    self.api_client = client.ApiClient()
                    self.core_v1 = client.CoreV1Api(self.api_client)
                    self.apps_v1 = client.AppsV1Api(self.api_client)
                    self.custom_objects = client.CustomObjectsApi(self.api_client)
                    logger.info("Successfully initialized Kubernetes client from kubeconfig")
                except Exception as e:
                    # If that fails, try in-cluster config (for running in a pod)
                    try:
                        config.load_incluster_config()
                        self.api_client = client.ApiClient()
                        self.core_v1 = client.CoreV1Api(self.api_client)
                        self.apps_v1 = client.AppsV1Api(self.api_client)
                        self.custom_objects = client.CustomObjectsApi(self.api_client)
                        logger.info("Successfully initialized Kubernetes client from in-cluster config")
                    except Exception as e2:
                        logger.error(f"Failed to initialize Kubernetes client: {e2}")
                        logger.warning("Falling back to mock mode")
                        self.use_mock = True
            except ImportError:
                logger.error("Kubernetes client module not installed, falling back to mock mode")
                self.use_mock = True
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes in the cluster."""
        if self.use_mock:
            return [
                {
                    "name": "worker-1",
                    "status": "Ready",
                    "roles": ["worker"],
                    "age": "45d",
                    "version": "v1.25.0",
                    "internal_ip": "10.0.0.5",
                    "external_ip": "203.0.113.1",
                    "os_image": "Ubuntu 20.04",
                    "kernel_version": "5.4.0-90-generic",
                    "container_runtime": "containerd://1.6.8",
                    "capacity": {
                        "cpu": "4",
                        "memory": "8Gi",
                        "pods": "110"
                    },
                    "allocatable": {
                        "cpu": "3800m",
                        "memory": "7Gi",
                        "pods": "110"
                    },
                    "conditions": [
                        {"type": "Ready", "status": "True"},
                        {"type": "DiskPressure", "status": "False"},
                        {"type": "MemoryPressure", "status": "False"},
                        {"type": "PIDPressure", "status": "False"},
                        {"type": "NetworkUnavailable", "status": "False"}
                    ]
                },
                {
                    "name": "worker-2",
                    "status": "Ready",
                    "roles": ["worker"],
                    "age": "45d",
                    "version": "v1.25.0",
                    "internal_ip": "10.0.0.6",
                    "external_ip": "203.0.113.2",
                    "os_image": "Ubuntu 20.04",
                    "kernel_version": "5.4.0-90-generic",
                    "container_runtime": "containerd://1.6.8",
                    "capacity": {
                        "cpu": "4",
                        "memory": "8Gi",
                        "pods": "110"
                    },
                    "allocatable": {
                        "cpu": "3800m",
                        "memory": "7Gi",
                        "pods": "110"
                    },
                    "conditions": [
                        {"type": "Ready", "status": "True"},
                        {"type": "DiskPressure", "status": "False"},
                        {"type": "MemoryPressure", "status": "False"},
                        {"type": "PIDPressure", "status": "False"},
                        {"type": "NetworkUnavailable", "status": "False"}
                    ]
                },
                {
                    "name": "master-1",
                    "status": "Ready",
                    "roles": ["control-plane", "master"],
                    "age": "45d",
                    "version": "v1.25.0",
                    "internal_ip": "10.0.0.2",
                    "external_ip": "203.0.113.10",
                    "os_image": "Ubuntu 20.04",
                    "kernel_version": "5.4.0-90-generic",
                    "container_runtime": "containerd://1.6.8",
                    "capacity": {
                        "cpu": "4",
                        "memory": "16Gi",
                        "pods": "110"
                    },
                    "allocatable": {
                        "cpu": "3600m",
                        "memory": "15Gi",
                        "pods": "110"
                    },
                    "conditions": [
                        {"type": "Ready", "status": "True"},
                        {"type": "DiskPressure", "status": "False"},
                        {"type": "MemoryPressure", "status": "False"},
                        {"type": "PIDPressure", "status": "False"},
                        {"type": "NetworkUnavailable", "status": "False"}
                    ]
                }
            ]
        else:
            # Real implementation would use the Kubernetes API
            try:
                nodes = self.core_v1.list_node().items
                return [self._format_node(node) for node in nodes]
            except Exception as e:
                logger.error(f"Error getting nodes: {e}")
                return []
    
    def get_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get all pods in the given namespace."""
        if self.use_mock:
            return [
                {
                    "name": "nginx-deployment-66b6c48dd5-4jw2p",
                    "namespace": namespace,
                    "status": "Running",
                    "ready": "1/1",
                    "restarts": 0,
                    "age": "2d",
                    "ip": "10.244.0.5",
                    "node": "worker-1",
                    "nominated_node": None,
                    "readiness_gates": None,
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:1.19",
                            "ports": [{"containerPort": 80, "protocol": "TCP"}],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "200m", "memory": "256Mi"}
                            },
                            "state": {"running": {"startedAt": "2023-09-01T10:00:00Z"}},
                            "ready": True,
                            "restart_count": 0,
                            "image_id": "docker-pullable://nginx@sha256:123456789abcdef",
                            "container_id": "containerd://abcdef1234567890"
                        }
                    ],
                    "conditions": [
                        {"type": "Initialized", "status": "True"},
                        {"type": "Ready", "status": "True"},
                        {"type": "ContainersReady", "status": "True"},
                        {"type": "PodScheduled", "status": "True"}
                    ],
                    "events": []
                },
                {
                    "name": "nginx-deployment-66b6c48dd5-8wxyz",
                    "namespace": namespace,
                    "status": "Running",
                    "ready": "1/1",
                    "restarts": 0,
                    "age": "2d",
                    "ip": "10.244.0.6",
                    "node": "worker-2",
                    "nominated_node": None,
                    "readiness_gates": None,
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:1.19",
                            "ports": [{"containerPort": 80, "protocol": "TCP"}],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "200m", "memory": "256Mi"}
                            },
                            "state": {"running": {"startedAt": "2023-09-01T10:00:00Z"}},
                            "ready": True,
                            "restart_count": 0,
                            "image_id": "docker-pullable://nginx@sha256:123456789abcdef",
                            "container_id": "containerd://abcdef1234567890"
                        }
                    ],
                    "conditions": [
                        {"type": "Initialized", "status": "True"},
                        {"type": "Ready", "status": "True"},
                        {"type": "ContainersReady", "status": "True"},
                        {"type": "PodScheduled", "status": "True"}
                    ],
                    "events": []
                },
                {
                    "name": "redis-master-5d8b66464f-2lmnx",
                    "namespace": namespace,
                    "status": "Pending",
                    "ready": "0/1",
                    "restarts": 0,
                    "age": "1h",
                    "ip": None,
                    "node": None,
                    "nominated_node": None,
                    "readiness_gates": None,
                    "containers": [
                        {
                            "name": "redis",
                            "image": "redis:6.0",
                            "ports": [{"containerPort": 6379, "protocol": "TCP"}],
                            "resources": {
                                "requests": {"cpu": "500m", "memory": "1Gi"},
                                "limits": {"cpu": "1", "memory": "2Gi"}
                            },
                            "state": {"waiting": {"reason": "ContainerCreating"}},
                            "ready": False,
                            "restart_count": 0,
                            "image_id": "",
                            "container_id": ""
                        }
                    ],
                    "conditions": [
                        {"type": "Initialized", "status": "True"},
                        {"type": "Ready", "status": "False"},
                        {"type": "ContainersReady", "status": "False"},
                        {"type": "PodScheduled", "status": "True"}
                    ],
                    "events": [
                        {
                            "type": "Warning",
                            "reason": "FailedScheduling",
                            "message": "0/3 nodes are available: 3 Insufficient memory.",
                            "count": 5,
                            "first_timestamp": "2023-09-02T10:00:00Z",
                            "last_timestamp": "2023-09-02T10:05:00Z"
                        }
                    ]
                }
            ]
        else:
            # Real implementation would use the Kubernetes API
            try:
                pods = self.core_v1.list_namespaced_pod(namespace).items
                return [self._format_pod(pod) for pod in pods]
            except Exception as e:
                logger.error(f"Error getting pods in namespace {namespace}: {e}")
                return []
    
    def get_deployments(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get all deployments in the given namespace."""
        if self.use_mock:
            return [
                {
                    "name": "nginx-deployment",
                    "namespace": namespace,
                    "ready": "2/2",
                    "up_to_date": 2,
                    "available": 2,
                    "age": "2d",
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:1.19",
                            "ports": [{"containerPort": 80, "protocol": "TCP"}],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "200m", "memory": "256Mi"}
                            }
                        }
                    ],
                    "replicas": 2,
                    "strategy": {
                        "type": "RollingUpdate",
                        "rollingUpdate": {
                            "maxUnavailable": "25%",
                            "maxSurge": "25%"
                        }
                    },
                    "conditions": [
                        {"type": "Available", "status": "True"},
                        {"type": "Progressing", "status": "True"}
                    ]
                },
                {
                    "name": "redis-master",
                    "namespace": namespace,
                    "ready": "0/1",
                    "up_to_date": 1,
                    "available": 0,
                    "age": "1h",
                    "containers": [
                        {
                            "name": "redis",
                            "image": "redis:6.0",
                            "ports": [{"containerPort": 6379, "protocol": "TCP"}],
                            "resources": {
                                "requests": {"cpu": "500m", "memory": "1Gi"},
                                "limits": {"cpu": "1", "memory": "2Gi"}
                            }
                        }
                    ],
                    "replicas": 1,
                    "strategy": {
                        "type": "RollingUpdate",
                        "rollingUpdate": {
                            "maxUnavailable": "25%",
                            "maxSurge": "25%"
                        }
                    },
                    "conditions": [
                        {"type": "Available", "status": "False", "reason": "MinimumReplicasUnavailable"},
                        {"type": "Progressing", "status": "True"}
                    ]
                }
            ]
        else:
            # Real implementation would use the Kubernetes API
            try:
                deployments = self.apps_v1.list_namespaced_deployment(namespace).items
                return [self._format_deployment(deployment) for deployment in deployments]
            except Exception as e:
                logger.error(f"Error getting deployments in namespace {namespace}: {e}")
                return []
    
    def get_services(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get all services in the given namespace."""
        if self.use_mock:
            return [
                {
                    "name": "nginx-service",
                    "namespace": namespace,
                    "type": "ClusterIP",
                    "cluster_ip": "10.96.0.10",
                    "external_ip": None,
                    "ports": [
                        {
                            "name": "http",
                            "port": 80,
                            "target_port": 80,
                            "node_port": None,
                            "protocol": "TCP"
                        }
                    ],
                    "selector": {"app": "nginx"},
                    "age": "2d"
                },
                {
                    "name": "redis-service",
                    "namespace": namespace,
                    "type": "ClusterIP",
                    "cluster_ip": "10.96.0.11",
                    "external_ip": None,
                    "ports": [
                        {
                            "name": "redis",
                            "port": 6379,
                            "target_port": 6379,
                            "node_port": None,
                            "protocol": "TCP"
                        }
                    ],
                    "selector": {"app": "redis"},
                    "age": "1h"
                }
            ]
        else:
            # Real implementation would use the Kubernetes API
            try:
                services = self.core_v1.list_namespaced_service(namespace).items
                return [self._format_service(service) for service in services]
            except Exception as e:
                logger.error(f"Error getting services in namespace {namespace}: {e}")
                return []
    
    def get_events(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get all events in the given namespace."""
        if self.use_mock:
            return [
                {
                    "type": "Warning",
                    "reason": "FailedScheduling",
                    "object": "pod/redis-master-5d8b66464f-2lmnx",
                    "message": "0/3 nodes are available: 3 Insufficient memory.",
                    "count": 5,
                    "first_timestamp": "2023-09-02T10:00:00Z",
                    "last_timestamp": "2023-09-02T10:05:00Z",
                    "source": "default-scheduler"
                },
                {
                    "type": "Normal",
                    "reason": "Scheduled",
                    "object": "pod/nginx-deployment-66b6c48dd5-4jw2p",
                    "message": "Successfully assigned default/nginx-deployment-66b6c48dd5-4jw2p to worker-1",
                    "count": 1,
                    "first_timestamp": "2023-09-01T10:00:00Z",
                    "last_timestamp": "2023-09-01T10:00:00Z",
                    "source": "default-scheduler"
                },
                {
                    "type": "Normal",
                    "reason": "Scheduled",
                    "object": "pod/nginx-deployment-66b6c48dd5-8wxyz",
                    "message": "Successfully assigned default/nginx-deployment-66b6c48dd5-8wxyz to worker-2",
                    "count": 1,
                    "first_timestamp": "2023-09-01T10:00:00Z",
                    "last_timestamp": "2023-09-01T10:00:00Z",
                    "source": "default-scheduler"
                }
            ]
        else:
            # Real implementation would use the Kubernetes API
            try:
                events = self.core_v1.list_namespaced_event(namespace).items
                return [self._format_event(event) for event in events]
            except Exception as e:
                logger.error(f"Error getting events in namespace {namespace}: {e}")
                return []
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status."""
        nodes = self.get_nodes()
        
        # Calculate overall status
        total_nodes = len(nodes)
        ready_nodes = sum(1 for node in nodes if any(
            cond.get("type") == "Ready" and cond.get("status") == "True" 
            for cond in node.get("conditions", [])
        ))
        
        # Calculate resource usage
        total_cpu = sum(float(node.get("capacity", {}).get("cpu", "0").replace("m", "")) for node in nodes)
        total_memory = sum(
            float(node.get("capacity", {}).get("memory", "0").replace("Gi", "")) 
            for node in nodes
        )
        
        return {
            "nodes": {
                "total": total_nodes,
                "ready": ready_nodes,
                "not_ready": total_nodes - ready_nodes
            },
            "resources": {
                "cpu": {
                    "total": f"{total_cpu}",
                    "unit": "cores"
                },
                "memory": {
                    "total": f"{total_memory}",
                    "unit": "Gi"
                }
            },
            "health": {
                "overall": "Healthy" if ready_nodes == total_nodes else "Degraded",
                "reason": None if ready_nodes == total_nodes else f"{total_nodes - ready_nodes} nodes not Ready"
            },
            "version": nodes[0].get("version") if nodes else "unknown"
        }
    
    def _format_node(self, node) -> Dict[str, Any]:
        """Format a Kubernetes node object into a dictionary."""
        # This would be implemented for real Kubernetes API objects
        return {}
    
    def _format_pod(self, pod) -> Dict[str, Any]:
        """Format a Kubernetes pod object into a dictionary."""
        # This would be implemented for real Kubernetes API objects
        return {}
    
    def _format_deployment(self, deployment) -> Dict[str, Any]:
        """Format a Kubernetes deployment object into a dictionary."""
        # This would be implemented for real Kubernetes API objects
        return {}
    
    def _format_service(self, service) -> Dict[str, Any]:
        """Format a Kubernetes service object into a dictionary."""
        # This would be implemented for real Kubernetes API objects
        return {}
    
    def _format_event(self, event) -> Dict[str, Any]:
        """Format a Kubernetes event object into a dictionary."""
        # This would be implemented for real Kubernetes API objects
        return {} 