"""按型号的关键词目录装载：读得到、缺失降级、非法型号名不放行。"""

from __future__ import annotations

import pytest

from engines.agents.config.log_keywords import load_log_keywords

pytestmark = [pytest.mark.unit]


def test_known_sku_returns_catalog():
    """已维护的型号能读到「功能点 → 关键词」正文。"""
    text = load_log_keywords("H6810")

    assert "timer_configs_set_success" in text
    assert "awaken_configs_set_success" in text
    assert "sleep_configs_set_success" in text


def test_unknown_sku_returns_empty():
    """未维护的型号返回空串，不抛异常。"""
    assert load_log_keywords("H0000") == ""


def test_empty_sku_returns_empty():
    """空型号返回空串。"""
    assert load_log_keywords("   ") == ""


def test_path_like_sku_is_rejected():
    """带路径分隔符的型号名不放行，避免拼出目录外路径。"""
    assert load_log_keywords("../../etc/passwd") == ""
