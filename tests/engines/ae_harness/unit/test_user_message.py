"""用户消息构造：名字固定为 user，正文原样保留。"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.messages import user_message

pytestmark = [pytest.mark.unit]


def test_user_message_keeps_name_and_content():
    message = user_message("打开设置")
    assert message.name == "user"
    assert message.content[0].text == "打开设置"
