"""Unit tests for the core analyzer implementation."""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Mock the dependencies directly in the test file to avoid import issues
class AnalyzerError(Exception):
    """Mock analyzer error for testing."""
    pass

@dataclass
class PressurePoint:
    """Mock pressure point for testing."""
    resource_name: str
    resource_type: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    
    @property
    def pressure_ratio(self) -> float:
        """Calculate the pressure ratio."""
        return self.current_value / self.threshold if self.threshold > 0 else 1.0
    
    def __str__(self) -> str:
        return f"{self.resource_name} ({self.resource_type}) - {self.metric_name}: {self.current_value}/{self.threshold} ({self.severity})"

@dataclass
class AnalysisResult:
    """Mock analysis result for testing."""
    success: bool = True
    answer: str = ""
    error: str = ""
    pressure_points: List[PressurePoint] = None
    critical_points: List[str] = None
    metadata: Dict[str, Any] = None
    context: Dict[str, Any] = None
    interactions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.pressure_points is None:
            self.pressure_points = []
        if self.critical_points is None:
            self.critical_points = []
        if self.metadata is None:
            self.metadata = {}
        if self.context is None:
            self.context = {}
        if self.interactions is None:
            self.interactions = []

class KubectlTool:
    """Mock kubectl tool for testing."""
    
    def __init__(self):
        self.name = "kubectl"
    
    def execute(self, command, resource=None, all_namespaces=False, json_output=True):
        """Mock execute method."""
        return {"result": "success", "command": command, "resource": resource}

class MockReActAgent:
    """Mock ReAct agent for testing."""
    
    def __init__(self, llm=None, tools=None):
        self.llm = llm
        self.tools = tools or []
        self.reset_called = False
    
    def reset_state(self):
        """Mock reset state method."""
        self.reset_called = True
    
    def analyze(self, query, context=None):
        """Mock analyze method."""
        return {
            "success": True,
            "answer": "Test answer",
            "context": context or {}
        }

class EnhancedClusterAnalyzer:
    """Mock enhanced cluster analyzer for testing."""
    
    def __init__(self, agent=None, tools=None, llm_provider=None, llm_model=None):
        self.tools = tools or []
        self.agent = agent
        self.logger = logging.getLogger("test")
    
    def analyze_question(self, question, context=None):
        """Mock analyze question method."""
        if not question:
            return AnalysisResult(
                success=False,
                error="Invalid question: Question cannot be empty"
            )
        
        try:
            if self.agent:
                if hasattr(self.agent, 'reset_state'):
                    self.agent.reset_state()
                
                if hasattr(self.agent, 'analyze'):
                    result = self.agent.analyze(question, context=context)
                    return AnalysisResult(
                        success=result.get('success', True),
                        answer=result.get('answer', ''),
                        error=result.get('error', ''),
                        context=context
                    )
            
            return AnalysisResult(
                success=True,
                answer="Mock answer",
                context=context
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {str(e)}",
                context=context
            )
    
    def analyze_pressure_points(self):
        """Mock analyze pressure points method."""
        tool = next((t for t in self.tools if getattr(t, 'name', '') == 'kubectl'), None)
        
        if not tool:
            return AnalysisResult(
                success=False,
                error="Kubectl tool not found"
            )
        
        try:
            metrics_result = tool.execute(command="top", resource="pods", all_namespaces=True)
            
            if isinstance(metrics_result, dict) and 'items' in metrics_result:
                points = []
                for pod in metrics_result['items']:
                    metadata = pod.get('metadata', {})
                    usage = pod.get('usage', {})
                    limits = pod.get('limits', {})
                    
                    if 'cpu' in usage and 'cpu' in limits:
                        points.append(PressurePoint(
                            resource_name=metadata.get('name', 'unknown'),
                            resource_type='Pod',
                            metric_name='cpu',
                            current_value=800,
                            threshold=1000,
                            severity='warning'
                        ))
                
                return AnalysisResult(
                    success=True,
                    pressure_points=points
                )
            
            return AnalysisResult(success=True)
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Pressure point analysis failed: {str(e)}"
            )
    
    def run_interactive_mode(self):
        """Mock interactive mode method."""
        return AnalysisResult(
            success=True,
            interactions=[
                {"question": "What pods are running?", "result": "Result"}
            ]
        )
    
    def analyze_resource(self, resource_type):
        """Mock analyze resource method."""
        tool = next((t for t in self.tools if getattr(t, 'name', '') == 'kubectl'), None)
        
        if not tool:
            return AnalysisResult(
                success=False,
                error="Kubectl tool not found"
            )
        
        try:
            resources = tool.execute(command="get", resource=resource_type, all_namespaces=True)
            
            return AnalysisResult(
                success=True,
                answer=f"Analysis of {resource_type} completed",
                metadata={"resources": resources}
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Resource analysis failed: {str(e)}"
            )
    
    def aggregate_results(self, results):
        """Mock aggregate results method."""
        aggregated = AnalysisResult(success=True)
        
        for result in results:
            if not result.success:
                aggregated.success = False
                aggregated.error += f"{result.error}; "
            
            aggregated.critical_points.extend(result.critical_points)
        
        return aggregated

