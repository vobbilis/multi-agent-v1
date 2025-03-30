"""Unit tests for the ReAct agent implementation."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from k8s_analyzer.react import (
    ReActAgent,
    AgentState,
    AgentError,
    AgentValidationError,
    AgentExecutionError
)
from k8s_analyzer.llm import BaseLLM, LLMResponse
from k8s_analyzer.tools import BaseTool, ToolResult

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def _initialize(self) -> None:
        pass
    
    def _generate(self, prompt: str, **kwargs):
        return {
            "thought": "Test thought",
            "action": {
                "tool": "mock_tool",
                "parameters": {"test": "value"}
            },
            "observation": "Test observation",
            "final_answer": "Test answer"
        }

class MockTool(BaseTool):
    """Mock tool for testing."""
    name = "mock_tool"
    description = "Mock tool for testing"
    required_permissions = ["test"]
    is_dangerous = False
    
    def _initialize(self) -> None:
        pass
    
    def _execute(self, context):
        return {"result": "success"}

@pytest.fixture
def mock_llm():
    """Fixture for mock LLM."""
    return MockLLM()

@pytest.fixture
def mock_tool():
    """Fixture for mock tool."""
    return MockTool()

@pytest.fixture
def agent(mock_llm, mock_tool):
    """Fixture for ReAct agent."""
    agent = ReActAgent(llm_client=mock_llm)
    agent.register_tool(mock_tool)
    return agent

class TestReActAgent:
    """Test cases for ReActAgent class."""
    
    def test_agent_initialization(self, mock_llm):
        """TC5_001: Test basic agent initialization."""
        agent = ReActAgent(llm_client=mock_llm)
        assert isinstance(agent, ReActAgent)
        assert agent.llm_client is mock_llm
    
    def test_tool_registration(self, agent, mock_tool):
        """TC5_002: Test tool registration."""
        # Test duplicate registration
        with pytest.raises(AgentError, match="already registered"):
            agent.register_tool(mock_tool)
        
        # Test tool retrieval
        assert agent.get_tool("mock_tool") is mock_tool
    
    def test_state_initialization(self, agent):
        """TC5_003: Test agent state initialization."""
        state = agent.initialize_state()
        assert isinstance(state, AgentState)
        assert state.session_id
        assert not state.history
    
    def test_successful_analysis(self, agent):
        """TC5_004: Test successful question analysis."""
        result = agent.analyze_question("Test question")
        assert result.success
        assert result.answer == "Test answer"
        assert not result.error
    
    def test_analysis_with_error(self, agent, mock_llm):
        """TC5_005: Test analysis with LLM error."""
        mock_llm._generate = MagicMock(side_effect=Exception("LLM error"))
        result = agent.analyze_question("Test question")
        assert not result.success
        assert "LLM error" in result.error
    
    def test_conversation_history(self, agent):
        """TC5_006: Test conversation history management."""
        # First question
        result1 = agent.analyze_question("First question")
        assert len(agent.state.history) == 1
        
        # Second question
        result2 = agent.analyze_question("Second question")
        assert len(agent.state.history) == 2
        
        # Verify history structure
        assert agent.state.history[0]["role"] == "user"
        assert agent.state.history[1]["role"] == "assistant"
    
    def test_action_execution(self, agent, mock_tool):
        """TC5_007: Test action execution."""
        action = {
            "tool": "mock_tool",
            "parameters": {"test": "value"}
        }
        result = agent.execute_action(action)
        assert result.success
        assert result.data["result"] == "success"
    
    def test_action_validation(self, agent):
        """TC5_008: Test action validation."""
        # Missing tool
        with pytest.raises(AgentValidationError):
            agent.execute_action({
                "parameters": {"test": "value"}
            })
        
        # Invalid tool
        with pytest.raises(AgentValidationError):
            agent.execute_action({
                "tool": "invalid_tool",
                "parameters": {"test": "value"}
            })
        
        # Missing parameters
        with pytest.raises(AgentValidationError):
            agent.execute_action({
                "tool": "mock_tool"
            })
    
    def test_iteration_limit(self, agent, mock_llm):
        """TC5_009: Test iteration limit handling."""
        # Make LLM never reach final answer
        def no_final_answer(*args, **kwargs):
            return {
                "thought": "Thinking...",
                "action": {
                    "tool": "mock_tool",
                    "parameters": {"test": "value"}
                },
                "observation": "Observing...",
                "final_answer": None
            }
        mock_llm._generate = no_final_answer
        
        result = agent.analyze_question(
            "Test question",
            max_iterations=3
        )
        assert not result.success
        assert "Maximum iterations reached" in result.error
    
    def test_human_interaction(self, agent, mock_tool):
        """TC5_010: Test human interaction handling."""
        # Make tool require approval
        mock_tool.is_dangerous = True
        mock_tool.requires_approval = True
        
        with patch("builtins.input", return_value="y"):
            result = agent.analyze_question("Test question")
            assert result.success
            assert "approved by user" in str(result.metadata)
    
    def test_state_persistence(self, agent):
        """TC5_011: Test state persistence."""
        # First analysis
        state1 = agent.state
        result1 = agent.analyze_question("First question")
        
        # Second analysis
        result2 = agent.analyze_question("Second question")
        
        # State should persist
        assert agent.state is state1
        assert len(agent.state.history) == 2
    
    def test_timeout_handling(self, agent, mock_llm):
        """TC5_012: Test timeout handling."""
        def slow_generate(*args, **kwargs):
            import time
            time.sleep(2)
            return mock_llm._generate(*args, **kwargs)
        
        mock_llm._generate = slow_generate
        
        with pytest.raises(TimeoutError):
            agent.analyze_question(
                "Test question",
                timeout=1
            )
    
    def test_conversation_formatting(self, agent):
        """TC5_013: Test conversation formatting."""
        # Add some history
        agent.analyze_question("First question")
        agent.analyze_question("Second question")
        
        formatted = agent.format_conversation()
        assert "First question" in formatted
        assert "Second question" in formatted
        assert "Test answer" in formatted
    
    def test_parallel_analysis(self, agent):
        """TC5_014: Test parallel analysis."""
        import concurrent.futures
        
        questions = [
            "First question",
            "Second question",
            "Third question"
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(agent.analyze_question, q)
                for q in questions
            ]
            results = [f.result() for f in futures]
        
        assert len(results) == len(questions)
        assert all(r.success for r in results)
    
    def test_error_recovery(self, agent, mock_llm):
        """TC5_015: Test error recovery."""
        error_count = 0
        
        def failing_generate(*args, **kwargs):
            nonlocal error_count
            if error_count < 2:
                error_count += 1
                raise Exception("Temporary error")
            return mock_llm._generate(*args, **kwargs)
        
        mock_llm._generate = failing_generate
        
        result = agent.analyze_question(
            "Test question",
            max_retries=3
        )
        assert result.success
        assert error_count == 2
    
    def test_context_handling(self, agent):
        """TC5_016: Test context handling."""
        context = {
            "environment": "test",
            "namespace": "default",
            "timeout": 30
        }
        
        result = agent.analyze_question(
            "Test question",
            context=context
        )
        
        assert result.success
        assert result.context == context 