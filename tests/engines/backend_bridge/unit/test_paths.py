"""平台报告根目录：末三级约定与绝对路径。

只测 `reports/paths.py`。不测运行入口与角色装配。
"""

from __future__ import annotations

import pytest

from engines.backend_bridge.reports import REPORT_ROOT

pytestmark = [pytest.mark.unit]


def test_report_root_ends_with_agents_bridge():
    """报告根目录的末三级固定为 logs/agents/backend_bridge。"""
    assert REPORT_ROOT.parts[-3:] == ("logs", "agents", "backend_bridge")


def test_report_root_is_absolute():
    """根目录解析成绝对路径，不依赖当前工作目录。"""
    assert REPORT_ROOT.is_absolute()
