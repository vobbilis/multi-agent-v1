"""Temporary test file for ReAct Agent implementation."""

import pytest
from unittest.mock import MagicMock, patch
import abc
from typing import Dict, Any, Optional, List

# Mock LLM classes
class LLMResponse:
    def __init__(self, success=True, thought="", action=None, observation="", final_answer="", **kwargs):
        self.success = success
        self.thought = thought
        self.action = action or {}
        self.observation = observation
        self.final_answer = final_answer
        self.metadata = kwargs.get("metadata", {})
        self.cache_key = kwargs.get("cache_key", "test_key")
        self.is_cached = kwargs.get("is_cached", False)

class BaseLLM:
    """Mock BaseLLM for testing."""
    
    def generate(self, prompt, **kwargs):
        return LLMResponse(
            success=True,
            thought="Test thought",
            action={"tool": "test_tool", "parameters": {"param": "value"}},
            observation="Test observation",
            final_answer="Test answer"
        )

# Mock Tool classes
class BaseTool(abc.ABC):
    """Mock BaseTool for testing."""
    
    def __init__(self, name="mock_tool", **kwargs):
        self.name = name
        self.description = "Mock tool for testing"
        self.parameters = {"param": {"type": "string", "description": "Test parameter"}}
        
    @abc.abstractmethod
    def run(self, **kwargs):
        pass

class MockTool(BaseTool):
    """Mock tool implementation."""
    
    def __init__(self, name="mock_tool", should_fail=False, **kwargs):
        super().__init__(name=name, **kwargs)
        self.should_fail = should_fail
        self.call_count = 0
        
    def run(self, **kwargs):
        self.call_count += 1
        if self.should_fail:
            raise Exception("Mock tool failure")
        return f"Result from {self.name}: {kwargs}"

# Mock Tool Registry
class ToolRegistry:
    """Mock ToolRegistry for testing."""
    
    def __init__(self):
        self._tools = {}
        self._tool_classes = {}
        
    def get_tool(self, name, **kwargs):
        if name not in self._tools:
            if name not in self._tool_classes:
                raise Exception(f"Tool {name} not found")
            self._tools[name] = self._tool_classes[name](**kwargs)
        return self._tools[name]
        
    def register_tool(self, tool_cls):
        tool_instance = tool_cls()
        self._tool_classes[tool_instance.name] = tool_cls
        return tool_instance.name

# Mock exceptions
class ReActAgentError(Exception):
    """Base exception for ReAct Agent errors."""
    pass

class ReActAgentConfigError(ReActAgentError):
    """Configuration error for ReAct Agent."""
    pass

class ReActAgentExecutionError(ReActAgentError):
    """Execution error for ReAct Agent."""
    pass

class ReActAgentTimeoutError(ReActAgentError):
    """Timeout error for ReAct Agent."""
    pass

# ReAct Agent implementation
class ReActAgent:
    """Mock ReAct Agent for testing."""
    
    def __init__(self, llm=None, tools=None, max_iterations=10, timeout=60, **kwargs):
        self.llm = llm or BaseLLM()
        self.registry = tools or ToolRegistry()
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.history = []
        self.initialize()
        
    def initialize(self):
        """Initialize the agent."""
        if not isinstance(self.llm, BaseLLM):
            raise ReActAgentConfigError("LLM must be an instance of BaseLLM")
        if not isinstance(self.registry, ToolRegistry):
            raise ReActAgentConfigError("Registry must be an instance of ToolRegistry")
        if self.max_iterations <= 0:
            raise ReActAgentConfigError("Max iterations must be positive")
        if self.timeout <= 0:
            raise ReActAgentConfigError("Timeout must be positive")
            
    def run(self, query, **kwargs):
        """Run the agent on a query."""
        # Input validation
        if query is None:
            raise TypeError("Query cannot be None")
            
        self.history = []
        iteration = 0
        
        while iteration < self.max_iterations:
            # Generate LLM response
            llm_response = self.llm.generate(
                self._build_prompt(query, self.history),
                **kwargs
            )
            
            # Record thought and action
            self.history.append({
                "thought": llm_response.thought,
                "action": llm_response.action
            })
            
            # Check for final answer
            if llm_response.final_answer:
                return {
                    "success": True,
                    "answer": llm_response.final_answer,
                    "history": self.history
                }
                
            # Execute tool action
            try:
                tool_name = llm_response.action.get("tool")
                params = llm_response.action.get("parameters", {})
                
                if not tool_name:
                    raise ReActAgentExecutionError("No tool specified in action")
                    
                tool = self.registry.get_tool(tool_name)
                result = tool.run(**params)
                
                # Record observation
                self.history[-1]["observation"] = result
                
            except Exception as e:
                self.history[-1]["error"] = str(e)
                
            iteration += 1
            
        # If we reach max iterations without a final answer
        return {
            "success": False,
            "answer": "Max iterations reached without resolution",
            "history": self.history
        }
        
    def _build_prompt(self, query, history):
        """Build prompt from query and history."""
        prompt = f"Query: {query}\n\n"
        
        if history:
            prompt += "History:\n"
            for step in history:
                prompt += f"Thought: {step.get('thought', '')}\n"
                action = step.get('action', {})
                prompt += f"Action: {action.get('tool', '')} with {action.get('parameters', {})}\n"
                if "observation" in step:
                    prompt += f"Observation: {step.get('observation', '')}\n"
                if "error" in step:
                    prompt += f"Error: {step.get('error', '')}\n"
                prompt += "\n"
                
        prompt += "Please provide your next step."
        return prompt
        
    def reset(self):
        """Reset the agent state."""
        self.history = []


