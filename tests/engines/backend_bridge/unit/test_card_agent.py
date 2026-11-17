"""名片装配：系统提示词由调用方传入，且不引用控制台入口。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def test_card_agent_does_not_import_console_assistant():
    source = Path("engines/backend_bridge/agents/card_agent.py").read_text(encoding="utf-8")
    assert "ae_harness.assistant" not in source
    assert "ASSISTANT_CARD_PROMPT" not in source
    assert "AppendPrompt" not in source
