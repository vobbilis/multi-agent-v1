"""
Kubernetes Events Specialist Agent for Root Cause Analysis
"""
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
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

class EventsClient:
    """Client for collecting Kubernetes events"""
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize the events client
        
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
    
    def get_events(self, namespace: Optional[str] = None, 
                 field_selector: Optional[str] = None,
                 time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Get Kubernetes events from the cluster
        
        Args:
            namespace: Filter events by namespace (None for all namespaces)
            field_selector: Additional field selectors
            time_window_minutes: Only return events from last N minutes
            
        Returns:
            List of event dictionaries
        """
        if self.use_mock:
            return self._mock_events(namespace, field_selector, time_window_minutes)
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Build the field selector
            if field_selector:
                selector = field_selector
            else:
                selector = ""
            
            # Get events
            if namespace:
                event_list = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=selector if selector else None
                )
            else:
                event_list = self.core_v1.list_event_for_all_namespaces(
                    field_selector=selector if selector else None
                )
            
            # Convert to simplified dictionary format and filter by time
            events = []
            for event in event_list.items:
                # Check if event is within the time window
                event_time = event.last_timestamp
                if not event_time:
                    event_time = event.event_time
                if not event_time:
                    event_time = event.first_timestamp
                
                # If we couldn't determine event time, include it anyway
                if not event_time or event_time >= cutoff_time:
                    event_dict = {
                        "name": event.metadata.name,
                        "namespace": event.metadata.namespace,
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "count": event.count,
                        "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                        "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                        "involved_object": {
                            "kind": event.involved_object.kind,
                            "name": event.involved_object.name,
                            "namespace": event.involved_object.namespace,
                            "uid": event.involved_object.uid
                        },
                        "source": {
                            "component": event.source.component,
                            "host": event.source.host
                        }
                    }
                    events.append(event_dict)
            
            return events
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def _mock_events(self, namespace: Optional[str] = None, 
                   field_selector: Optional[str] = None,
                   time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Provide mock events for testing"""
        now = datetime.now()
        
        # Common Kubernetes events for different scenarios
        mock_events = [
            # Pod scheduling events
            {
                "name": "backend-pod-scheduled",
                "namespace": "default",
                "type": "Normal",
                "reason": "Scheduled",
                "message": "Successfully assigned default/backend-6f7b8d9c5e-fghij to worker-1",
                "count": 1,
                "first_timestamp": (now - timedelta(minutes=25)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=25)).isoformat(),
                "involved_object": {
                    "kind": "Pod",
                    "name": "backend-6f7b8d9c5e-fghij",
                    "namespace": "default",
                    "uid": "123e4567-e89b-12d3-a456-426614174001"
                },
                "source": {
                    "component": "default-scheduler",
                    "host": ""
                }
            },
            # Container failures
            {
                "name": "database-container-failed",
                "namespace": "default",
                "type": "Warning",
                "reason": "BackOff",
                "message": "Back-off restarting failed container database in pod database-7c8d9e0f1a-klmno",
                "count": 5,
                "first_timestamp": (now - timedelta(minutes=15)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=5)).isoformat(),
                "involved_object": {
                    "kind": "Pod",
                    "name": "database-7c8d9e0f1a-klmno",
                    "namespace": "default",
                    "uid": "123e4567-e89b-12d3-a456-426614174002"
                },
                "source": {
                    "component": "kubelet",
                    "host": "worker-1"
                }
            },
            # Image pull errors
            {
                "name": "api-image-pull-error",
                "namespace": "api",
                "type": "Warning",
                "reason": "Failed",
                "message": "Error: ImagePullBackOff",
                "count": 3,
                "first_timestamp": (now - timedelta(minutes=10)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=2)).isoformat(),
                "involved_object": {
                    "kind": "Pod",
                    "name": "api-9e0f1b2c3d-uvwxy",
                    "namespace": "api",
                    "uid": "123e4567-e89b-12d3-a456-426614174003"
                },
                "source": {
                    "component": "kubelet",
                    "host": "worker-1"
                }
            },
            # Resource constraints
            {
                "name": "frontend-oom-killed",
                "namespace": "default",
                "type": "Warning",
                "reason": "OOMKilled",
                "message": "Container frontend was killed due to OOM (Out of Memory)",
                "count": 1,
                "first_timestamp": (now - timedelta(minutes=8)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=8)).isoformat(),
                "involved_object": {
                    "kind": "Pod",
                    "name": "frontend-5d8b9c7f68-abcde",
                    "namespace": "default",
                    "uid": "123e4567-e89b-12d3-a456-426614174004"
                },
                "source": {
                    "component": "kubelet",
                    "host": "worker-1"
                }
            },
            # Node issues
            {
                "name": "node-pressure",
                "namespace": "",
                "type": "Warning",
                "reason": "NodeHasDiskPressure",
                "message": "Node worker-2 has disk pressure",
                "count": 1,
                "first_timestamp": (now - timedelta(minutes=30)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=30)).isoformat(),
                "involved_object": {
                    "kind": "Node",
                    "name": "worker-2",
                    "namespace": "",
                    "uid": "123e4567-e89b-12d3-a456-426614174005"
                },
                "source": {
                    "component": "kubelet",
                    "host": "worker-2"
                }
            },
            # Service creation
            {
                "name": "service-created",
                "namespace": "default",
                "type": "Normal",
                "reason": "Created",
                "message": "Service default/cache created successfully",
                "count": 1,
                "first_timestamp": (now - timedelta(minutes=50)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=50)).isoformat(),
                "involved_object": {
                    "kind": "Service",
                    "name": "cache",
                    "namespace": "default",
                    "uid": "123e4567-e89b-12d3-a456-426614174006"
                },
                "source": {
                    "component": "service-controller",
                    "host": ""
                }
            },
            # Network policy issues
            {
                "name": "network-policy-applied",
                "namespace": "default",
                "type": "Normal",
                "reason": "NetworkPolicyApplied",
                "message": "Network policy default/default-deny applied",
                "count": 1,
                "first_timestamp": (now - timedelta(minutes=55)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=55)).isoformat(),
                "involved_object": {
                    "kind": "NetworkPolicy",
                    "name": "default-deny",
                    "namespace": "default",
                    "uid": "123e4567-e89b-12d3-a456-426614174007"
                },
                "source": {
                    "component": "kube-controller-manager",
                    "host": ""
                }
            },
            # ImagePullBackOff for chaos-dashboard
            {
                "name": "chaos-dashboard-image-pull-error",
                "namespace": "chaos-testing",
                "type": "Warning",
                "reason": "Failed",
                "message": "Error: ImagePullBackOff: unable to pull image 'ghcr.io/chaos-mesh/chaos-dashboard:v2.6.1'",
                "count": 3,
                "first_timestamp": (now - timedelta(minutes=10)).isoformat(),
                "last_timestamp": (now - timedelta(minutes=2)).isoformat(),
                "involved_object": {
                    "kind": "Pod",
                    "name": "chaos-dashboard-697d4ff49c-hztlb",
                    "namespace": "chaos-testing",
                    "uid": "123e4567-e89b-12d3-a456-426614174008"
                },
                "source": {
                    "component": "kubelet",
                    "host": "kind-control-plane"
                }
            }
        ]
        
        # Filter events by namespace
        if namespace:
            mock_events = [event for event in mock_events if event["namespace"] == namespace]
        
        # Filter by field selector (very basic implementation)
        if field_selector:
            if 'type=Warning' in field_selector:
                mock_events = [event for event in mock_events if event["type"] == "Warning"]
            elif 'type=Normal' in field_selector:
                mock_events = [event for event in mock_events if event["type"] == "Normal"]
            
            # Add support for other field selectors as needed
        
        return mock_events

