"""AgentScope Tool 权限单元测试 — 纯逻辑，不依赖 AgentScope 框架。

覆盖：
- check_platform_permission：读工具放行 / 写工具 + 未登录拒绝 / 写工具 + 已登录放行
- ToolContext 字段正确性
- AgentScope JWT 鉴权（依赖注入）
"""

from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from agentscope_service.tools.tool_context import (
    ToolContext,
    check_platform_permission,
)
from agentscope_service.auth import get_current_user_id, get_stored_jwt


# ═══════════════════════════════════════════════════════════════════
# ToolContext
# ═══════════════════════════════════════════════════════════════════


class TestToolContext:
    """ToolContext 数据类"""

    def test_default_values_are_empty_strings(self):
        ctx = ToolContext()
        assert ctx.user_id == ""
        assert ctx.agent_id == ""
        assert ctx.session_id == ""
        assert ctx.jwt == ""

    def test_all_fields_settable(self):
        ctx = ToolContext(
            user_id="42",
            agent_id="agent-1",
            session_id="sess-abc",
            jwt="eyJhbGci...",
        )
        assert ctx.user_id == "42"
        assert ctx.agent_id == "agent-1"
        assert ctx.session_id == "sess-abc"
        assert ctx.jwt == "eyJhbGci..."


# ═══════════════════════════════════════════════════════════════════
# check_platform_permission
# ═══════════════════════════════════════════════════════════════════


class TestCheckPlatformPermission:
    """Tool 平台权限检查"""

    def test_read_tool_always_allowed_even_without_context(self):
        """读工具：即使无 context 也放行"""
        tool = MagicMock()
        tool.is_read_only = True
        tool._ctx = None  # 无 context

        decision = check_platform_permission(tool)
        assert decision.behavior.name == "ALLOW"

    def test_read_tool_always_allowed_with_context(self):
        """读工具：有 context 也放行"""
        tool = MagicMock()
        tool.is_read_only = True
        tool._ctx = ToolContext(user_id="42")

        decision = check_platform_permission(tool)
        assert decision.behavior.name == "ALLOW"

    def test_write_tool_no_context_denied(self):
        """写工具 + 无 context → 拒绝"""
        tool = MagicMock()
        tool.is_read_only = False
        tool._ctx = None

        decision = check_platform_permission(tool)
        assert decision.behavior.name == "DENY"

    def test_write_tool_no_user_id_denied(self):
        """写工具 + user_id 为空 → 拒绝"""
        tool = MagicMock()
        tool.is_read_only = False
        tool._ctx = ToolContext(user_id="")  # 空 user_id

        decision = check_platform_permission(tool)
        assert decision.behavior.name == "DENY"
        assert "登录" in decision.message

    def test_write_tool_with_user_id_allowed(self):
        """写工具 + 已登录用户 → 放行"""
        tool = MagicMock()
        tool.is_read_only = False
        tool._ctx = ToolContext(user_id="42")

        decision = check_platform_permission(tool)
        assert decision.behavior.name == "ALLOW"

    def test_deny_message_is_chinese_and_user_facing(self):
        """拒绝消息是中文"""
        tool = MagicMock()
        tool.is_read_only = False
        tool._ctx = ToolContext()

        decision = check_platform_permission(tool)
        assert "登录" in decision.message

    def test_allow_message_is_english_internal(self):
        """放行消息是英文"""
        tool = MagicMock()
        tool.is_read_only = True

        decision = check_platform_permission(tool)
        assert "Read-only" in decision.message


# ═══════════════════════════════════════════════════════════════════
# AgentScope JWT 鉴权
# ═══════════════════════════════════════════════════════════════════


class TestAgentScopeAuth:
    """AgentScope get_current_user_id"""

    @pytest.mark.asyncio
    async def test_no_authorization_header_raises_401(self):
        """没有 Authorization header → HTTPException 401"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization="")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_access_token_returns_user_id(self):
        """合法 access token → 返回 user_id"""
        from shared.auth.jwt_auth import create_access_token

        token = create_access_token("42")
        user_id = await get_current_user_id(authorization=f"Bearer {token}")
        assert user_id == "42"

    @pytest.mark.asyncio
    async def test_valid_token_stores_jwt_in_contextvar(self):
        """验证通过后 JWT 存入 ContextVar"""
        from shared.auth.jwt_auth import create_access_token

        token = create_access_token("42")
        await get_current_user_id(authorization=f"Bearer {token}")

        stored = get_stored_jwt()
        assert stored == token

    @pytest.mark.asyncio
    async def test_refresh_token_as_access_raises_401(self):
        """拿 refresh token 当 access → 401"""
        from fastapi import HTTPException
        from shared.auth.jwt_auth import create_refresh_token

        refresh_token = create_refresh_token("42")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization=f"Bearer {refresh_token}")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_bearer_prefix_still_works(self):
        """Authorization header 不带 Bearer 前缀时也当作 token 处理"""
        from shared.auth.jwt_auth import create_access_token

        token = create_access_token("42")
        user_id = await get_current_user_id(authorization=token)  # 无 Bearer 前缀
        assert user_id == "42"

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401_with_detail(self):
        """无效 token → 401 + 错误详情"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization="Bearer not.a.real.token")
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_empty_bearer_raises_401(self):
        """Bearer 后面什么都没有 → 401"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization="Bearer ")
        assert exc_info.value.status_code == 401
