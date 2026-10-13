"""灰盒·单元测试 — xpath get_text 多命中时按下标列出全部元素。

零设备：用假 u2 替身喂给 AndroidControl，断言下标与点击所用下标一致。
"""

import pytest

from engines.device.android.android_device import AndroidControl


class _Element:
    def __init__(self, text: str, bounds: str):
        self.attrib = {"text": text, "bounds": bounds}


class _XPath:
    def __init__(self, elements):
        self._elements = elements

    def all(self):
        return list(self._elements)


class _U2:
    def __init__(self, elements):
        self._elements = elements

    def xpath(self, _expr):
        return _XPath(self._elements)


class _Connection:
    def __init__(self, elements):
        self.u2 = _U2(elements)


@pytest.mark.unit
def test_get_text_matches_lists_every_hit_with_index():
    """多个相同文本时，items 按命中顺序标下标，text 取入参 index 那一条。"""
    control = AndroidControl(
        _Connection(
            [
                _Element("ON", "[10,20][30,40]"),
                _Element("ON", "[110,20][130,40]"),
            ]
        )
    )
    payload = control.get_text_matches("//android.widget.TextView[@text='ON']", index=1)
    assert payload["count"] == 2
    assert payload["index"] == 1
    assert payload["text"] == "ON"
    assert payload["items"] == [
        {"index": 0, "text": "ON", "bounds": "[10,20][30,40]"},
        {"index": 1, "text": "ON", "bounds": "[110,20][130,40]"},
    ]


@pytest.mark.unit
def test_get_text_matches_empty_when_nothing_hits():
    """未命中时 count 为 0，text 为空，items 为空列表。"""
    control = AndroidControl(_Connection([]))
    payload = control.get_text_matches("//android.widget.TextView[@text='ON']")
    assert payload == {"text": "", "index": 0, "count": 0, "items": []}
