#!/bin/bash
# Simple test runner script
# Run from the project root directory

# Set PYTHONPATH to include the project root
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run unit tests
pytest tests/unit -v

# Run specialist agent tests
pytest tests/specialist_agents -v

# Run integration tests
pytest tests/integration_tests -v

# Run workflow tests
pytest tests/workflow_tests -v 