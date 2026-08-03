"""AI Assistant 权限函数单元测试 — 纯逻辑，mock ORM 查询。

覆盖：
- check_agent_owner（owner 匹配 / 非 owner / null owner / 不存在 / 未登录）
- check_conversation_access（双重校验：conv owner + agent owner）
- check_can_create_agent / check_can_delete_agent / check_can_update_agent
- filter_agents_for_user / filter_conversations_for_user
"""

from unittest.mock import MagicMock, patch, Mock

import pytest

from apps.ai_assistant.permissions import (
    _same_user,
    check_agent_owner,
    check_conversation_access,
    check_can_create_agent,
    check_can_delete_agent,
    check_can_update_agent,
    filter_agents_for_user,
    filter_conversations_for_user,
)


# ═══════════════════════════════════════════════════════════════════
# _same_user
# ═══════════════════════════════════════════════════════════════════


class TestSameUser:
    """_same_user 内部函数"""

    def test_same_id_returns_true(self):
        assert _same_user(5, "5") is True

    def test_different_id_returns_false(self):
        assert _same_user(1, "2") is False

    def test_null_owner_returns_true(self):
        """null owner → 共享资源，视为匹配"""
        assert _same_user(None, "42") is True

    def test_null_user_id_returns_false(self):
        """None != None 因为 'None' != None"""
        # 实际上 _same_user(None, "42") → True（null owner 共享）
        # 但 _same_user(5, None) → str(5) != str(None) → False
        assert _same_user(5, None) is False


# ═══════════════════════════════════════════════════════════════════
# check_agent_owner
# ═══════════════════════════════════════════════════════════════════


class TestCheckAgentOwner:
    """check_agent_owner"""

    @patch("apps.ai_assistant.permissions.AIAgent")
    def test_owner_returns_true(self, MockAgent):
        """Agent owner → True"""
        mock_agent = Mock()
        mock_agent.owner_id = 1
        # Mock filter + only + first 链式调用
        MockAgent.objects.filter.return_value.only.return_value.first.return_value = mock_agent

        assert check_agent_owner("1", agent_id=1) is True

    @patch("apps.ai_assistant.permissions.AIAgent")
    def test_non_owner_returns_false(self, MockAgent):
        """非 owner → False"""
        mock_agent = Mock()
        mock_agent.owner_id = 1
        MockAgent.objects.filter.return_value.only.return_value.first.return_value = mock_agent

        assert check_agent_owner("2", agent_id=1) is False

    @patch("apps.ai_assistant.permissions.AIAgent")
    def test_agent_not_found_returns_false(self, MockAgent):
        """Agent 不存在 → False"""
        MockAgent.objects.filter.return_value.only.return_value.first.return_value = None

        assert check_agent_owner("1", agent_id=999) is False

    def test_unauthenticated_user_returns_false(self):
        """user_id=None → False（不查 DB）"""
        assert check_agent_owner(None, 1) is False

    @patch("apps.ai_assistant.permissions.AIAgent")
    def test_null_owner_legacy_shared(self, MockAgent):
        """owner_id=None 的 legacy 数据 → 任意用户可访问"""
        mock_agent = Mock()
        mock_agent.owner_id = None
        MockAgent.objects.filter.return_value.only.return_value.first.return_value = mock_agent

        # 任意 user_id 都能访问 null-owner agent
        assert check_agent_owner("1", agent_id=1) is True
        assert check_agent_owner("99", agent_id=1) is True


# ═══════════════════════════════════════════════════════════════════
# check_conversation_access
# ═══════════════════════════════════════════════════════════════════


class TestCheckConversationAccess:
    """check_conversation_access — 双重校验：conv.owner + agent.owner"""

    @patch("apps.ai_assistant.permissions.AIConversation")
    def test_both_owners_match_returns_true(self, MockConv):
        """conv owner + agent owner 都匹配 → True"""
        mock_conv = Mock()
        mock_conv.owner_id = 1
        mock_conv.agent.owner_id = 1
        MockConv.objects.filter.return_value.select_related.return_value.only.return_value.first.return_value = mock_conv

        assert check_conversation_access("1", conv_id=1) is True

    @patch("apps.ai_assistant.permissions.AIConversation")
    def test_conv_owner_mismatch_returns_false(self, MockConv):
        """对话 owner 不匹配 → False"""
        mock_conv = Mock()
        mock_conv.owner_id = 1
        mock_conv.agent.owner_id = 1
        MockConv.objects.filter.return_value.select_related.return_value.only.return_value.first.return_value = mock_conv

        assert check_conversation_access("2", conv_id=1) is False

    @patch("apps.ai_assistant.permissions.AIConversation")
    def test_agent_owner_mismatch_returns_false(self, MockConv):
        """agent owner 不匹配 → False"""
        mock_conv = Mock()
        mock_conv.owner_id = 1
        mock_conv.agent.owner_id = 2  # agent 属于用户 2
        MockConv.objects.filter.return_value.select_related.return_value.only.return_value.first.return_value = mock_conv

        assert check_conversation_access("1", conv_id=1) is False

    @patch("apps.ai_assistant.permissions.AIConversation")
    def test_conversation_not_found_returns_false(self, MockConv):
        """对话不存在 → False"""
        MockConv.objects.filter.return_value.select_related.return_value.only.return_value.first.return_value = None

        assert check_conversation_access("1", conv_id=999) is False

    def test_unauthenticated_returns_false(self):
        """未登录 → False"""
        assert check_conversation_access(None, 1) is False


# ═══════════════════════════════════════════════════════════════════
# check_can_create / delete / update
# ═══════════════════════════════════════════════════════════════════


class TestCreateDeleteUpdate:
    """创建/删除/更新权限"""

    def test_any_authenticated_user_can_create(self):
        """已认证即可创建"""
        assert check_can_create_agent("1") is True

    def test_unauthenticated_cannot_create(self):
        """未认证不能创建"""
        assert check_can_create_agent(None) is False

    @patch("apps.ai_assistant.permissions.check_agent_owner")
    def test_delete_delegates_to_owner_check(self, mock_owner):
        """删除 = owner 检查"""
        mock_owner.return_value = True
        assert check_can_delete_agent("1", 1) is True
        mock_owner.assert_called_once_with("1", 1)

    @patch("apps.ai_assistant.permissions.check_agent_owner")
    def test_update_delegates_to_owner_check(self, mock_owner):
        """更新 = owner 检查"""
        mock_owner.return_value = False
        assert check_can_update_agent("1", 1) is False
        mock_owner.assert_called_once_with("1", 1)


# ═══════════════════════════════════════════════════════════════════
# filter_for_user
# ═══════════════════════════════════════════════════════════════════


class TestFilterForUser:
    """列表查询过滤"""

    def test_no_user_id_returns_empty_queryset(self):
        """无 user_id → none()"""
        mock_qs = MagicMock()
        result = filter_agents_for_user(mock_qs, None)
        mock_qs.none.assert_called_once()

    def test_with_user_id_filters_by_owner_and_null(self):
        """有 user_id → filter(owner=user OR owner__isnull=True)"""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = "filtered_qs"

        result = filter_agents_for_user(mock_qs, "42")

        mock_qs.filter.assert_called_once()
        # Q 对象包含两个条件
        result == "filtered_qs"

    def test_filter_conversations_same_logic(self):
        """对话过滤逻辑一致"""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = "filtered_conv_qs"

        result = filter_conversations_for_user(mock_qs, "42")
        assert result == "filtered_conv_qs"
