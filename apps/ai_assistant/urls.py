"""ai-assistant URL routing."""
from django.urls import path
from .views import (
    list_agents, agent_detail, create_agent, update_agent, delete_agent,
    reveal_api_key, get_default_system_prompt, list_available_skills,
    list_conversations, create_conversation, rename_conversation, delete_conversation,
    list_messages, send_message,
    upload_avatar, serve_avatar,
    login, register, refresh_token, logout, me,
    save_message, stream_chat, send_confirm_result, health_check,
    upload_and_parse_file,
    test_agent_connection, list_available_models, health_check_all_agents,
    register_agent_in_agentscope, create_scope_session,
    list_conv_tasks, get_conv_task, list_ai_tasks,
    kb_status, kb_documents, kb_reindex, kb_add_document,
)
from .views.tool_views import (
    list_available_platform_tools,
    list_agent_tools,
    save_mcp,
    test_mcp,
    upload_skill,
    toggle_tool,
    delete_tool,
)

app_name = 'ai'

urlpatterns = [
    # Auth
    path('auth/login', login, name='auth_login'),
    path('auth/register', register, name='auth_register'),
    path('auth/refresh', refresh_token, name='auth_refresh'),
    path('auth/logout', logout, name='auth_logout'),
    path('auth/me', me, name='auth_me'),
    # Agents
    path('agents', list_agents, name='agents_list'),
    path('agents/create', create_agent, name='agent_create'),
    path('agents/<int:agent_id>', agent_detail, name='agent_detail'),
    path('agents/<int:agent_id>/update', update_agent, name='agent_update'),
    path('agents/<int:agent_id>/delete', delete_agent, name='agent_delete'),
    path('agents/<int:agent_id>/reveal-key', reveal_api_key, name='agent_reveal_key'),
    path('agents/<int:agent_id>/conversations', list_conversations, name='conv_list'),
    path('agents/<int:agent_id>/conversations/create', create_conversation, name='conv_create'),
    # Conversations
    path('conversations/<int:conv_id>/messages', list_messages, name='msg_list'),
    path('conversations/<int:conv_id>/send', send_message, name='msg_send'),
    path('conversations/<int:conv_id>/save-message', save_message, name='msg_save'),
    path('conversations/<int:conv_id>/stream', stream_chat, name='msg_stream'),
    path('conversations/<int:conv_id>/confirm-result', send_confirm_result, name='msg_confirm'),
    path('conversations/<int:conv_id>/rename', rename_conversation, name='conv_rename'),
    path('conversations/<int:conv_id>/delete', delete_conversation, name='conv_delete'),
    # Agent connectivity & models
    path('models/detect', list_available_models, name='models_detect'),
    path('agents/<int:agent_id>/test', test_agent_connection, name='agent_test'),
    path('agents/<int:agent_id>/models', list_available_models, name='agent_models'),
    path('agents/<int:agent_id>/register-scope', register_agent_in_agentscope, name='agent_register_scope'),
    path('agents/health', health_check_all_agents, name='agent_health'),
    # Default prompt template & available platform tools
    path('default-system-prompt', get_default_system_prompt, name='default_system_prompt'),
    path('available-tools', list_available_platform_tools, name='available_tools'),
    path('available-skills', list_available_skills, name='available_skills'),
    # MCP & Skill management (per-agent)
    path('agents/<int:agent_id>/tools', list_agent_tools, name='agent_tools_list'),
    path('agents/<int:agent_id>/tools/mcp/save', save_mcp, name='agent_mcp_save'),
    path('agents/<int:agent_id>/tools/mcp/test', test_mcp, name='agent_mcp_test'),
    path('agents/<int:agent_id>/tools/skill/upload', upload_skill, name='agent_skill_upload'),
    path('agents/<int:agent_id>/tools/<int:tool_id>/toggle', toggle_tool, name='agent_tool_toggle'),
    path('agents/<int:agent_id>/tools/<int:tool_id>/delete', delete_tool, name='agent_tool_delete'),
    # AgentScope SSE session management
    path('conversations/<int:conv_id>/create-scope-session', create_scope_session, name='conv_scope_session'),
    # Conversation-level task history
    path('conversations/<int:conv_id>/tasks', list_conv_tasks, name='conv_tasks'),
    path('conversations/<int:conv_id>/tasks/<str:run_id>', get_conv_task, name='conv_task_detail'),
    # Health check
    path('health', health_check, name='health_check'),
    # Workbench task board
    path('tasks', list_ai_tasks, name='ai_tasks_list'),
    # Uploads
    path('upload-avatar', upload_avatar, name='upload_avatar'),
    path('upload-file', upload_and_parse_file, name='upload_file'),
    path('avatars/<str:filename>', serve_avatar, name='serve_avatar'),
    # Knowledge base
    path('knowledge/status', kb_status, name='kb_status'),
    path('knowledge/documents', kb_documents, name='kb_documents'),
    path('knowledge/reindex', kb_reindex, name='kb_reindex'),
    path('knowledge/documents/add', kb_add_document, name='kb_add_doc'),
]
