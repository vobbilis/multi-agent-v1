"""Integration tests for tools and LLM interaction."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from k8s_analyzer.tools import (
    get_tool_registry,
    KubectlTool,
    ToolResult
)
from k8s_analyzer.llm import (
    get_llm_client,
    LLMResponse
)
from k8s_analyzer.react import (
    ReActAgent,
    AgentState
)

@pytest.fixture
def test_fixtures_dir():
    """Get the test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "tools"

@pytest.fixture
def pod_fixture(test_fixtures_dir):
    """Load pod fixture data."""
    with open(test_fixtures_dir / "pod.json") as f:
        return json.load(f)

@pytest.fixture
def node_fixture(test_fixtures_dir):
    """Load node fixture data."""
    with open(test_fixtures_dir / "node.json") as f:
        return json.load(f)

@pytest.fixture
def metrics_fixture(test_fixtures_dir):
    """Load metrics fixture data."""
    with open(test_fixtures_dir / "metrics.json") as f:
        return json.load(f)

@pytest.fixture
def mock_kubectl_tool(pod_fixture, node_fixture, metrics_fixture):
    """Create a mock kubectl tool."""
    tool = MagicMock(spec=KubectlTool)
    
    def mock_execute(**kwargs):
        if kwargs.get("resource") == "pods":
            data = pod_fixture
        elif kwargs.get("resource") == "nodes":
            data = node_fixture
        elif kwargs.get("resource") == "metrics":
            data = metrics_fixture
        else:
            data = {"items": []}
        
        return ToolResult(
            success=True,
            data=data,
            error=None,
            execution_time=0.1,
            timestamp="2024-03-30T06:10:00Z",
            metadata={"tool": "kubectl"}
        )
    
    tool.execute.side_effect = mock_execute
    return tool

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    
    def mock_generate(**kwargs):
        return LLMResponse(
            thought="Analyzing cluster resources",
            action={
                "tool": "kubectl",
                "parameters": {
                    "command": "get",
                    "resource": "pods",
                    "namespace": "default",
                    "output": "json"
                }
            },
            observation="Retrieved pod information",
            final_answer="Analysis complete"
        )
    
    client.generate.side_effect = mock_generate
    return client