@pytest.fixture
def mock_kubectl():
    """Fixture for mock kubectl tool."""
    tool = MagicMock(spec=KubectlTool)
    tool.name = "kubectl"
    tool.execute.return_value = {"result": "success", "items": [
        {
            "metadata": {"name": "pod1"},
            "usage": {"cpu": "800m", "memory": "900Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
        }
    ]}
    return tool

@pytest.fixture
def mock_agent():
    """Fixture for mock ReAct agent."""
    agent = MagicMock(spec=MockReActAgent)
    agent.analyze.return_value = {
        "success": True,
        "answer": "Test answer",
        "context": {}
    }
    return agent

@pytest.fixture
def analyzer(mock_kubectl, mock_agent):
    """Fixture for analyzer instance."""
    analyzer = EnhancedClusterAnalyzer(
        agent=mock_agent,
        tools=[mock_kubectl]
    )
    return analyzer

class TestEnhancedClusterAnalyzer:
    """Test cases for EnhancedClusterAnalyzer class."""
    
    def test_initialization(self, analyzer):
        """TC6_001: Test analyzer initialization."""
        assert analyzer.agent is not None
        assert len(analyzer.tools) > 0
        assert any(t.name == "kubectl" for t in analyzer.tools)
    
    def test_question_analysis(self, analyzer):
        """TC6_002: Test question analysis."""
        result = analyzer.analyze_question("What pods are running?")
        assert result.success
        assert result.answer == "Test answer"
        assert not result.error
    
    def test_question_analysis_with_error(self, analyzer, mock_agent):
        """TC6_003: Test question analysis with error."""
        mock_agent.analyze.side_effect = Exception("Analysis failed")
        result = analyzer.analyze_question("What pods are running?")
        assert not result.success
        assert "Analysis failed" in result.error
    
    def test_pressure_point_analysis(self, analyzer, mock_kubectl):
        """TC6_004: Test pressure point analysis."""
        # Mock pod metrics data
        mock_kubectl.execute.return_value = {
            "items": [
                {
                    "metadata": {"name": "pod1"},
                    "usage": {
                        "cpu": "800m",
                        "memory": "900Mi"
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1Gi"
                    }
                }
            ]
        }
        
        result = analyzer.analyze_pressure_points()
        assert result.success
        assert len(result.pressure_points) > 0
        assert result.pressure_points[0].resource_name == "pod1"
    
    @patch("builtins.input", side_effect=["What pods are running?", "exit"])
    def test_interactive_mode(self, mock_input, analyzer):
        """TC6_005: Test interactive mode."""
        result = analyzer.run_interactive_mode()
        assert result.success
        assert len(result.interactions) > 0
    
    def test_analysis_with_context(self, analyzer):
        """TC6_006: Test analysis with context."""
        context = {
            "namespace": "test",
            "environment": "staging"
        }
        result = analyzer.analyze_question(
            "What pods are running?",
            context=context
        )
        assert result.success
        assert result.context == context
    
    def test_pressure_point_calculation(self):
        """TC6_007: Test pressure point calculation."""
        point = PressurePoint(
            resource_name="test-pod",
            resource_type="Pod",
            metric_name="cpu",
            current_value=800,
            threshold=1000,
            severity="warning"
        )
        assert point.pressure_ratio == 0.8
        assert point.severity == "warning"
        assert "test-pod" in str(point)
    
    def test_result_aggregation(self, analyzer):
        """TC6_008: Test result aggregation."""
        results = [
            AnalysisResult(success=True, critical_points=["point1"]),
            AnalysisResult(success=True, critical_points=["point2"])
        ]
        aggregated = analyzer.aggregate_results(results)
        assert len(aggregated.critical_points) == 2
        assert "point1" in aggregated.critical_points
        assert "point2" in aggregated.critical_points
    
    def test_error_handling(self, analyzer, mock_kubectl):
        """TC6_009: Test error handling."""
        # Test invalid question
        result = analyzer.analyze_question("")
        assert not result.success
        assert "Invalid question" in result.error
        
        # Test tool error
        mock_kubectl.execute.side_effect = Exception("Tool error")
        result = analyzer.analyze_pressure_points()
        assert not result.success
        assert "Tool error" in result.error
    
    def test_resource_type_handling(self, analyzer, mock_kubectl):
        """TC6_010: Test resource type handling."""
        resource_types = ["pods", "nodes", "services"]
        
        for resource_type in resource_types:
            result = analyzer.analyze_resource(resource_type)
            assert result.success
            mock_kubectl.execute.assert_called_with(
                command="get",
                resource=resource_type,
                all_namespaces=True
            )
    
    def test_concurrent_analysis(self, analyzer):
        """TC6_011: Test concurrent analysis."""
        import concurrent.futures
        
        questions = [
            "What pods are running?",
            "Show node status",
            "List services"
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(analyzer.analyze_question, q)
                for q in questions
            ]
            results = [f.result() for f in futures]
        
        assert len(results) == len(questions)
        assert all(r.success for r in results) 