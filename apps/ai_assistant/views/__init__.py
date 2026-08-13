"""ai-assistant views package — re-exports all endpoint handlers for urls.py."""

from .agent_views import (
    agent_detail,
    create_agent,
    delete_agent,
    health_check_all_agents,
    list_agents,
    list_available_skills,
    reveal_api_key,
    update_agent,
)
from .chat_views import chat_stream
from .conversation_views import (
    create_conversation,
    delete_conversation,
    get_conv_task,
    list_ai_tasks,
    list_conv_tasks,
    list_conversations,
    list_messages,
    rename_conversation,
    save_message,
)
from .file_views import upload_and_parse_file, upload_avatar
from .hitl_views import send_confirm_result
from .knowledge_views import kb_add_document, kb_documents, kb_reindex, kb_status
from .model_views import list_available_models, test_agent_connection
from .tool_views import (
    delete_tool,
    list_agent_tools,
    list_available_platform_tools,
    save_mcp,
    test_mcp,
    toggle_tool,
    upload_skill,
)
from .toolbox_views import (
    create_shared_tool,
    delete_shared_tool,
    import_from_toolbox,
    list_shared_tools,
    update_shared_tool,
    upload_shared_skill,
)

__all__ = [
    "list_agents",
    "agent_detail",
    "create_agent",
    "update_agent",
    "delete_agent",
    "reveal_api_key",
    "list_available_skills",
    "health_check_all_agents",
    "list_conversations",
    "create_conversation",
    "delete_conversation",
    "rename_conversation",
    "list_messages",
    "save_message",
    "chat_stream",
    "list_conv_tasks",
    "get_conv_task",
    "list_ai_tasks",
    "upload_avatar",
    "upload_and_parse_file",
    "test_agent_connection",
    "list_available_models",
    "send_confirm_result",
    "kb_status",
    "kb_documents",
    "kb_reindex",
    "kb_add_document",
    "list_available_platform_tools",
    "list_agent_tools",
    "save_mcp",
    "test_mcp",
    "upload_skill",
    "toggle_tool",
    "delete_tool",
    "list_shared_tools",
    "create_shared_tool",
    "update_shared_tool",
    "delete_shared_tool",
    "upload_shared_skill",
    "import_from_toolbox",
]
