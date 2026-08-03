"""Django JWT 中间件单元测试 — mock Request，不依赖 Redis/DB。

覆盖：
- 公开路径放行（auth / tools / admin / static / screenshot）
- 需鉴权路径：无 token → 401；伪造 token → 401；合法 token → 注入 user_id
- 非 /api/ 路径直接放行
"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from gateway.middleware import JWTAuthenticationMiddleware, PUBLIC_PREFIXES, _is_public
from shared.auth.jwt_auth import create_access_token


@pytest.fixture
def middleware():
    """返回中间件实例。get_response 返回一个 mock，用于验证请求到达了视图。"""
    response = MagicMock()
    response.status_code = 200
    return JWTAuthenticationMiddleware(lambda req: response)


# ═══════════════════════════════════════════════════════════════════
# _is_public
# ═══════════════════════════════════════════════════════════════════


class TestIsPublic:
    """公开路径判断"""

    @pytest.mark.parametrize("path", [
        "/api/ai/auth/login",
        "/api/ai/auth/register",
        "/api/ai/auth/refresh",
        "/api/ai/auth/logout",
        "/api/ai/auth/me",
    ])
    def test_auth_paths_are_public(self, path):
        """所有 auth 路径都是公开的"""
        assert _is_public(path) is True

    @pytest.mark.parametrize("path", [
        "/api/ai/tools/schemas",
        "/api/ai/tools/devices/list_online",
        "/api/ai/tools/agent-config/1",
    ])
    def test_tools_paths_are_public(self, path):
        """AgentScope 工具网关是公开的（JWT 由 AgentScope 自行传递）"""
        assert _is_public(path) is True

    @pytest.mark.parametrize("path", [
        "/admin/",
        "/admin/login/",
        "/admin/ai_assistant/aiagent/",
    ])
    def test_admin_paths_are_public(self, path):
        """Django Admin 路径是公开的"""
        assert _is_public(path) is True

    @pytest.mark.parametrize("path", [
        "/static/css/app.css",
        "/static/js/main.js",
    ])
    def test_static_paths_are_public(self, path):
        """静态文件路径是公开的"""
        assert _is_public(path) is True

    @pytest.mark.parametrize("path", [
        "/api/runner/step-screenshots/some-file.png",
        "/api/runner/step-screenshots/2024/case1.png",
    ])
    def test_screenshot_paths_are_public(self, path):
        """截图路径是公开的（img 标签无法带 Authorization header）"""
        assert _is_public(path) is True

    @pytest.mark.parametrize("path", [
        "/api/ai/agents",
        "/api/ai/agents/1",
        "/api/ai/agents/1/update",
        "/api/ai/agents/1/conversations",
        "/api/ai/conversations/1/messages",
        "/api/ai/upload-avatar",
        "/api/ai/knowledge/status",
    ])
    def test_protected_paths_are_not_public(self, path):
        """业务 API 不是公开路径"""
        assert _is_public(path) is False


# ═══════════════════════════════════════════════════════════════════
# 公开路径放行
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestPublicPathPassThrough:
    """公开路径直接放行，不检查 token"""

    def test_auth_login_passes_through(self, middleware):
        """登录接口无需 token"""
        request = RequestFactory().post("/api/ai/auth/login",
                                         data="{}",
                                         content_type="application/json")
        response = middleware(request)
        assert response.status_code == 200

    def test_tools_gateway_passes_through(self, middleware):
        """工具网关无需 token（AgentScope 内部调用）"""
        request = RequestFactory().post("/api/ai/tools/devices/list_online",
                                         data="{}",
                                         content_type="application/json")
        response = middleware(request)
        assert response.status_code == 200

    def test_admin_passes_through(self, middleware):
        """Django Admin 无需 token"""
        request = RequestFactory().get("/admin/")
        response = middleware(request)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# 非 /api/ 路径
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestNonApiPaths:
    """非 API 路径直接放行"""

    def test_root_path_passes_through(self, middleware):
        """根路径无需鉴权"""
        request = RequestFactory().get("/")
        response = middleware(request)
        assert response.status_code == 200

    def test_random_path_passes_through(self, middleware):
        """非 /api/ 路径无需鉴权"""
        request = RequestFactory().get("/some-page/")
        response = middleware(request)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# 需鉴权路径
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestProtectedPathNoToken:
    """受保护路径 + 无 token"""

    def test_no_auth_header_returns_401(self, middleware):
        """没有 Authorization header → 401"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json")
        response = middleware(request)

        assert response.status_code == 401
        content = response.content.decode()
        assert "Authorization header required" in content

    def test_wrong_auth_scheme_returns_401(self, middleware):
        """用了 Basic 而非 Bearer → 401"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION="Basic YWRtaW46YWRtaW4=")
        response = middleware(request)

        assert response.status_code == 401
        assert "Authorization header required" in response.content.decode()


@pytest.mark.django_db
class TestProtectedPathInvalidToken:
    """受保护路径 + 无效 token"""

    def test_fake_token_returns_401(self, middleware):
        """伪造 token → 401"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION="Bearer fake.token.here")
        response = middleware(request)

        assert response.status_code == 401
        assert "Invalid or expired token" in response.content.decode()

    def test_empty_token_returns_401(self, middleware):
        """Bearer 后面是空字符串 → 401"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION="Bearer ")
        response = middleware(request)

        assert response.status_code == 401
        assert "Invalid or expired token" in response.content.decode()

    def test_garbage_token_returns_401(self, middleware):
        """随机字符串 token → 401"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION="Bearer abcdefghijklmnop")
        response = middleware(request)

        assert response.status_code == 401


