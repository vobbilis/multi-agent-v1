# Multi-Agent Root Cause Analysis System Documentation

This directory contains comprehensive documentation for the Multi-Agent Root Cause Analysis System, designed to automatically identify and analyze the root causes of failures and performance issues in Kubernetes environments.

## Documentation Overview

The documentation is organized into the following sections:

### Architecture
- [System Overview](architecture/system_overview.md): High-level architecture and component interactions

### Component Documentation
- [Components Overview](components/README.md): Introduction to all system components
- [Analysis Engine](components/analysis_engine.md): Root cause determination
- [Simulation Engine](components/simulation_engine.md): Failure scenario simulation
- Specialist Agents:
  - [Events Agent](components/specialist_agents/events_agent.md): Event processing and analysis
  - [Logs Agent](components/specialist_agents/logs_agent.md): Log analysis and correlation

### API Documentation
- [API Reference](api/api_reference.md): Complete API endpoints and usage

### Deployment
- [Deployment Guide](deployment/deployment_guide.md): Installation and setup
- [Security](deployment/security.md): Security considerations and best practices

### Scenarios
- [Scenarios Overview](scenarios/README.md): Introduction to test scenarios
- [Resource Issues](scenarios/resource_issues.md): Memory, CPU, and quota problems
- [Cascade Failures](scenarios/cascade_failures.md): Complex multi-component failures

### Diagrams
The [diagrams](diagrams/) directory contains architectural and workflow diagrams:
- [System Architecture](diagrams/system_architecture.txt): Overall system design
- [Component Communication](diagrams/component_communication.txt): Inter-component messaging
- [Data Flow](diagrams/data_flow.txt): Information flow through components
- [Security Architecture](diagrams/security_architecture.txt): Security controls and boundaries
- [Message Flow](diagrams/message_flow.md): Detailed message flow between components

## Using This Documentation

### For Operators
Start with the [Deployment Guide](deployment/deployment_guide.md) for installation instructions, then refer to the [Security](deployment/security.md) documentation for security best practices.

### For Developers
Begin with the [System Overview](architecture/system_overview.md) to understand the architecture and component interactions.

### For Users
The [API Reference](api/api_reference.md) provides comprehensive details on interacting with the system programmatically, while [Scenarios](scenarios/README.md) documentation explains common use cases.

## Documentation Conventions

- Markdown is used for all documentation files
- Code examples are provided in appropriate syntax highlighting
- Configuration examples use YAML format
- Diagrams are provided as text (ASCII art) for version control compatibility
- Each document follows a consistent structure:
  - Introduction/Purpose
  - Detailed Sections
  - Examples (where applicable)
  - References to Related Documentation

## Contributing to Documentation

Documentation improvements are welcome. Please follow these guidelines:
1. Maintain the existing structure and naming conventions
2. Use clear, concise language
3. Include practical examples where applicable
4. Update cross-references when adding new documents
5. Verify all links work correctly

## Documentation TODOs

- [ ] Complete missing component documentation
- [ ] Add documentation for operations and development
- [ ] Add more scenario examples
- [ ] Include troubleshooting guides
- [ ] Add user journey documentation 