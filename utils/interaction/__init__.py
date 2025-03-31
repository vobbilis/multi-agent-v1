"""
Agent interaction tracking utilities
"""
from utils.interaction.tracer import AgentInteractionTracer

# Create a global instance of the tracer for convenience
tracer = AgentInteractionTracer()

__all__ = ['AgentInteractionTracer', 'tracer'] 