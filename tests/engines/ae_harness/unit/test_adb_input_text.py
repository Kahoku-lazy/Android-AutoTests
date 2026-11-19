"""adb 文本输入：送进设备 shell 前必须加引号。

只测参数拼装，不连真机。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.tools.adb import tools

pytestmark = [pytest.mark.unit]


def test_shell_quote_wraps_metacharacters():
    """分号、管道、反引号与单引号都留在引号内。"""
    quoted = tools._shell_quote("hi; rm -rf /sdcard/`x` | cat")  # noqa: SLF001

    assert quoted.startswith("'")
    assert quoted.endswith("'")
    assert ";" in quoted


def test_input_text_quotes_the_shell_argument(monkeypatch: pytest.MonkeyPatch):
    """模型给出的文本以单个带引号参数交给 adb，不再按空格拆开。"""
    captured: list[list[str]] = []

    def fake_run(args: list[str], *, serial: str = "", timeout: int = 30) -> str:
        captured.append(args)
        return ""

    monkeypatch.setattr(tools, "resolve_serial", lambda _serial: "device-1")
    monkeypatch.setattr(tools, "run_adb", fake_run)

    result = tools.adb_input_text("hello world; id", serial="device-1")

    assert '"status": true' in result
    assert captured == [["shell", "input", "text", "'hello%sworld;%sid'"]]


def test_input_text_rejects_non_ascii_before_adb(monkeypatch: pytest.MonkeyPatch):
    """非 ASCII 在调用 adb 之前就拒绝。"""

    def fail(*_args, **_kwargs):
        raise AssertionError("不应该调用 adb")

    monkeypatch.setattr(tools, "run_adb", fail)

    result = tools.adb_input_text("中文")

    assert '"status": false' in result
