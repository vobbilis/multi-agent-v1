"""Tool execution result."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json

class ToolResultEncoder(json.JSONEncoder):
    """JSON encoder for ToolResult objects."""
    def default(self, obj):
        if isinstance(obj, ToolResult):
            return obj.to_dict()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: Optional[Union[str, datetime]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure timestamp is present
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result_dict = {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }
        
        # Convert timestamp to string if it's a datetime
        if isinstance(self.timestamp, datetime):
            result_dict["timestamp"] = self.timestamp.isoformat()
        else:
            result_dict["timestamp"] = self.timestamp
            
        return result_dict
    
    def __str__(self) -> str:
        """String representation of the result."""
        if self.success:
            return f"Success: {self.data}"
        else:
            return f"Error: {self.error}" 