class EventsAgent:
    """
    Kubernetes Events specialist agent for the root cause analysis system.
    This agent focuses on analyzing Kubernetes events to identify:
    - Pod lifecycle issues (creation, scheduling, termination)
    - Container failures
    - Image pull errors
    - Resource constraints
    - Node problems
    - System component issues
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0, use_mock: bool = False):
        """
        Initialize the events agent with LLM settings
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
            use_mock: Whether to use mock data
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.events_client = EventsClient(use_mock=use_mock)
        
        self.system_prompt = """
        You are a Kubernetes events specialist agent in a root cause analysis system.
        Your job is to analyze Kubernetes events to identify issues and their causes.
        
        You need to:
        1. Identify warning and error events
        2. Correlate events across resources and time
        3. Recognize patterns that indicate specific issues
        4. Understand the relationship between events and their causes
        5. Determine the significance and impact of events
        
        Based on the events analysis, identify potential issues and their likely causes.
        Look for patterns that may indicate the root cause of the reported symptoms.
        """
    
    def collect_events_evidence(self, task: Task) -> List[Evidence]:
        """
        Collect Kubernetes events as evidence
        
        Args:
            task: The investigation task
            
        Returns:
            List[Evidence]: Collected evidence items
        """
        logger.info(f"Collecting events evidence for task: {task.description}")
        evidence = []
        
        # Extract namespace if present in the task description
        namespace_match = re.search(r'namespace[s]?\s+([a-zA-Z0-9-]+)', task.description)
        namespace = namespace_match.group(1) if namespace_match else None
        
        # Get warning events (higher priority for issue detection)
        warning_events = self.events_client.get_events(
            namespace=namespace,
            field_selector="type=Warning",
            time_window_minutes=60
        )
        
        if warning_events:
            evidence.append(Evidence(
                resource_type="WarningEvents",
                raw_data=warning_events,
                analysis=f"Warning events from {namespace or 'all namespaces'} in the last 60 minutes"
            ))
        
        # Get normal events (for context)
        normal_events = self.events_client.get_events(
            namespace=namespace,
            field_selector="type=Normal",
            time_window_minutes=60
        )
        
        if normal_events:
            evidence.append(Evidence(
                resource_type="NormalEvents",
                raw_data=normal_events,
                analysis=f"Normal events from {namespace or 'all namespaces'} in the last 60 minutes"
            ))
        
        # If a specific pod or service name is mentioned, get events specific to that resource
        for resource_type in ["pod", "deployment", "service", "node"]:
            resource_match = re.search(f'{resource_type}[s]?\s+([a-zA-Z0-9-]+)', task.description, re.IGNORECASE)
            if resource_match:
                resource_name = resource_match.group(1)
                
                # Get events related to this specific resource
                resource_events = self.events_client.get_events(
                    namespace=namespace,
                    field_selector=f"involvedObject.name={resource_name}",
                    time_window_minutes=120  # Look back further for specific resources
                )
                
                if resource_events:
                    evidence.append(Evidence(
                        resource_type=f"{resource_type.capitalize()}Events",
                        raw_data=resource_events,
                        analysis=f"Events related to {resource_type} {resource_name} in the last 120 minutes"
                    ))
        
        return evidence
    
    def analyze_evidence(self, evidence: List[Evidence], task: Task) -> Finding:
        """
        Analyze the collected events evidence to produce findings
        
        Args:
            evidence: Collected evidence items
            task: The investigation task
            
        Returns:
            Finding: Analysis results
        """
        logger.info(f"Analyzing events evidence for task: {task.description}")
        
        # Build the analysis prompt
        template = self.system_prompt + """
        ## Task Description
        {task_description}
        
        ## Events Evidence
        {events_evidence}
        
        ## Your Task
        Analyze these Kubernetes events to identify patterns, issues, and root causes that might be related to the task.
        Look for warning events, error patterns, and correlations between events.
        Pay special attention to:
        - Pod lifecycle issues (scheduling, termination)
        - Container failures and restarts
        - Image pull errors
        - Resource constraints (CPU, memory, disk)
        - Node problems
        - Networking issues
        - Configuration problems
        
        ## Output Format
        Provide your analysis in the following JSON format:
        ```json
        {{
          "analysis": "Overall analysis of the events and what they indicate",
          "confidence": "Float between 0.0 and 1.0 indicating confidence in the analysis",
          "potential_issues": ["List of potential issues identified from the events"],
          "significant_events": [
            {{
              "type": "Warning/Normal",
              "reason": "The event reason",
              "description": "What this event indicates",
              "impact": "The impact of this event",
              "related_resources": ["Resources affected by or related to this event"]
            }}
          ],
          "timeline": "Brief chronological summary of key events",
          "affected_components": ["List of affected components or resources"]
        }}
        ```
        """
        
        # Format the events evidence for the prompt
        events_evidence_str = ""
        for i, ev in enumerate(evidence):
            # Format events data in a readable way
            formatted_events = []
            raw_data = ev.raw_data
            
            if isinstance(raw_data, list):
                # Sort events by timestamp if available
                try:
                    # Try to sort by last_timestamp first, falling back to first_timestamp
                    raw_data = sorted(
                        raw_data, 
                        key=lambda x: x.get("last_timestamp") or x.get("first_timestamp") or "",
                        reverse=True
                    )
                except:
                    # If sorting fails, just use the original order
                    pass
                
                # Limit to most recent/relevant events
                raw_data = raw_data[:15]  # Show at most 15 events to avoid overwhelming the LLM
                
                for event in raw_data:
                    # Format each event as a concise string
                    event_str = (
                        f"[{event.get('type', 'Unknown')}] "
                        f"{event.get('last_timestamp', event.get('first_timestamp', 'Unknown time'))} "
                        f"{event.get('reason', 'Unknown reason')}: "
                        f"{event.get('message', 'No message')} "
                        f"(Object: {event.get('involved_object', {}).get('kind', 'Unknown')}/"
                        f"{event.get('involved_object', {}).get('name', 'unknown')})"
                    )
                    formatted_events.append(event_str)
                
                raw_data_str = "\n".join(formatted_events)
            else:
                # If not a list, just use the string representation
                raw_data_str = str(raw_data)
                
            events_evidence_str += f"--- Events Evidence #{i+1}: {ev.analysis} ---\n{raw_data_str}\n\n"
        
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
                "events_evidence": events_evidence_str
            })
        except Exception as e:
            logger.error(f"Error analyzing events evidence: {e}")
            result = {
                "analysis": f"Error analyzing events: {str(e)}",
                "confidence": 0.1,
                "potential_issues": ["Error during events analysis"],
                "significant_events": [],
                "timeline": "Could not generate timeline due to analysis error",
                "affected_components": []
            }
        
        # Convert the result to a Finding
        return Finding(
            agent_type="events",
            evidence=evidence,
            analysis=result.get("analysis", "No analysis available"),
            confidence=float(result.get("confidence", 0.5)),
            potential_issues=result.get("potential_issues", [])
        )
    
    def investigate(self, task: Task) -> Finding:
        """
        Perform an events investigation for the given task
        
        Args:
            task: The investigation task
            
        Returns:
            Finding: Investigation results
        """
        logger.info(f"Starting events investigation for task: {task.description}")
        
        # Collect evidence
        evidence = self.collect_events_evidence(task)
        
        # If no evidence was collected, return a default finding
        if not evidence:
            return Finding(
                agent_type="events",
                evidence=[],
                analysis="No Kubernetes events were found relevant to the task. This could mean that the issues "
                         "are not reflected in events, or that events have aged out of the system.",
                confidence=0.1,
                potential_issues=["No relevant Kubernetes events found", "Events may have aged out of the system"]
            )
        
        # Analyze the evidence
        return self.analyze_evidence(evidence, task) 