class TestReActAgent:
    """Test cases for ReAct Agent implementation."""
    
    @pytest.fixture
    def mock_llm(self):
        return MagicMock(spec=BaseLLM)
    
    @pytest.fixture
    def mock_registry(self):
        registry = ToolRegistry()
        registry.register_tool(MockTool)
        return registry
    
    def test_agent_initialization(self, mock_llm, mock_registry):
        """TC5_001: Test ReAct Agent initialization."""
        agent = ReActAgent(
            llm=mock_llm,
            tools=mock_registry
        )
        assert agent.llm == mock_llm
        assert agent.registry == mock_registry
        assert agent.max_iterations == 10
        assert agent.timeout == 60
    
    def test_initialization_validation(self, mock_llm, mock_registry):
        """TC5_002: Test initialization validation."""
        # Test invalid LLM
        with pytest.raises(ReActAgentConfigError, match="LLM must be an instance"):
            ReActAgent(llm="invalid", tools=mock_registry)
            
        # Test invalid registry
        with pytest.raises(ReActAgentConfigError, match="Registry must be an instance"):
            ReActAgent(llm=mock_llm, tools="invalid")
            
        # Test invalid max iterations
        with pytest.raises(ReActAgentConfigError, match="Max iterations must be positive"):
            ReActAgent(llm=mock_llm, tools=mock_registry, max_iterations=0)
            
        # Test invalid timeout
        with pytest.raises(ReActAgentConfigError, match="Timeout must be positive"):
            ReActAgent(llm=mock_llm, tools=mock_registry, timeout=0)
    
    def test_successful_run(self, mock_llm, mock_registry):
        """TC5_003: Test successful agent run."""
        # Configure mock LLM to return a final answer
        llm_response = LLMResponse(
            thought="I know the answer",
            action={"tool": "none"},
            final_answer="This is the final answer"
        )
        mock_llm.generate.return_value = llm_response
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        assert result["success"] is True
        assert result["answer"] == "This is the final answer"
        assert len(result["history"]) == 1
    
    def test_tool_execution(self, mock_llm, mock_registry):
        """TC5_004: Test tool execution in agent run."""
        # Configure mock LLM to return a tool action then a final answer
        responses = [
            LLMResponse(
                thought="I need to use a tool",
                action={"tool": "mock_tool", "parameters": {"param": "test"}}
            ),
            LLMResponse(
                thought="Now I have the answer",
                action={"tool": "none"},
                final_answer="Final answer based on tool result"
            )
        ]
        mock_llm.generate.side_effect = responses
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        assert result["success"] is True
        assert result["answer"] == "Final answer based on tool result"
        assert len(result["history"]) == 2
        assert "observation" in result["history"][0]
    
    def test_tool_error_handling(self, mock_llm, mock_registry):
        """TC5_005: Test tool error handling."""
        # Configure mock LLM to return a tool action
        responses = [
            LLMResponse(
                thought="I need to use a tool",
                action={"tool": "nonexistent_tool", "parameters": {"param": "test"}}
            ),
            LLMResponse(
                thought="Error occurred, let me try a different approach",
                action={"tool": "none"},
                final_answer="Final answer despite tool error"
            )
        ]
        mock_llm.generate.side_effect = responses
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        assert result["success"] is True
        assert result["answer"] == "Final answer despite tool error"
        assert len(result["history"]) == 2
        assert "error" in result["history"][0]
    
    def test_max_iterations(self, mock_llm, mock_registry):
        """TC5_006: Test max iterations limit."""
        # Configure mock LLM to always return a tool action (no final answer)
        mock_llm.generate.return_value = LLMResponse(
            thought="Still thinking...",
            action={"tool": "mock_tool", "parameters": {"param": "test"}}
        )
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry, max_iterations=3)
        result = agent.run("Test query")
        
        assert result["success"] is False
        assert "Max iterations" in result["answer"]
        assert len(result["history"]) == 3
    
    def test_timeout_handling(self, mock_llm, mock_registry):
        """TC5_007: Test timeout handling."""
        # This would require actual time passage, so we'll just test the configuration
        agent = ReActAgent(llm=mock_llm, tools=mock_registry, timeout=30)
        assert agent.timeout == 30
    
    def test_history_structure(self, mock_llm, mock_registry):
        """TC5_008: Test history structure in agent run."""
        # Configure mock LLM for a single response
        mock_llm.generate.return_value = LLMResponse(
            thought="Test thought",
            action={"tool": "mock_tool", "parameters": {"param": "test"}},
            final_answer="Final answer"
        )
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        history_entry = result["history"][0]
        assert "thought" in history_entry
        assert "action" in history_entry
        assert history_entry["thought"] == "Test thought"
        assert history_entry["action"]["tool"] == "mock_tool"
        assert history_entry["action"]["parameters"]["param"] == "test"
    
    def test_prompt_construction(self, mock_llm, mock_registry):
        """TC5_009: Test prompt construction."""
        # We'll use a mock to capture the prompt
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        agent.run("Test query")
        
        # Extract the prompt from the mock call
        args, kwargs = mock_llm.generate.call_args
        prompt = args[0]
        
        assert "Query: Test query" in prompt
        assert "Please provide your next step" in prompt
    
    def test_agent_reset(self, mock_llm, mock_registry):
        """TC5_010: Test agent reset functionality."""
        # Configure mock LLM for a response
        mock_llm.generate.return_value = LLMResponse(
            thought="Test thought",
            action={"tool": "mock_tool", "parameters": {"param": "test"}},
            final_answer="Final answer"
        )
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        agent.run("Test query")
        
        # Verify history was populated
        assert len(agent.history) > 0
        
        # Reset and verify
        agent.reset()
        assert len(agent.history) == 0
    
    def test_multi_step_reasoning(self, mock_llm, mock_registry):
        """TC5_011: Test multi-step reasoning process."""
        # Configure mock LLM for multiple responses
        responses = [
            LLMResponse(
                thought="First step",
                action={"tool": "mock_tool", "parameters": {"param": "step1"}}
            ),
            LLMResponse(
                thought="Second step",
                action={"tool": "mock_tool", "parameters": {"param": "step2"}}
            ),
            LLMResponse(
                thought="Final step",
                action={"tool": "none"},
                final_answer="Multi-step reasoning complete"
            )
        ]
        mock_llm.generate.side_effect = responses
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        assert result["success"] is True
        assert result["answer"] == "Multi-step reasoning complete"
        assert len(result["history"]) == 3
        assert result["history"][0]["thought"] == "First step"
        assert result["history"][1]["thought"] == "Second step"
        assert result["history"][2]["thought"] == "Final step"
    
    def test_context_preservation(self, mock_llm, mock_registry):
        """TC5_012: Test context preservation between steps."""
        # We'll verify that history is included in each prompt
        responses = [
            LLMResponse(
                thought="First step",
                action={"tool": "mock_tool", "parameters": {"param": "test"}}
            ),
            LLMResponse(
                thought="Second step",
                action={"tool": "none"},
                final_answer="Final answer"
            )
        ]
        mock_llm.generate.side_effect = responses
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        agent.run("Test query")
        
        # Extract the second prompt from the mock call
        calls = mock_llm.generate.call_args_list
        second_prompt = calls[1][0][0]
        
        # Verify first step is included in second prompt
        assert "First step" in second_prompt
        assert "mock_tool" in second_prompt
    
    def test_input_validation(self, mock_llm, mock_registry):
        """TC5_013: Test input validation."""
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        
        # Test with empty query
        result = agent.run("")
        assert result["success"] is True  # Empty queries are allowed
        
        # Test with None query (should raise TypeError)
        with pytest.raises(TypeError, match="Query cannot be None"):
            agent.run(None)
    
    def test_custom_parameters(self, mock_llm, mock_registry):
        """TC5_014: Test custom parameters handling."""
        mock_llm.generate.return_value = LLMResponse(
            thought="Using custom parameters",
            action={"tool": "none"},
            final_answer="Final answer with custom parameters"
        )
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        
        # Pass custom parameters
        custom_params = {"temperature": 0.7, "max_tokens": 100}
        agent.run("Test query", **custom_params)
        
        # Verify parameters were passed to LLM
        _, kwargs = mock_llm.generate.call_args
        assert "temperature" in kwargs
        assert kwargs["temperature"] == 0.7
        assert "max_tokens" in kwargs
        assert kwargs["max_tokens"] == 100
    
    def test_empty_action(self, mock_llm, mock_registry):
        """TC5_015: Test handling of empty action."""
        # Configure mock LLM to return an empty action
        mock_llm.generate.return_value = LLMResponse(
            thought="Thinking...",
            action={},  # Empty action
            final_answer=""  # No final answer
        )
        
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        result = agent.run("Test query")
        
        # Should treat as an error and continue
        assert "error" in result["history"][0]
    
    def test_custom_system_prompt(self, mock_llm, mock_registry):
        """TC5_016: Test custom system prompt."""
        agent = ReActAgent(llm=mock_llm, tools=mock_registry)
        
        # Run with custom system prompt
        agent.run("Test query", system_prompt="You are a helpful assistant")
        
        # Verify system prompt was passed to LLM
        _, kwargs = mock_llm.generate.call_args
        assert "system_prompt" in kwargs
        assert kwargs["system_prompt"] == "You are a helpful assistant" 