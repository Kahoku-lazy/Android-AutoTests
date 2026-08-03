"""tests/api/ 共享 fixtures — Django TestClient + 鉴权/资源 fixtures。

提供：
- Django TestClient（无需启动 :8765 服务）
- Agent/Conversation fixtures（权限隔离测试用）
"""

import json

import pytest
from django.test import Client
from django.contrib.auth.models import User

from apps.ai_assistant.models import AIAgent, AIConversation
from apps.ai_assistant.api import encrypt_key


# ═══════════════════════════════════════
# Django TestClient
# ═══════════════════════════════════════

@pytest.fixture
def client():
    """Django TestClient — 走完整中间件链，无需启动服务。"""
    return Client()


# ═══════════════════════════════════════
# 测试用户
# ═══════════════════════════════════════

@pytest.fixture
def user1(db):
    """测试用户 alice。"""
    return User.objects.create_user(username="alice", password="pass1")


@pytest.fixture
def user2(db):
    """测试用户 bob（权限隔离用）。"""
    return User.objects.create_user(username="bob", password="pass2")


# ═══════════════════════════════════════
# AI Agent
# ═══════════════════════════════════════

@pytest.fixture
def agent1(db, user1):
    """属于 user1 的 Agent。"""
    return AIAgent.objects.create(
        owner=user1,
        name="Alice's Agent",
        model_provider="dashscope",
        model_name="qwen-max",
        api_key=encrypt_key("sk-test-alice-key-123"),
        system_prompt="You are a helpful assistant.",
    )


@pytest.fixture
def agent2(db, user2):
    """属于 user2 的 Agent。"""
    return AIAgent.objects.create(
        owner=user2,
        name="Bob's Agent",
        model_provider="openai",
        model_name="gpt-4",
        api_key=encrypt_key("sk-test-bob-key-456"),
    )


# ═══════════════════════════════════════
# 对话
# ═══════════════════════════════════════

@pytest.fixture
def conversation1(db, agent1, user1):
    """属于 user1 的对话。"""
    return AIConversation.objects.create(
        owner=user1,
        agent=agent1,
        title="Alice 的测试对话",
    )


@pytest.fixture
def conversation2(db, agent2, user2):
    """属于 user2 的对话。"""
    return AIConversation.objects.create(
        owner=user2,
        agent=agent2,
        title="Bob 的对话",
    )


# ═══════════════════════════════════════
# Helpers
# ═══════════════════════════════════════

def _jwt_header(user):
    """构造 JWT Authorization header。"""
    from shared.auth.jwt_auth import create_access_token
    token = create_access_token(str(user.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _json(response):
    """解析 response content 为 JSON。"""
    return json.loads(response.content.decode())
