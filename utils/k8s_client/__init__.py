"""
Kubernetes Client package for interacting with Kubernetes clusters.

This package provides a client for interacting with Kubernetes clusters,
both real and simulated.
"""

from utils.k8s_client.client import K8sClient

__all__ = ["K8sClient"]
