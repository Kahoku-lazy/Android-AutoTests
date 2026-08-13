"""ai-assistant URL routing."""

from django.urls import path

from .views import (
    agent_detail,
    chat_stream,
    create_agent,
    create_conversation,
    create_shared_tool,
    delete_agent,
    delete_conversation,
    delete_shared_tool,
    get_conv_task,
    health_check_all_agents,
    import_from_toolbox,
    kb_add_document,
    kb_documents,
    kb_reindex,
    kb_status,
    list_agents,
    list_ai_tasks,
    list_available_models,
    list_available_skills,
    list_conv_tasks,
    list_conversations,
    list_messages,
    list_shared_tools,
    rename_conversation,
    reveal_api_key,
    save_message,
    send_confirm_result,
    test_agent_connection,
    update_agent,
    update_shared_tool,
    upload_and_parse_file,
    upload_avatar,
    upload_shared_skill,
)
from .views.tool_gateway import agent_config, tool_gateway, tool_schemas
from .views.tool_views import (
    delete_tool,
    list_agent_tools,
    list_available_platform_tools,
    save_mcp,
    test_mcp,
    toggle_tool,
    upload_skill,
)

app_name = "ai"

urlpatterns = [
    # Agents
    path("agents", list_agents, name="agents_list"),
    path("agents/create", create_agent, name="agent_create"),
    path("agents/<int:agent_id>", agent_detail, name="agent_detail"),
    path("agents/<int:agent_id>/update", update_agent, name="agent_update"),
    path("agents/<int:agent_id>/delete", delete_agent, name="agent_delete"),
    path("agents/<int:agent_id>/reveal-key", reveal_api_key, name="agent_reveal_key"),
    path("agents/<int:agent_id>/conversations", list_conversations, name="conv_list"),
    path("agents/<int:agent_id>/conversations/create", create_conversation, name="conv_create"),
    # Conversations
    path("conversations/<int:conv_id>/messages", list_messages, name="msg_list"),
    path("conversations/<int:conv_id>/save-message", save_message, name="msg_save"),
    path("conversations/<int:conv_id>/confirm-result", send_confirm_result, name="msg_confirm"),
    path("conversations/<int:conv_id>/rename", rename_conversation, name="conv_rename"),
    path("conversations/<int:conv_id>/delete", delete_conversation, name="conv_delete"),
    # Agent connectivity & models
    path("models/detect", list_available_models, name="models_detect"),
    path("agents/<int:agent_id>/test", test_agent_connection, name="agent_test"),
    path("agents/<int:agent_id>/models", list_available_models, name="agent_models"),
    path("agents/health", health_check_all_agents, name="agent_health"),
    # Available platform tools
    path("available-tools", list_available_platform_tools, name="available_tools"),
    path("available-skills", list_available_skills, name="available_skills"),
    # MCP & Skill management (per-agent)
    path("agents/<int:agent_id>/tools", list_agent_tools, name="agent_tools_list"),
    path("agents/<int:agent_id>/tools/mcp/save", save_mcp, name="agent_mcp_save"),
    path("agents/<int:agent_id>/tools/mcp/test", test_mcp, name="agent_mcp_test"),
    path("agents/<int:agent_id>/tools/skill/upload", upload_skill, name="agent_skill_upload"),
    path("agents/<int:agent_id>/tools/<int:tool_id>/toggle", toggle_tool, name="agent_tool_toggle"),
    path("agents/<int:agent_id>/tools/<int:tool_id>/delete", delete_tool, name="agent_tool_delete"),
    # SSE streaming chat — Agent runs in-process (no AgentScope service needed)
    path(
        "conversations/<int:conv_id>/chat/stream",
        chat_stream,
        name="conv_chat_stream",
    ),
    # Conversation-level task history
    path("conversations/<int:conv_id>/tasks", list_conv_tasks, name="conv_tasks"),
    path("conversations/<int:conv_id>/tasks/<str:run_id>", get_conv_task, name="conv_task_detail"),
    # Workbench task board
    path("tasks", list_ai_tasks, name="ai_tasks_list"),
    # Uploads
    path("upload-avatar", upload_avatar, name="upload_avatar"),
    path("upload-file", upload_and_parse_file, name="upload_file"),
    # Knowledge base
    path("knowledge/status", kb_status, name="kb_status"),
    path("knowledge/documents", kb_documents, name="kb_documents"),
    path("knowledge/reindex", kb_reindex, name="kb_reindex"),
    path("knowledge/documents/add", kb_add_document, name="kb_add_doc"),
    # Tool gateway — AgentScope calls Django via these endpoints
    path("tools/schemas", tool_schemas, name="tool_schemas"),
    path("tools/agent-config/<str:agent_id>", agent_config, name="tool_agent_config"),
    path("tools/<str:module>/<str:action>", tool_gateway, name="tool_gateway"),
    # AI Toolbox — shared skills / tools / extensions
    path("toolbox", list_shared_tools, name="toolbox_list"),
    path("toolbox/create", create_shared_tool, name="toolbox_create"),
    path("toolbox/<int:item_id>/update", update_shared_tool, name="toolbox_update"),
    path("toolbox/<int:item_id>/delete", delete_shared_tool, name="toolbox_delete"),
    path("toolbox/upload-skill", upload_shared_skill, name="toolbox_upload_skill"),
    path(
        "agents/<int:agent_id>/tools/import-from-toolbox",
        import_from_toolbox,
        name="agent_import_toolbox",
    ),
]