@pytest.mark.django_db
class TestProtectedPathValidToken:
    """受保护路径 + 合法 token"""

    def test_valid_token_injects_user_id_and_passes(self, middleware):
        """合法 token → 注入 request.user_id → 放行"""
        token = create_access_token("42")
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION=f"Bearer {token}")
        response = middleware(request)

        assert response.status_code == 200
        assert request.user_id == "42"

    def test_valid_token_on_different_endpoint(self, middleware):
        """不同业务端点都能拿到 user_id"""
        token = create_access_token("99")
        request = RequestFactory().get("/api/ai/agents/1/conversations",
                                        HTTP_AUTHORIZATION=f"Bearer {token}")
        response = middleware(request)

        assert response.status_code == 200
        assert request.user_id == "99"

    def test_token_with_correct_user_sub(self, middleware):
        """验证 sub 字段正确注入"""
        token = create_access_token("12345")
        request = RequestFactory().post("/api/ai/conversations/1/rename",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION=f"Bearer {token}")
        response = middleware(request)

        assert response.status_code == 200
        assert request.user_id == "12345"


# ═══════════════════════════════════════════════════════════════════
# 错误消息不泄露内部细节
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestErrorMessageSecurity:
    """401 错误消息不泄露 token 具体为何无效"""

    def test_error_message_is_generic(self, middleware):
        """不管什么原因，返回的消息都是同一句话"""
        request = RequestFactory().post("/api/ai/agents",
                                         data="{}",
                                         content_type="application/json",
                                         HTTP_AUTHORIZATION="Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI.e30.")
        response = middleware(request)

        error = response.content.decode()
        # 统一模糊消息，不区分"过期"/"签名错误"/"格式不对"
        assert error == '{"ok": false, "error": "Invalid or expired token"}'

    def test_no_token_message_is_different(self, middleware):
        """无 token 和无效 token 的错误消息不同是有意为之"""
        # 无 token → 明确告知缺少 Authorization header
        request_no_auth = RequestFactory().post("/api/ai/agents",
                                                 data="{}",
                                                 content_type="application/json")
        r1 = middleware(request_no_auth)
        # 有 token 但无效 → 模糊消息
        request_bad_token = RequestFactory().post("/api/ai/agents",
                                                   data="{}",
                                                   content_type="application/json",
                                                   HTTP_AUTHORIZATION="Bearer x")
        r2 = middleware(request_bad_token)

        assert r1.content.decode() != r2.content.decode()