@pytest.mark.integration
class TestToolsLLMIntegration:
    """Integration tests for tools and LLM interaction."""
    
    def test_tool_execution_in_react_loop(
        self,
        mock_kubectl_tool,
        mock_llm_client
    ):
        """Test tool execution within ReAct loop."""
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Run analysis
        result = agent.analyze_question(
            "What pods are running in the default namespace?"
        )
        
        # Verify LLM was called
        assert mock_llm_client.generate.called
        
        # Verify tool was executed
        assert mock_kubectl_tool.execute.called
        
        # Verify result contains pod data
        assert result.success
        assert "pods" in result.data
    
    def test_tool_error_handling_in_react_loop(
        self,
        mock_kubectl_tool,
        mock_llm_client
    ):
        """Test error handling in ReAct loop."""
        # Make tool fail
        mock_kubectl_tool.execute.side_effect = Exception("Tool error")
        
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Run analysis
        result = agent.analyze_question(
            "What pods are running in the default namespace?"
        )
        
        # Verify error was handled
        assert not result.success
        assert "Tool error" in result.error
    
    def test_llm_error_handling_in_react_loop(
        self,
        mock_kubectl_tool,
        mock_llm_client
    ):
        """Test LLM error handling in ReAct loop."""
        # Make LLM fail
        mock_llm_client.generate.side_effect = Exception("LLM error")
        
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Run analysis
        result = agent.analyze_question(
            "What pods are running in the default namespace?"
        )
        
        # Verify error was handled
        assert not result.success
        assert "LLM error" in result.error
    
    def test_multi_tool_interaction(
        self,
        mock_kubectl_tool,
        mock_llm_client,
        pod_fixture,
        node_fixture,
        metrics_fixture
    ):
        """Test interaction with multiple tools."""
        # Configure LLM to request multiple tools
        def mock_generate(**kwargs):
            history = kwargs.get("history", [])
            if not history:
                # First call - get pods
                return LLMResponse(
                    thought="Getting pod information",
                    action={
                        "tool": "kubectl",
                        "parameters": {
                            "command": "get",
                            "resource": "pods",
                            "namespace": "default",
                            "output": "json"
                        }
                    },
                    observation=None,
                    final_answer=None
                )
            elif len(history) == 1:
                # Second call - get nodes
                return LLMResponse(
                    thought="Getting node information",
                    action={
                        "tool": "kubectl",
                        "parameters": {
                            "command": "get",
                            "resource": "nodes",
                            "output": "json"
                        }
                    },
                    observation=None,
                    final_answer=None
                )
            else:
                # Final call - get metrics and analyze
                return LLMResponse(
                    thought="Analyzing metrics",
                    action={
                        "tool": "kubectl",
                        "parameters": {
                            "command": "get",
                            "resource": "metrics",
                            "output": "json"
                        }
                    },
                    observation="Retrieved all information",
                    final_answer="Analysis of cluster state complete"
                )
        
        mock_llm_client.generate.side_effect = mock_generate
        
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Run analysis
        result = agent.analyze_question(
            "Analyze the cluster state"
        )
        
        # Verify multiple tool calls
        assert mock_kubectl_tool.execute.call_count == 3
        
        # Verify calls were made with different resources
        calls = mock_kubectl_tool.execute.call_args_list
        resources = [call[1]["resource"] for call in calls]
        assert "pods" in resources
        assert "nodes" in resources
        assert "metrics" in resources
        
        # Verify final result
        assert result.success
        assert "Analysis of cluster state complete" in result.final_answer
    
    def test_human_in_the_loop_interaction(
        self,
        mock_kubectl_tool,
        mock_llm_client
    ):
        """Test human-in-the-loop interaction."""
        # Configure LLM to request dangerous operation
        def mock_generate(**kwargs):
            return LLMResponse(
                thought="Need to delete pod",
                action={
                    "tool": "kubectl",
                    "parameters": {
                        "command": "delete",
                        "resource": "pod",
                        "name": "test-pod",
                        "namespace": "default"
                    }
                },
                observation=None,
                final_answer=None
            )
        
        mock_llm_client.generate.side_effect = mock_generate
        
        # Configure mock tool to require approval
        mock_kubectl_tool.is_dangerous = True
        mock_kubectl_tool.requires_approval = True
        
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Mock human approval
        with patch("builtins.input", return_value="y"):
            result = agent.analyze_question(
                "Remove the test pod"
            )
        
        # Verify tool execution was attempted
        assert mock_kubectl_tool.execute.called
        
        # Verify result
        assert result.success
        assert mock_kubectl_tool.execute.call_args[1]["command"] == "delete"
    
    def test_state_persistence_between_questions(
        self,
        mock_kubectl_tool,
        mock_llm_client
    ):
        """Test state persistence between questions."""
        # Configure LLM responses
        responses = [
            LLMResponse(
                thought="Getting pod information",
                action={
                    "tool": "kubectl",
                    "parameters": {
                        "command": "get",
                        "resource": "pods",
                        "namespace": "default",
                        "output": "json"
                    }
                },
                observation="Found pods",
                final_answer="Pod analysis complete"
            ),
            LLMResponse(
                thought="Using previous pod information",
                action=None,
                observation="Retrieved from history",
                final_answer="Analysis using previous data complete"
            )
        ]
        mock_llm_client.generate.side_effect = responses
        
        # Register mock tool
        registry = get_tool_registry()
        registry.register(mock_kubectl_tool)
        
        # Create agent with mock LLM
        agent = ReActAgent(llm_client=mock_llm_client)
        
        # Run first analysis
        result1 = agent.analyze_question(
            "What pods are running?"
        )
        
        # Run second analysis
        result2 = agent.analyze_question(
            "Analyze those pods"
        )
        
        # Verify tool was only called once
        assert mock_kubectl_tool.execute.call_count == 1
        
        # Verify both results
        assert result1.success
        assert result2.success
        assert "Pod analysis complete" in result1.final_answer
        assert "Analysis using previous data" in result2.final_answer 