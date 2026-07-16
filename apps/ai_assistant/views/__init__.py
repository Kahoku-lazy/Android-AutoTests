"""ai-assistant views package — re-exports all endpoint handlers for urls.py."""
from .auth_views import login, register, refresh_token, logout, me
from .agent_views import (
    list_agents,
    agent_detail,
    create_agent,
    update_agent,
    delete_agent,
    reveal_api_key,
    health_check_all_agents,
    register_agent_in_agentscope,
)
from .conversation_views import (
    list_conversations,
    create_conversation,
    delete_conversation,
    rename_conversation,
    list_messages,
    send_message,
    save_message,
    stream_chat,
    list_conv_tasks,
    get_conv_task,
)
from .file_views import upload_avatar, serve_avatar, upload_and_parse_file
from .model_views import test_agent_connection, list_available_models
from .hitl_views import send_confirm_result, create_scope_session

__all__ = [
    'login', 'register', 'refresh_token', 'logout', 'me',
    'list_agents', 'agent_detail', 'create_agent', 'update_agent', 'delete_agent',
    'reveal_api_key', 'health_check_all_agents', 'register_agent_in_agentscope',
    'list_conversations', 'create_conversation', 'delete_conversation', 'rename_conversation',
    'list_messages', 'send_message', 'save_message', 'stream_chat',
    'list_conv_tasks', 'get_conv_task',
    'upload_avatar', 'serve_avatar', 'upload_and_parse_file',
    'test_agent_connection', 'list_available_models',
    'send_confirm_result', 'create_scope_session',
]
