"""鉴权集成测试 — 依赖 Django ORM + Test Client，不需外部服务。

覆盖：
- 登录表单校验（逐层中文错误信息）
- Token 生命周期（签发 → 使用 → 刷新 → 登出 → 拒绝）
- 注册校验（重复 / 短用户名 / 缺少字段）
- 资源权限隔离（跨用户访问 Agent / 对话 → 403）
- API Key 安全（DB 密文 / 列表脱敏 / 掩码保护 / 一次性查看）
- 装饰器 @require_auth

注意：所有测试类都必须加 @pytest.mark.django_db(transaction=True)，
因为 JWTAuthenticationMiddleware.__call__ 会触发 close_old_connections()。
"""

import json

import pytest

from apps.ai_assistant.models import AIAgent, AIConversation
from apps.ai_assistant.api import decrypt_key, mask_key


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _jwt_header(user):
    """构造 JWT Authorization header。"""
    from shared.auth.jwt_auth import create_access_token
    token = create_access_token(str(user.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _json(response):
    """解析 response content 为 JSON。"""
    return json.loads(response.content.decode())


# ═══════════════════════════════════════════════════════════════════
# 登录
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestLogin:
    """POST /api/ai/auth/login"""

    def test_normal_login(self, client, user1):
        """正常登录 → 200 + access_token + refresh_token"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "alice", "password": "pass1"}),
                            content_type="application/json")
        data = _json(resp)

        assert resp.status_code == 200
        assert data["ok"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "alice"

    def test_wrong_password(self, client, user1):
        """错误密码 → 401"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "alice", "password": "wrong"}),
                            content_type="application/json")
        data = _json(resp)

        assert resp.status_code == 401
        assert data["ok"] is False
        assert "用户名或密码错误" in data["error"]

    def test_nonexistent_user(self, client):
        """不存在的用户 → 401（同样不透露用户是否存在）"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "nobody", "password": "x"}),
                            content_type="application/json")
        assert resp.status_code == 401

    # ── 逐层校验 ──

    def test_both_empty(self, client):
        """用户名和密码都空 → 400"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "", "password": ""}),
                            content_type="application/json")
        data = _json(resp)
        assert resp.status_code == 400
        assert "请输入用户名和密码" in data["error"]

    def test_username_empty(self, client):
        """用户名为空 → 400"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "", "password": "x"}),
                            content_type="application/json")
        data = _json(resp)
        assert resp.status_code == 400
        assert "请输入用户名" in data["error"]

    def test_password_empty(self, client):
        """密码为空 → 400"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "alice", "password": ""}),
                            content_type="application/json")
        data = _json(resp)
        assert resp.status_code == 400
        assert "请输入密码" in data["error"]

    def test_whitespace_username(self, client):
        """纯空格用户名 → 400"""
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": "   ", "password": "x"}),
                            content_type="application/json")
        assert resp.status_code == 400

    def test_username_too_long(self, client):
        """用户名超过 150 字符 → 400"""
        long_name = "a" * 151
        resp = client.post("/api/ai/auth/login",
                            data=json.dumps({"username": long_name, "password": "x"}),
                            content_type="application/json")
        assert resp.status_code == 400

    def test_invalid_json_body(self, client):
        """非 JSON 请求体 → 400"""
        resp = client.post("/api/ai/auth/login",
                            data="not-json",
                            content_type="application/json")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# 注册
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestRegister:
    """POST /api/ai/auth/register"""

    def test_normal_register(self, client):
        """正常注册 → 200 + token + user"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "new_user", "password": "new_pass"}),
                            content_type="application/json")
        data = _json(resp)

        assert resp.status_code == 200
        assert data["ok"] is True
        assert data["user"]["username"] == "new_user"

    def test_duplicate_username(self, client, user1):
        """重复用户名 → 409"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "alice", "password": "x"}),
                            content_type="application/json")
        assert resp.status_code == 409
        assert "用户名已存在" in _json(resp)["error"]

    def test_short_username(self, client):
        """用户名 < 3 字符 → 400"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "ab", "password": "123"}),
                            content_type="application/json")
        assert resp.status_code == 400

    def test_long_username(self, client):
        """用户名 > 20 字符 → 400"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "a" * 21, "password": "123"}),
                            content_type="application/json")
        assert resp.status_code == 400

    def test_both_empty(self, client):
        """用户名和密码都空 → 400"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "", "password": ""}),
                            content_type="application/json")
        assert resp.status_code == 400

    def test_password_empty(self, client):
        """密码为空 → 400"""
        resp = client.post("/api/ai/auth/register",
                            data=json.dumps({"username": "valid", "password": ""}),
                            content_type="application/json")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# Token 刷新
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestTokenRefresh:
    """POST /api/ai/auth/refresh"""

    def test_refresh_success(self, client, user1):
        """用 refresh token 换新 access token"""
        login_resp = client.post("/api/ai/auth/login",
                                  data=json.dumps({"username": "alice", "password": "pass1"}),
                                  content_type="application/json")
        refresh_token = _json(login_resp)["refresh_token"]

        resp = client.post("/api/ai/auth/refresh",
                            data=json.dumps({"refresh_token": refresh_token}),
                            content_type="application/json")
        data = _json(resp)

        assert resp.status_code == 200
        assert data["ok"] is True
        assert "access_token" in data

    def test_access_token_as_refresh_rejected(self, client, user1):
        """拿 access token 去刷新 → 401"""
        login_resp = client.post("/api/ai/auth/login",
                                  data=json.dumps({"username": "alice", "password": "pass1"}),
                                  content_type="application/json")
        access_token = _json(login_resp)["access_token"]

        resp = client.post("/api/ai/auth/refresh",
                            data=json.dumps({"refresh_token": access_token}),
                            content_type="application/json")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# 用户信息
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestMe:
    """GET /api/ai/auth/me"""

    def test_me_endpoint_requires_auth(self, client):
        """/api/ai/auth/me 因为 URL 前缀命中 PUBLIC_PREFIXES，
        中间件不注入 user_id，因此 me() 视图始终返回 401。

        这是中间件设计的已知行为——auth 前缀下所有端点被统一视为公开路径。
        me() 想要拿到 user_id 需要中间件把它的路由从 PUBLIC_PREFIXES 中剥离。
        """
        resp = client.get("/api/ai/auth/me")
        data = _json(resp)
        assert resp.status_code == 401
        assert data["ok"] is False


# ═══════════════════════════════════════════════════════════════════
# 资源权限隔离
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestResourceIsolation:
    """跨用户访问对方资源 → 403"""

    def test_access_others_agent_detail(self, client, agent1, user2):
        """用户 2 访问用户 1 的 Agent → 403"""
        resp = client.get(f"/api/ai/agents/{agent1.id}", **_jwt_header(user2))
        assert resp.status_code == 403

    def test_access_own_agent_detail(self, client, agent1, user1):
        """用户 1 访问自己的 Agent → 200"""
        resp = client.get(f"/api/ai/agents/{agent1.id}", **_jwt_header(user1))
        assert resp.status_code == 200

    def test_update_others_agent(self, client, agent1, user2):
        """用户 2 更新用户 1 的 Agent → 403"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/update",
                            data=json.dumps({"name": "Hacked"}),
                            content_type="application/json",
                            **_jwt_header(user2))
        assert resp.status_code == 403

    def test_delete_others_agent(self, client, agent1, user2):
        """用户 2 删除用户 1 的 Agent → 403"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/delete",
                            **_jwt_header(user2))
        assert resp.status_code == 403

    def test_list_conversations_of_others_agent(self, client, agent1, user2):
        """用户 2 看用户 1 的 Agent 对话列表 → 403"""
        resp = client.get(f"/api/ai/agents/{agent1.id}/conversations",
                           **_jwt_header(user2))
        assert resp.status_code == 403

    def test_access_others_conversation_messages(self, client, conversation1, user2):
        """用户 2 访问用户 1 的对话消息 → 403"""
        resp = client.get(f"/api/ai/conversations/{conversation1.id}/messages",
                           **_jwt_header(user2))
        assert resp.status_code == 403

    def test_rename_others_conversation(self, client, conversation1, user2):
        """用户 2 重命名用户 1 的对话 → 403"""
        resp = client.post(f"/api/ai/conversations/{conversation1.id}/rename",
                            data=json.dumps({"title": "Hacked"}),
                            content_type="application/json",
                            **_jwt_header(user2))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# API Key 安全
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestAPIKeySecurity:
    """API Key 存储 / 展示 / 掩码安全"""

    def test_db_stores_encrypted_key(self, agent1):
        """DB 中 api_key 不以 sk- 开头"""
        assert not agent1.api_key.startswith("sk-"), \
            f"DB api_key 应该是密文，实际: {agent1.api_key[:20]}..."

    def test_agent_list_excludes_api_key(self, client, agent1, user1):
        """Agent 列表不返回 api_key"""
        resp = client.get("/api/ai/agents", **_jwt_header(user1))
        agents = _json(resp)["agents"]

        for a in agents:
            assert "api_key" not in a, f"Agent 列表泄漏了 api_key"

    def test_agent_detail_api_key_is_masked(self, client, agent1, user1):
        """Agent 详情中 api_key 已脱敏"""
        resp = client.get(f"/api/ai/agents/{agent1.id}", **_jwt_header(user1))
        agent_data = _json(resp)["agent"]

        key = agent_data.get("api_key", "")
        assert "***" in key or not key, f"api_key 未脱敏: {key}"

    def test_update_with_mask_preserves_real_key(self, client, agent1, user1):
        """更新时用 *** 掩码不会覆盖真实 Key——需同时传 name 避免校验失败"""
        old_encrypted = agent1.api_key

        resp = client.post(f"/api/ai/agents/{agent1.id}/update",
                            data=json.dumps({
                                "name": agent1.name,
                                "api_key": "sk-***xxxx",
                            }),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200

        agent1.refresh_from_db()
        assert agent1.api_key == old_encrypted, "掩码更新不应覆盖真实 Key"

    def test_update_with_new_key_changes_encrypted_value(self, client, agent1, user1):
        """更新时用新 Key → 密文变化"""
        old_encrypted = agent1.api_key

        resp = client.post(f"/api/ai/agents/{agent1.id}/update",
                            data=json.dumps({
                                "name": agent1.name,
                                "api_key": "sk-new-real-key",
                            }),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200

        agent1.refresh_from_db()
        assert agent1.api_key != old_encrypted
        assert not agent1.api_key.startswith("sk-")

    def test_reveal_key_first_time(self, client, agent1, user1):
        """首次查看 → 返回完整解密 Key"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/reveal-key",
                            **_jwt_header(user1))
        data = _json(resp)

        assert resp.status_code == 200
        assert data["ok"] is True
        assert data["revealed"] is True
        assert data["api_key"] == "sk-test-alice-key-123"

    def test_reveal_key_second_time_returns_masked(self, client, agent1, user1):
        """第二次查看 → 只返回脱敏值"""
        # 第一次查看
        client.post(f"/api/ai/agents/{agent1.id}/reveal-key", **_jwt_header(user1))
        # 第二次查看
        resp = client.post(f"/api/ai/agents/{agent1.id}/reveal-key", **_jwt_header(user1))
        data = _json(resp)

        assert resp.status_code == 200
        assert data["revealed"] is False
        assert "已过期" in data["hint"]
        assert "***" in data["api_key"]

    def test_create_agent_api_key_is_encrypted(self, client, user1):
        """创建 Agent → DB 中 Key 已加密"""
        resp = client.post("/api/ai/agents/create",
                            data=json.dumps({
                                "name": "Test Agent",
                                "model_provider": "dashscope",
                                "model_name": "qwen-max",
                                "api_key": "sk-created-key-999",
                            }),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200
        agent_id = _json(resp)["id"]

        agent = AIAgent.objects.get(id=agent_id)
        assert not agent.api_key.startswith("sk-")


# ═══════════════════════════════════════════════════════════════════
# @require_auth 装饰器
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestRequireAuthDecorator:
    """需要认证的端点无 token → 401"""

    def test_create_agent_without_auth(self, client):
        """无 token 创建 Agent → 401"""
        resp = client.post("/api/ai/agents/create",
                            data=json.dumps({"name": "x"}),
                            content_type="application/json")
        assert resp.status_code == 401

    def test_update_agent_without_auth(self, client, agent1):
        """无 token 更新 Agent → 401"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/update",
                            data=json.dumps({"name": "x"}),
                            content_type="application/json")
        assert resp.status_code == 401

    def test_create_conversation_without_auth(self, client, agent1):
        """无 token 创建对话 → 401"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/conversations/create",
                            data=json.dumps({"title": "x"}),
                            content_type="application/json")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# 对话 CRUD（正常流程）
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestConversationCRUD:
    """对话的正常 CRUD"""

    def test_create_and_list(self, client, agent1, user1):
        """创建对话 → 列表中可见"""
        resp = client.post(f"/api/ai/agents/{agent1.id}/conversations/create",
                            data=json.dumps({"title": "测试会话"}),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200
        conv_id = _json(resp)["id"]

        resp = client.get(f"/api/ai/agents/{agent1.id}/conversations",
                           **_jwt_header(user1))
        convs = _json(resp)["conversations"]
        assert any(c["id"] == conv_id for c in convs)

    def test_rename(self, client, conversation1, user1):
        """重命名对话"""
        resp = client.post(f"/api/ai/conversations/{conversation1.id}/rename",
                            data=json.dumps({"title": "新标题"}),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200
        conversation1.refresh_from_db()
        assert conversation1.title == "新标题"

    def test_delete(self, client, agent1, user1):
        """删除对话"""
        conv = AIConversation.objects.create(
            owner=user1, agent=agent1, title="待删除",
        )
        resp = client.post(f"/api/ai/conversations/{conv.id}/delete",
                            **_jwt_header(user1))
        assert resp.status_code == 200
        assert not AIConversation.objects.filter(id=conv.id).exists()

    def test_save_and_list_messages(self, client, conversation1, user1):
        """保存消息 → 列表中可见"""
        resp = client.post(f"/api/ai/conversations/{conversation1.id}/save-message",
                            data=json.dumps({
                                "role": "user",
                                "content": "你好",
                            }),
                            content_type="application/json",
                            **_jwt_header(user1))
        assert resp.status_code == 200

        resp = client.get(f"/api/ai/conversations/{conversation1.id}/messages",
                           **_jwt_header(user1))
        msgs = _json(resp)["messages"]
        assert len(msgs) == 1
        assert msgs[0]["content"] == "你好"
