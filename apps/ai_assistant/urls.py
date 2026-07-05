"""ai-assistant URL routing."""
from django.urls import path
from .views import (
    list_agents, agent_detail, create_agent, update_agent, delete_agent,
    reveal_api_key,
    list_conversations, create_conversation, rename_conversation, delete_conversation,
    list_messages, send_message,
    upload_avatar, serve_avatar,
    login, register, refresh_token, logout, me,
    save_message, stream_chat, send_confirm_result,
    upload_and_parse_file,
    test_agent_connection, list_available_models, health_check_all_agents,
    register_agent_in_agentscope, create_scope_session,
    list_conv_tasks, get_conv_task,
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
    # AgentScope SSE session management
    path('conversations/<int:conv_id>/create-scope-session', create_scope_session, name='conv_scope_session'),
    # Conversation-level task history
    path('conversations/<int:conv_id>/tasks', list_conv_tasks, name='conv_tasks'),
    path('conversations/<int:conv_id>/tasks/<str:run_id>', get_conv_task, name='conv_task_detail'),
    # Uploads
    path('upload-avatar', upload_avatar, name='upload_avatar'),
    path('upload-file', upload_and_parse_file, name='upload_file'),
    path('avatars/<str:filename>', serve_avatar, name='serve_avatar'),
]
