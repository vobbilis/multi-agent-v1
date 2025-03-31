"""Integration tests for analyzer and ReAct agent interaction."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from k8s_analyzer.core.analyzer import (
    EnhancedClusterAnalyzer,
    AnalysisResult,
    PressurePoint
)
from k8s_analyzer.react import (
    ReActAgent,
    AgentState
)
from k8s_analyzer.llm import (
    BaseLLM,
    LLMResponse
)
from k8s_analyzer.tools import (
    get_tool_registry,
    KubectlTool,
    ToolResult
)

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def _initialize(self) -> None:
        pass
    
    def _generate(self, *args, **kwargs):
        return {
            "thought": "Analyzing cluster resources",
            "action": {
                "tool": "kubectl",
                "parameters": {
                    "command": "get",
                    "resource": "pods",
                    "namespace": "default",
                    "output": "json"
                }
            },
            "observation": "Retrieved pod information",
            "final_answer": "Analysis complete: Found 2 pods with high resource usage"
        }

@pytest.fixture
def mock_kubectl_tool():
    """Create a mock kubectl tool."""
    tool = MagicMock(spec=KubectlTool)
    
    def mock_execute(**kwargs):
        if kwargs.get("resource") == "pods":
            return ToolResult(
                success=True,
                data={
                    "items": [
                        {
                            "metadata": {
                                "name": "test-pod-1",
                                "namespace": "default"
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "name": "test-container",
                                        "resources": {
                                            "requests": {
                                                "cpu": "100m",
                                                "memory": "128Mi"
                                            },
                                            "limits": {
                                                "cpu": "200m",
                                                "memory": "256Mi"
                                            }
                                        }
                                    }
                                ]
                            },
                            "status": {
                                "phase": "Running",
                                "containerStatuses": [
                                    {
                                        "name": "test-container",
                                        "ready": True,
                                        "restartCount": 5
                                    }
                                ]
                            }
                        }
                    ]
                },
                error=None,
                execution_time=0.1,
                timestamp=datetime.now().isoformat(),
                metadata={"tool": "kubectl"}
            )
        elif kwargs.get("resource") == "nodes":
            return ToolResult(
                success=True,
                data={
                    "items": [
                        {
                            "metadata": {
                                "name": "test-node"
                            },
                            "status": {
                                "capacity": {
                                    "cpu": "4",
                                    "memory": "8Gi"
                                },
                                "allocatable": {
                                    "cpu": "3800m",
                                    "memory": "7Gi"
                                }
                            }
                        }
                    ]
                },
                error=None,
                execution_time=0.1,
                timestamp=datetime.now().isoformat(),
                metadata={"tool": "kubectl"}
            )
        return ToolResult(
            success=True,
            data={"items": []},
            error=None,
            execution_time=0.1,
            timestamp=datetime.now().isoformat(),
            metadata={"tool": "kubectl"}
        )
    
    tool.execute.side_effect = mock_execute
    return tool

@pytest.fixture
def analyzer(mock_kubectl_tool):
    """Create an analyzer instance with mocked dependencies."""
    # Register mock tool
    registry = get_tool_registry()
    registry.register(mock_kubectl_tool)
    
    # Create ReAct agent with mock LLM
    agent = ReActAgent(llm_client=MockLLM())
    
    return EnhancedClusterAnalyzer(
        agent=agent,
        tools={"kubectl": mock_kubectl_tool}
    )

@pytest.mark.integration
class TestAnalyzerReActIntegration:
    """Integration tests for analyzer and ReAct agent."""
    
    def test_basic_analysis(self, analyzer):
        """Test basic cluster analysis."""
        result = analyzer.analyze_question(
            "What is the current cluster state?"
        )
        
        assert result.success
        assert "Found 2 pods" in result.answer
        assert not result.error
    
    def test_pressure_point_analysis(self, analyzer):
        """Test pressure point analysis."""
        result = analyzer.analyze_pressure_points()
        
        assert result
        assert any(p.resource == "test-pod-1" for p in result)
        assert any(p.severity > 0 for p in result)
    
    def test_interactive_analysis(self, analyzer):
        """Test interactive analysis mode."""
        questions = [
            "Check pod status",
            "Analyze node resources",
            "exit"
        ]
        
        with patch("builtins.input", side_effect=questions):
            analyzer.run_interactive_mode()
        
        # Verify tool was called for each question
        assert analyzer.tools["kubectl"].execute.call_count == 2
    
    def test_analysis_with_context(self, analyzer):
        """Test analysis with context."""
        context = {
            "namespace": "default",
            "resource_type": "pods",
            "time_window": "1h"
        }
        
        result = analyzer.analyze_with_context(
            "What resources are under pressure?",
            context
        )
        
        assert result.success
        assert result.context == context
        assert "Found 2 pods" in result.answer
    
    def test_error_handling(self, analyzer, mock_kubectl_tool):
        """Test error handling in analysis."""
        # Make tool fail
        mock_kubectl_tool.execute.side_effect = Exception("Tool error")
        
        result = analyzer.analyze_question(
            "What is the cluster state?"
        )
        
        assert not result.success
        assert "Tool error" in result.error
    
    def test_result_aggregation(self, analyzer):
        """Test result aggregation from multiple analyses."""
        # Run multiple analyses
        results = [
            analyzer.analyze_question("Check pod status"),
            analyzer.analyze_question("Check node status"),
            analyzer.analyze_question("Check service status")
        ]
        
        # Aggregate results
        aggregated = analyzer.aggregate_results(results)
        
        assert aggregated.success
        assert len(aggregated.pressure_points) > 0
        assert all(isinstance(p, PressurePoint) for p in aggregated.pressure_points)
    
    def test_concurrent_analysis(self, analyzer):
        """Test concurrent analysis execution."""
        import concurrent.futures
        
        questions = [
            "Check pod status",
            "Check node status",
            "Check service status"
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(analyzer.analyze_question, q)
                for q in questions
            ]
            
            results = [f.result() for f in futures]
        
        assert all(r.success for r in results)
        assert len(results) == len(questions)
    
    def test_analysis_caching(self, analyzer, mock_kubectl_tool):
        """Test analysis result caching."""
        # First analysis
        result1 = analyzer.analyze_question(
            "What pods are running?",
            use_cache=True
        )
        
        # Second analysis with same question
        result2 = analyzer.analyze_question(
            "What pods are running?",
            use_cache=True
        )
        
        # Tool should only be called once
        assert mock_kubectl_tool.execute.call_count == 1
        assert result1.answer == result2.answer
    
    def test_analysis_with_timeout(self, analyzer):
        """Test analysis with timeout."""
        # Make LLM slow
        class SlowLLM(MockLLM):
            def _generate(self, *args, **kwargs):
                import time
                time.sleep(2)
                return super()._generate(*args, **kwargs)
        
        # Create new analyzer with slow LLM
        agent = ReActAgent(llm_client=SlowLLM())
        slow_analyzer = EnhancedClusterAnalyzer(
            agent=agent,
            tools=analyzer.tools
        )
        
        with pytest.raises(TimeoutError):
            slow_analyzer.analyze_question(
                "What is the cluster state?",
                timeout=1
            )
    
    def test_analysis_with_dry_run(self, analyzer, mock_kubectl_tool):
        """Test analysis in dry-run mode."""
        result = analyzer.analyze_question(
            "Delete problematic pods",
            dry_run=True
        )
        
        assert result.success
        # Verify kubectl was called with dry-run
        for call in mock_kubectl_tool.execute.call_args_list:
            assert call[1].get("dry_run", False)
    
    def test_dangerous_operation_handling(self, analyzer, mock_kubectl_tool):
        """Test handling of dangerous operations."""
        # Make tool require approval
        mock_kubectl_tool.is_dangerous = True
        mock_kubectl_tool.requires_approval = True
        
        # Mock user input
        with patch("builtins.input", return_value="y"):
            result = analyzer.analyze_question(
                "Delete all pods"
            )
        
        assert result.success
        assert "approved by user" in str(result.metadata)
    
    def test_analysis_result_formatting(self, analyzer):
        """Test analysis result formatting."""
        result = analyzer.analyze_question(
            "What is the cluster state?"
        )
        
        # Convert to different formats
        dict_format = result.to_dict()
        assert dict_format["success"]
        assert "answer" in dict_format
        
        str_format = str(result)
        assert "Analysis Result" in str_format
        assert result.answer in str_format
        
        # Test with pressure points
        points = analyzer.analyze_pressure_points()
        formatted = analyzer.format_pressure_points(points)
        assert "Pressure Points" in formatted
        assert "Severity" in formatted 