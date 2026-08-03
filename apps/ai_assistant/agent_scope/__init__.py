"""AgentScope integration layer — Tool gateway, RAG, provider registry, prompts.

This package is the single boundary between Django and AgentScope.
AgentScope communicates with Django ONLY through the /api/tools/ gateway.
Django owns all business data and logic.
"""
