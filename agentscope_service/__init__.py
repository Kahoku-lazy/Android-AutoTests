"""AgentScope 2.0 Agent Service — pure AI engine.

This package contains ONLY AI engine concerns:
  - FastAPI app creation and lifecycle
  - PlatformTool abstraction (HTTP-based tool calls to Django)
  - Workspace and skill management
  - Sub-agent team templates
  - JWT authentication

AgentScope NEVER imports Django modules or connects to MySQL.
All business data access goes through HTTP calls to Django's /api/tools/ gateway.
"""
