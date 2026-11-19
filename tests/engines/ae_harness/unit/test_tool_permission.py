"""工具权限放行契约：权限检查必须交出 PermissionDecision 实例（harness-tool-permission）。

守护 P0 缺陷不回归：FunctionTool(permission=...) 只收决策实例，
传可调用对象时 check_permissions 会把函数原样交给权限引擎。
零 I/O：不注入写入函数、不绑定正文，只查权限决策。
"""

from __future__ import annotations

import pytest

from agentscope.permission import PermissionBehavior, PermissionDecision

from engines.ae_harness.tools.case_library.tools import build_case_library_tools
from engines.ae_harness.tools.document.tools import build_document_tools

pytestmark = [pytest.mark.unit]


async def test_case_writer_permission_is_allow_decision():
    """写工具（保存用例）的权限检查返回允许决策实例，不是可调用对象。"""
    tool = build_case_library_tools()[0]
    decision = await tool.check_permissions()
    assert isinstance(decision, PermissionDecision)
    assert not callable(decision)
    assert decision.behavior == PermissionBehavior.ALLOW


async def test_document_reader_permission_is_allow_decision():
    """只读文档工具的权限检查返回允许决策实例。"""
    tool = build_document_tools()[0]
    decision = await tool.check_permissions()
    assert isinstance(decision, PermissionDecision)
    assert not callable(decision)
    assert decision.behavior == PermissionBehavior.ALLOW


async def test_no_ask_fallback_for_unattended_runs():
    """无人值守口径：两个域的决策都不是「询问用户」，不会挂起等确认。"""
    for tool in [*build_case_library_tools(), *build_document_tools()]:
        decision = await tool.check_permissions()
        assert decision.behavior != PermissionBehavior.ASK
