"""验收截图工具包装：按被包装实现的签名决定是否转发 user_id。"""

from __future__ import annotations

import pytest

from engines.ai.agents.verifier import _force_keep_local_screenshot


@pytest.mark.unit
def test_engine_owned_implementation_without_user_id():
    """引擎自带实现不接受 user_id：包装后 MUST NOT 因它报错，且强制 keep_local=True。"""
    calls: list[dict] = []

    def screenshot_page(serial: str, keep_local: bool = True) -> dict:
        calls.append({"serial": serial, "keep_local": keep_local})
        return {"screenshot_path": "inspector/shots/a.png"}

    wrapped = _force_keep_local_screenshot(screenshot_page)

    result = wrapped("R5CT62RH88F", keep_local=False, user_id="u-1")

    assert result["screenshot_path"] == "inspector/shots/a.png"
    assert calls == [{"serial": "R5CT62RH88F", "keep_local": True}]


@pytest.mark.unit
def test_platform_implementation_keeps_user_id():
    """平台实现声明了 user_id：包装后仍把归属传下去。"""
    calls: list[dict] = []

    def screenshot_page(serial: str, keep_local: bool = True, user_id: str = "") -> dict:
        calls.append({"serial": serial, "keep_local": keep_local, "user_id": user_id})
        return {"screenshot_path": "inspector/shots/b.png"}

    wrapped = _force_keep_local_screenshot(screenshot_page)

    wrapped("S1", keep_local=False, user_id="u-2")

    assert calls == [{"serial": "S1", "keep_local": True, "user_id": "u-2"}]
