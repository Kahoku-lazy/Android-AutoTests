"""Agent factory — thin loader for default system prompt.

The business domain knowledge (140-line Chinese prompt template) is owned by
Django at apps.ai_assistant.agent_scope.system_prompt. This module is a thin
bridge for backward compatibility — any code that imports DEFAULT_SYSTEM_PROMPT_TEMPLATE
from here still works, while the actual content lives in Django.
"""

from apps.ai_assistant.agent_scope.system_prompt import get_default_system_prompt

DEFAULT_SYSTEM_PROMPT_TEMPLATE = get_default_system_prompt()
