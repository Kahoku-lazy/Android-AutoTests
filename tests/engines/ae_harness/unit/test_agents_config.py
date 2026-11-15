"""配置读取口：提示词与按型号的日志关键词目录。

覆盖 `openspec/specs/agent-harness` 的「提示词唯一配置入口」与本变更的日志关键词迁移。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents import config

pytestmark = [pytest.mark.unit]


def test_load_prompt_reads_verifier_prompt():
    """验收者提示词已合并为旧 agents 版的较厚版本。"""
    text = config.load_prompt("UI_VERIFIER_PROMPT")

    assert "验收" in text
    assert len(text) > 2000


def test_load_log_keywords_hits_known_sku():
    """按型号命中关键词目录。"""
    text = config.load_log_keywords("H6810")

    assert text
    assert text == text.strip()


def test_load_log_keywords_rejects_illegal_sku():
    """非法型号名不拼路径，直接降级为空串。"""
    assert config.load_log_keywords("../config") == ""
    assert config.load_log_keywords("H6810/../../x") == ""


def test_load_log_keywords_missing_sku_degrades():
    """未知型号返回空串而不是抛异常：该步照常开始，提示词降级为截图核对。"""
    assert config.load_log_keywords("NOT_A_SKU_9") == ""
    assert config.load_log_keywords("") == ""
