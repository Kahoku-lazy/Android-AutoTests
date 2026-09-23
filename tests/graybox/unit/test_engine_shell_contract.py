"""灰盒·单元测试 — 引擎 shell 返回值归一化（engine-protocol「感知标准化」）。

零设备、零 I/O：以真 ShellResponse 作为假 u2 的返回值，断言引擎契约方法把
原生响应对象归一化为标准输出字符串，MUST NOT 把 (输出, 退出码) 元组形态交给调用方。
"""

import inspect

import pytest

from uiautomator2.abstract import ShellResponse

from engines.device.android.u2 import U2Engine
from engines.device.base import UiEngine


class _FakeU2:
    """最小 u2 替身：shell 返回 uiautomator2 的原生响应对象。"""

    def __init__(self, output: str, exit_code: int = 0):
        self._response = ShellResponse(output=output, exit_code=exit_code)

    def shell(self, cmd):
        return self._response


@pytest.mark.unit
@pytest.mark.device_pool
def test_protocol_declares_shell_returns_str():
    """协议声明 shell 返回字符串。"""
    assert inspect.signature(UiEngine.shell).return_annotation is str


@pytest.mark.unit
@pytest.mark.device_pool
def test_shell_normalizes_native_response_to_str():
    """底层返回 ShellResponse 时，契约方法返回标准输出字符串。"""
    engine = U2Engine()
    engine._u2 = _FakeU2(output="package:com.demo\npackage:com.other\n")

    result = engine.shell("pm list packages")

    assert isinstance(result, str)
    assert result == "package:com.demo\npackage:com.other\n"
    assert len(result.splitlines()) == 2


@pytest.mark.unit
@pytest.mark.device_pool
def test_shell_does_not_leak_tuple_shape():
    """MUST NOT 返回 (输出, 退出码) 元组形态——避免上层静默当成结构化数据。"""
    engine = U2Engine()
    engine._u2 = _FakeU2(output="SM-S9010\n", exit_code=0)

    result = engine.shell("getprop ro.product.model")

    assert not isinstance(result, tuple)
    assert result == "SM-S9010\n"
