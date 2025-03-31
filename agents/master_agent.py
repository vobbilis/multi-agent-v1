"""
Master Agent Coordinator for Kubernetes Root Cause Analysis
"""
import json
import logging
import os
from typing import Dict, List, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master coordinator agent for the Kubernetes root cause analysis system.
    This agent orchestrates the investigation process by:
    1. Assessing initial symptoms
    2. Formulating an investigation plan
    3. Coordinating specialist agents
    4. Analyzing findings and evidence
    5. Determining root causes
    6. Generating recommendations
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0, explain_reasoning: bool = False):
        """
        Initialize the master agent with LLM settings
        
        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for LLM output
            explain_reasoning: Whether to explain reasoning before execution
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.system_prompt = """
        You are the master coordinator agent in a Kubernetes root cause analysis system.
        Your job is to coordinate a multi-agent investigation into Kubernetes issues.
        
        You need to:
        1. Assess initial symptoms
        2. Formulate investigation plans
        3. Direct specialist agents
        4. Analyze findings
        5. Determine root causes
        6. Generate recommendations
        
        Based on the current state of the investigation and evidence collected,
        determine the next steps and update the investigation state.
        
        Think step by step. First understand the current phase and evidence, then
        reason through the most likely causes, and finally determine the next actions.
        """
        self.investigation_history = []
        self.confidence_history = {}
        self.explain_reasoning = explain_reasoning
        
    def _create_assessment_prompt(self, symptoms: str) -> ChatPromptTemplate:
        """
        Create the prompt for initial assessment of symptoms
        
        Args:
            symptoms: The initial symptoms reported
            
        Returns:
            ChatPromptTemplate: The prompt for initial assessment
        """
        template = self.system_prompt + """
        ## Initial Symptoms
        {symptoms}
        
        ## Task
        Perform an initial assessment of these symptoms. Think about what could be causing
        these issues in a Kubernetes environment. Consider problems related to:
        
        - Cluster infrastructure (nodes, resources)
        - Control plane components (API Server, Scheduler, Controller Manager, ETCD)
        - Networking (services, DNS, connectivity)
        - Workloads (pods, deployments, scheduling)
        - Configuration (manifests, CRDs, RBAC)
        - Resource management (quotas, limits)
        - Metrics and performance (CPU, memory, disk utilization)
        - Cluster state (control plane, etcd)
        - Logs and events
        - Security
        
        ## Reasoning Process (Required)
        First, explain your reasoning process in detail. Think step by step about the symptoms, what they indicate,
        and how different components of a Kubernetes system might be causing these symptoms. Be thorough in your analysis
        and consider multiple possible explanations.

        ## Final Output
        After your reasoning process, output your analysis in the following JSON format:
        ```json
        {{
          "reasoning": "A detailed explanation of your reasoning process, including your step-by-step thought process, analysis of the symptoms, and why you believe your conclusions are correct",
          "investigation_phase": "initial_assessment",
          "initial_hypothesis": {{
            "possible_causes": [list of potential causes],
            "priority_areas": [ordered list of areas to investigate first]
          }},
          "specialist_agents_to_activate": [list of agent types to activate],
          "confidence_scores": {{
            "area1": score (0.0-1.0),
            "area2": score (0.0-1.0),
            ...
          }}
        }}
        ```
        
        For specialist_agents_to_activate, you can choose from: "network", "metrics", "cluster", "workload",
 "config", "state", "logs", "events", "security".
        Note that currently available agents are "network", "metrics", "cluster", "logs", and "events". Choose these agents when appropriate for the investigation.
        """
        return ChatPromptTemplate.from_template(template)
    
    def _create_hypothesis_prompt(self, state: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Create prompt for hypothesis testing phase
        
        Args:
            state: Current investigation state
            
        Returns:
            ChatPromptTemplate: The prompt for hypothesis testing
        """
        template = self.system_prompt + """
        ## Investigation State
        Current phase: {phase}
        Initial symptoms: {symptoms}
        
        ## Current Evidence
        {evidence}
        
        ## Current Findings
        {findings}
        
        ## Current Hypothesis
        {hypothesis}
        
        ## Task
        Based on the evidence collected so far, evaluate the current hypotheses and determine
        which specialist agents should be activated next for deeper investigation.
        
        Consider all aspects that might be relevant:
        
        - Control plane health and functionality (API Server, Scheduler, Controller Manager, ETCD)
        - Cluster object state (Pods, Services, Deployments, etc.)
        - Metrics and resource utilization (CPU, memory, disk)
        - Network connectivity and policies
        
        Remember that resource constraints and control plane issues can manifest as other problems.
        For example, API server slowness might appear as networking timeouts, or scheduler issues
        might manifest as pod placement problems.
        
        ## Reasoning Process (Required)
        First, explain your reasoning process in detail. Think step by step about the evidence you have, how it relates to
        the current hypothesis, and what additional information you need to confirm or refute the hypothesis. Be thorough in
        your analysis of the current state of the investigation.

        ## Final Output
        After your reasoning process, output your analysis in the following JSON format:
        ```json
        {{
          "reasoning": "A detailed explanation of your reasoning process, including your analysis of the current evidence, how it relates to the hypotheses, and why you believe your conclusions are correct",
          "investigation_phase": "hypothesis_testing",
          "current_hypothesis": {{
            "most_likely_causes": [ordered list of most likely causes],
            "focus_areas": [areas requiring further investigation],
            "type": "primary_category_of_issue"
          }},
          "specialist_agents_to_activate": [list of agent types to activate next],
          "confidence_scores": {{
            "area1": score (0.0-1.0),
            "area2": score (0.0-1.0),
            ...
          }}
        }}
        ```
        
        For specialist_agents_to_activate, you can choose from: "network", "metrics", "cluster", "workload",
 "config", "state", "logs", "events", "security".
        Note that currently available agents are "network", "metrics", "cluster", "logs", and "events". Choose these agents when appropriate for the investigation.
        """
        return ChatPromptTemplate.from_template(template)
    
    def _create_determination_prompt(self, state: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Create prompt for root cause determination phase
        
        Args:
            state: Current investigation state
            
        Returns:
            ChatPromptTemplate: The prompt for root cause determination
        """
        template = self.system_prompt + """
        ## Investigation State
        Current phase: {phase}
        Initial symptoms: {symptoms}
        
        ## All Evidence Collected
        {evidence}
        
        ## All Findings
        {findings}
        
        ## Current Hypothesis
        {hypothesis}
        
        ## Confidence Scores
        {confidence_scores}
        
        ## Task
        Based on all evidence and findings, determine the most likely root cause(s) of the 
        reported symptoms. Provide a detailed analysis of why this is the root cause and
        explain the causal relationship between the root cause and the observed symptoms.
        
        Consider how different issues might interact across the layers of a Kubernetes cluster:
        
        - Control plane issues can affect all workloads and services
        - Network policy issues might be exacerbated by CPU throttling
        - Memory constraints might lead to application timeouts that appear as connectivity problems
        - API server performance impacts scheduler decisions and service endpoint updates
        - ETCD performance affects the overall cluster responsiveness
        
        ## Reasoning Process (Required)
        First, explain your reasoning process in detail. Think step by step about all the evidence collected, how it forms
        a coherent explanation, and why your identified root causes are the most likely explanation for the observed symptoms.
        Be thorough in your analysis and consider alternative explanations.

        ## Final Output
        After your reasoning process, output your analysis in the following JSON format:
        ```json
        {{
          "reasoning": "A detailed explanation of your reasoning process, including your analysis of all evidence collected, why you believe the identified root causes are correct, and how they explain the observed symptoms",
          "investigation_phase": "root_cause_determination",
          "root_causes": [
            {{
              "category": "category_of_issue",
              "component": "specific_component",
              "description": "detailed_description",
              "confidence": score (0.0-1.0),
              "supporting_evidence": [list of evidence items that support this conclusion]
            }}
          ],
          "confidence_scores": {{
            "area1": score (0.0-1.0),
            "area2": score (0.0-1.0),
            ...
          }}
        }}
        ```
        """
        return ChatPromptTemplate.from_template(template)
    
    def _create_recommendation_prompt(self, state: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Create prompt for recommendation generation phase
        
        Args:
            state: Current investigation state
            
        Returns:
            ChatPromptTemplate: The prompt for recommendation generation
        """
        template = self.system_prompt + """
        ## Investigation State
        Current phase: {phase}
        Initial symptoms: {symptoms}
        
        ## Root Causes
        {root_causes}
        
        ## All Evidence Collected
        {evidence}
        
        ## Task
        Based on the identified root causes, generate specific, actionable recommendations
        to resolve the issues. Prioritize the recommendations based on:
        
        1. Impact (how much it will resolve the issue)
        2. Effort required (how difficult/risky it is to implement)
        3. Long-term stability (preventing recurrence)
        
        Consider different types of potential issues:
        
        - If control plane issues were identified, include recommendations for stabilizing or
          scaling control plane components (API Server, Scheduler, Controller Manager, ETCD)
        
        - If resource constraints were identified (CPU, memory, disk, etc.), include
          recommendations for addressing these with appropriate resource limits, requests,
          horizontal/vertical scaling, or infrastructure changes
          
        - If there are architectural issues with Kubernetes objects, provide guidance on
          proper deployment patterns, service configurations, or ingress setup
        
        ## Reasoning Process (Required)
        First, explain your reasoning process in detail. Think step by step about the root causes, what actions would
        address them most effectively, how these actions should be prioritized, and why your recommendations will solve the
        problem. Be thorough in your analysis.

        ## Final Output
        After your reasoning process, output your recommendations in the following JSON format:
        ```json
        {{
          "reasoning": "A detailed explanation of your reasoning process, including why you chose these recommendations, how they address the root causes, and why your prioritization makes sense",
          "investigation_phase": "recommendation_generation",
          "recommendations": [
            {{
              "action": "specific_action_to_take",
              "component": "component_to_modify",
              "priority": "high/medium/low",
              "impact": "explanation_of_impact",
              "effort": "estimation_of_effort",
              "instructions": "detailed_instructions"
            }}
          ],
          "next_actions": [ordered list of actions to take],
          "prevention_measures": [measures to prevent recurrence]
        }}
        ```
        """
        return ChatPromptTemplate.from_template(template)
    
    def _select_prompt_by_phase(self, state: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Select the appropriate prompt based on investigation phase
        
        Args:
            state: Current investigation state
            
        Returns:
            ChatPromptTemplate: The appropriate prompt for the current phase
        """
        phase = state.get("investigation_phase", "initial_assessment")
        symptoms = state.get("initial_symptoms", "")
        
        if phase == "initial_assessment":
            return self._create_assessment_prompt(symptoms)
        elif phase == "hypothesis_testing":
            return self._create_hypothesis_prompt(state)
        elif phase == "root_cause_determination":
            return self._create_determination_prompt(state)
        elif phase == "recommendation_generation":
            return self._create_recommendation_prompt(state)
        else:
            # Default to assessment if unknown phase
            return self._create_assessment_prompt(symptoms)
    
    def _advance_phase(self, current_phase: str, confidence_scores: Dict[str, float]) -> str:
        """
        Determine if the investigation should advance to the next phase
        
        Args:
            current_phase: The current investigation phase
            confidence_scores: Current confidence scores
            
        Returns:
            str: The next investigation phase
        """
        # Get highest confidence score
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0
        
        # Phase transition logic
        if current_phase == "initial_assessment":
            return "hypothesis_testing"
        elif current_phase == "hypothesis_testing":
            # Move to determination if we have high confidence
            if max_confidence >= 0.7:
                return "root_cause_determination"
            else:
                return "hypothesis_testing"
        elif current_phase == "root_cause_determination":
            # Move to recommendations if we have very high confidence
            if max_confidence >= 0.8:
                return "recommendation_generation"
            else:
                return "root_cause_determination"
        elif current_phase == "recommendation_generation":
            return "complete"
        
        return current_phase
    
    def _update_confidence_history(self, timestamp: str, confidence_scores: Dict[str, float]) -> None:
        """
        Update the history of confidence scores
        
        Args:
            timestamp: The timestamp to record
            confidence_scores: Current confidence scores
        """
        self.confidence_history[timestamp] = confidence_scores.copy()
    
    def get_reasoning_and_confirm(self, state: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Display the agent's reasoning and wait for user confirmation
        
        Args:
            state: Current investigation state
            result: LLM analysis result
            
        Returns:
            bool: Whether to proceed with the analysis
        """
        if not self.explain_reasoning:
            return True
            
        phase = state.get("investigation_phase", "initial_assessment")
        reasoning = result.get("reasoning", "No detailed reasoning provided.")
        
        print("\n" + "="*80)
        print(f"MASTER AGENT REASONING (Phase: {phase})")
        print("="*80)
        print(reasoning)
        print("\n" + "="*80)
        print("INVESTIGATION PLAN")
        print("="*80)
        
        if phase == "initial_assessment":
            initial_hypothesis = result.get("initial_hypothesis", {})
            
            print("Possible causes:")
            possible_causes = initial_hypothesis.get("possible_causes", [])
            if isinstance(possible_causes, list) and len(possible_causes) > 0:
                # Extract cause descriptions if possible
                for cause in possible_causes:
                    # Check if cause is a dict with explanation
                    if isinstance(cause, dict) and "cause" in cause and "explanation" in cause:
                        print(f"- {cause['cause']}: {cause['explanation']}")
                    else:
                        # Try to generate an explanation for each cause
                        explanation = self._generate_explanation_for_item(cause, reasoning)
                        print(f"- {cause}: {explanation}")
            else:
                print("  No specific causes identified.")
            
            print("\nPriority areas:")
            priority_areas = initial_hypothesis.get("priority_areas", [])
            if isinstance(priority_areas, list) and len(priority_areas) > 0:
                for area in priority_areas:
                    # Check if area is a dict with explanation
                    if isinstance(area, dict) and "area" in area and "reason" in area:
                        print(f"- {area['area']}: {area['reason']}")
                    else:
                        explanation = self._generate_explanation_for_item(area, reasoning)
                        print(f"- {area}: {explanation}")
            else:
                print("  No priority areas identified.")
                
            print("\nSpecialist agents to activate:")
            for agent in result.get("specialist_agents_to_activate", []):
                explanation = self._get_agent_explanation(agent)
                print(f"- {agent}: {explanation}")
                
        elif phase == "hypothesis_testing":
            current_hypothesis = result.get("current_hypothesis", {})
            
            print("Most likely causes:")
            likely_causes = current_hypothesis.get("most_likely_causes", [])
            if isinstance(likely_causes, list) and len(likely_causes) > 0:
                for cause in likely_causes:
                    if isinstance(cause, dict) and "cause" in cause and "explanation" in cause:
                        print(f"- {cause['cause']}: {cause['explanation']}")
                    else:
                        explanation = self._generate_explanation_for_item(cause, reasoning)
                        print(f"- {cause}: {explanation}")
            else:
                print("  No most likely causes identified.")
                
            print("\nFocus areas:")
            focus_areas = current_hypothesis.get("focus_areas", [])
            if isinstance(focus_areas, list) and len(focus_areas) > 0:
                for area in focus_areas:
                    if isinstance(area, dict) and "area" in area and "reason" in area:
                        print(f"- {area['area']}: {area['reason']}")
                    else:
                        explanation = self._generate_explanation_for_item(area, reasoning)
                        print(f"- {area}: {explanation}")
            else:
                print("  No focus areas identified.")
                
            print("\nSpecialist agents to activate:")
            for agent in result.get("specialist_agents_to_activate", []):
                explanation = self._get_agent_explanation(agent)
                print(f"- {agent}: {explanation}")
                
        elif phase == "root_cause_determination":
            print("Root causes:")
            for rc in result.get("root_causes", []):
                component = rc.get("component", "unknown component")
                description = rc.get("description", "No description provided")
                confidence = int(rc.get("confidence", 0) * 100)
                supporting_evidence = rc.get("supporting_evidence", [])
                
                print(f"- {rc.get('category', 'unknown')}: {component} - {description} (Confidence: {confidence}%)")
                if supporting_evidence:
                    print("  Supporting evidence:")
                    for evidence in supporting_evidence[:3]:  # Limit to top 3 pieces of evidence
                        print(f"  * {evidence}")
                
        elif phase == "recommendation_generation":
            print("Recommendations:")
            for rec in result.get("recommendations", []):
                action = rec.get("action", "unknown action")
                component = rec.get("component", "unknown component")
                priority = rec.get("priority", "unknown")
                impact = rec.get("impact", "No impact information provided")
                
                print(f"- {action} on {component} (Priority: {priority})")
                print(f"  Impact: {impact}")
                print(f"  Effort: {rec.get('effort', 'Not specified')}")
                
            print("\nNext actions:")
            for i, action in enumerate(result.get("next_actions", [])):
                print(f"- {i+1}. {action}")
            
            if "prevention_measures" in result:
                print("\nPrevention measures:")
                for measure in result.get("prevention_measures", []):
                    print(f"- {measure}")
                
        print("\n" + "="*80)
        print("Confidence scores:")
        for area, score in result.get("confidence_scores", {}).items():
            print(f"- {area}: {int(score * 100)}%")
        print("="*80)
        
        while True:
            response = input("\nDo you agree with this reasoning and plan? (yes/no/edit): ").lower()
            if response == "yes" or response == "y":
                return True
            elif response == "no" or response == "n":
                return False
            elif response == "edit" or response == "e":
                print("Edit functionality not implemented yet. Please provide feedback separately.")
                continue
            else:
                print("Invalid response. Please enter 'yes', 'no', or 'edit'.")
    
    def _generate_explanation_for_item(self, item: str, reasoning: str) -> str:
        """
        Generate a brief explanation for a cause or area based on the reasoning text
        
        Args:
            item: The cause or area to explain
            reasoning: The full reasoning text
            
        Returns:
            str: A brief explanation
        """
        # Look for sentences that mention the item in the reasoning
        item_lower = item.lower()
        sentences = reasoning.split('.')
        
        relevant_sentences = []
        for sentence in sentences:
            if item_lower in sentence.lower():
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Get the most informative sentence (usually the longest one)
            relevant_sentences.sort(key=len, reverse=True)
            explanation = relevant_sentences[0]
            
            # Truncate if too long
            if len(explanation) > 100:
                explanation = explanation[:97] + "..."
                
            return explanation
        
        # If no specific mention found, return a generic explanation based on item type
        if "network" in item_lower or "connectivity" in item_lower:
            return "Network issues may be causing connectivity problems between services"
        elif "resource" in item_lower or "cpu" in item_lower or "memory" in item_lower:
            return "Resource constraints might be affecting performance or availability"
        elif "config" in item_lower or "configuration" in item_lower:
            return "Misconfiguration could be leading to unexpected behavior"
        elif "pod" in item_lower or "container" in item_lower:
            return "Container or pod lifecycle issues might be causing failures"
        elif "control plane" in item_lower or "api server" in item_lower:
            return "Control plane components may not be functioning optimally"
        elif "chaos" in item_lower or "experiment" in item_lower:
            return "Chaos engineering experiments could be intentionally causing failures"
        else:
            return "This area requires investigation based on the symptoms observed"
    
    def _get_agent_explanation(self, agent_type: str) -> str:
        """
        Get a standard explanation for why a particular specialist agent is being activated
        
        Args:
            agent_type: The type of specialist agent
            
        Returns:
            str: A brief explanation
        """
        explanation_map = {
            "network": "The Network agent will check connectivity between services, DNS resolution, and network policies that might be affecting pod communication.",
            "metrics": "The Metrics agent will analyze resource usage (CPU/memory) patterns, identify performance bottlenecks, and check for resource constraints.",
            "cluster": "The Cluster agent will examine node health, scheduler decisions, and cluster-wide resource allocation that could impact pod placement.",
            "logs": "The Logs agent will analyze container logs for error patterns, application-specific issues, and stack traces that indicate the root cause.",
            "events": "The Events agent will collect and analyze Kubernetes events for warnings and errors related to pod lifecycle, image pulls, and resource constraints."
        }
        
        return explanation_map.get(agent_type, f"The {agent_type} agent will gather specialized evidence related to this symptom category.")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and determine next steps
        
        Args:
            state: Current investigation state
            
        Returns:
            Dict: Updated investigation state
        """
        # Record the state in history
        self.investigation_history.append(state.copy())
        
        # Get appropriate prompt for current phase
        prompt = self._select_prompt_by_phase(state)
        
        # Parse the current state
        phase = state.get("investigation_phase", "initial_assessment")
        symptoms = state.get("initial_symptoms", "")
        evidence = state.get("evidence", [])
        findings = state.get("findings", {})
        hypothesis = state.get("current_hypothesis", {})
        confidence_scores = state.get("confidence_scores", {})
        root_causes = state.get("root_causes", [])
        
        # Generate analysis using LLM
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Run the chain with appropriate inputs based on phase
        if phase == "initial_assessment":
            result = chain.invoke({"symptoms": symptoms})
        else:
            result = chain.invoke({
                "phase": phase,
                "symptoms": symptoms,
                "evidence": evidence,
                "findings": findings,
                "hypothesis": hypothesis,
                "confidence_scores": confidence_scores,
                "root_causes": root_causes
            })
        
        # Display reasoning and get confirmation
        if not self.get_reasoning_and_confirm(state, result):
            logger.warning("User rejected the master agent's reasoning. Investigation halted.")
            return {"investigation_phase": "halted_by_user", **state}
        
        # Determine if phase should advance
        next_phase = self._advance_phase(
            result.get("investigation_phase", phase),
            result.get("confidence_scores", {})
        )
        result["investigation_phase"] = next_phase
        
        # Update confidence history
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        self._update_confidence_history(timestamp, result.get("confidence_scores", {}))
        
        # Log the decision
        logger.info(f"Investigation advancing from {phase} to {next_phase}")
        
        # Create updated state
        updated_state = {
            # Update with new results
            "investigation_phase": next_phase,
            "confidence_scores": result.get("confidence_scores", {}),
            
            # Conditionally update based on phase
            "current_hypothesis": result.get("current_hypothesis", hypothesis),
            "specialist_agents_to_activate": result.get("specialist_agents_to_activate", []),
            "root_causes": result.get("root_causes", root_causes),
            "recommendations": result.get("recommendations", []),
            "next_actions": result.get("next_actions", []),
            "prevention_measures": result.get("prevention_measures", []),
            
            # Preserve existing state elements
            "initial_symptoms": symptoms,
            "evidence": evidence,
            "findings": findings,
            
            # Add metadata
            "timestamp": timestamp,
            "confidence_history": self.confidence_history
        }
        
        return updated_state
    
    def get_investigation_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the investigation
        
        Returns:
            Dict: Summary of the investigation
        """
        # Get the latest state
        if not self.investigation_history:
            return {"status": "No investigation has been conducted"}
        
        latest_state = self.investigation_history[-1]
        
        # Create summary
        summary = {
            "status": "complete" if latest_state.get("investigation_phase") == "complete" else "in_progress"
,
            "initial_symptoms": latest_state.get("initial_symptoms", ""),
            "phases_completed": [state.get("investigation_phase") for state in self.investigation_history],
            "root_causes": latest_state.get("root_causes", []),
            "next_actions": latest_state.get("next_actions", []),
            "confidence_scores": latest_state.get("confidence_scores", {}),
            "specialist_agents_activated": []
        }
        
        # Collect all specialist agents activated
        for state in self.investigation_history:
            agents = state.get("specialist_agents_to_activate", [])
            if agents:
                summary["specialist_agents_activated"].extend(agents)
        
        # Remove duplicates
        summary["specialist_agents_activated"] = list(set(summary["specialist_agents_activated"]))
        
        return summary

# Example of usage
if __name__ == "__main__":
    master_agent = MasterAgent(explain_reasoning=True)
    
    # Initial state with symptoms
    initial_state = {
        "investigation_phase": "initial_assessment",
        "initial_symptoms": """
        Several pods in the production namespace keep restarting with CrashLoopBackOff status.
        The application logs show connection timeouts when trying to reach the database service.
        This started approximately 30 minutes after a network policy update was applied.
        CPU and memory metrics show high utilization during the timeouts.
        Control plane nodes are reporting disk pressure warnings.
        """
    }
    
    # Process initial state
    result = master_agent(initial_state)
    
    # Print the result
    print(json.dumps(result, indent=2)) 