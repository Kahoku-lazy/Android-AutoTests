"""ai_assistant.api 跨模块导出契约。"""

from __future__ import annotations

import pytest

from apps.ai_assistant import api

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def test_filter_agents_for_user_is_exported():
    assert "filter_agents_for_user" in api.__all__
    assert callable(api.filter_agents_for_user)
