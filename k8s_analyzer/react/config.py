"""Configuration settings for ReAct agents."""

from typing import Dict, Any
import os

# Agent Configuration
MAX_ITERATIONS: int = int(os.getenv("REACT_MAX_ITERATIONS", "10"))
THOUGHT_PROCESS_TIMEOUT: int = int(os.getenv("REACT_THOUGHT_TIMEOUT", "30"))
ACTION_EXECUTION_TIMEOUT: int = int(os.getenv("REACT_ACTION_TIMEOUT", "60"))

# System Prompts
BASE_SYSTEM_PROMPT: str = """You are an AI agent analyzing a Kubernetes cluster.
Your task is to help diagnose and solve problems by following these steps:
1. Understand the user's question
2. Think about what information you need
3. Choose appropriate tools to gather that information
4. Analyze the results
5. Either gather more information or provide a final answer

Always explain your reasoning and be transparent about your confidence level."""

TOOL_DESCRIPTION_PROMPT: str = """Available tools for analysis:
{tool_descriptions}

For each tool:
- Consider its purpose and limitations
- Use it appropriately in your analysis
- Handle its results correctly"""

ACTION_FORMAT_PROMPT: str = """When proposing actions, use this JSON format:
{
    "type": "action" | "final_answer",
    "action": {
        "tool": "tool_name",
        "parameters": {},
        "reasoning": "Why this action is needed",
        "expected_result": "What you expect to learn"
    }
}

For final answers:
{
    "type": "final_answer",
    "main_response": "Clear explanation of findings",
    "confidence": 0.0-1.0,
    "reasoning": "How you reached this conclusion",
    "next_steps": ["recommended actions"],
    "analyzed_components": ["what was checked"]
}"""

# HITL Configuration
HITL_ENABLED: bool = os.getenv("REACT_HITL_ENABLED", "true").lower() == "true"
HITL_TIMEOUT: int = int(os.getenv("REACT_HITL_TIMEOUT", "300"))
HITL_AUTO_APPROVE_SAFE_ACTIONS: bool = os.getenv("REACT_HITL_AUTO_APPROVE_SAFE", "false").lower() == "true"
AUTO_APPROVE_ACTIONS: bool = os.getenv("REACT_AUTO_APPROVE_ACTIONS", "false").lower() == "true"

# Safe Actions (can be auto-approved if configured)
SAFE_ACTIONS: list[str] = [
    "get_pods",
    "get_nodes",
    "get_services",
    "describe_pod",
    "describe_node",
    "get_events",
    "get_logs"
]

# Dangerous Actions (always require HITL)
DANGEROUS_ACTIONS: list[str] = [
    "delete_pod",
    "drain_node",
    "scale_deployment",
    "rollback_deployment",
    "exec_pod"
]

# Presentation Configuration
DISPLAY_THOUGHT_PROCESS: bool = os.getenv("REACT_DISPLAY_THOUGHTS", "true").lower() == "true"
DISPLAY_TOOL_OUTPUTS: bool = os.getenv("REACT_DISPLAY_OUTPUTS", "true").lower() == "true"
MAX_OUTPUT_WIDTH: int = int(os.getenv("REACT_OUTPUT_WIDTH", "100"))

def get_prompt_template(template_name: str) -> str:
    """Get a prompt template by name."""
    templates = {
        "base": BASE_SYSTEM_PROMPT,
        "tools": TOOL_DESCRIPTION_PROMPT,
        "format": ACTION_FORMAT_PROMPT
    }
    return templates.get(template_name, "")
