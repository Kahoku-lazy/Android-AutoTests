"""
单文件调试指令：python -m pytest tests/engines/device/unit/test_device_log_tools.py -vv -s --tb=short

1. tail_lines: 尾部行读取（顺序、CRLF、缺失文件、limit 边界）。
2. KeywordIndex: 小写匹配（关键词带大写也能命中）、坏文件降级为空索引。
"""

from __future__ import annotations

import json

import pytest

from engines.device.logbus import KeywordIndex
from engines.device.logfiles import tail_lines

pytestmark = [pytest.mark.unit]


class TestTailLines:
    """tail_lines：按块倒读，返回旧→新的尾部行。"""

    def test_returns_last_lines_in_file_order(self, tmp_path):
        """只取最后 N 行，顺序仍是旧→新。"""
        path = tmp_path / "device.log"
        path.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")

        assert tail_lines(path, 2) == ["d", "e"]

    def test_strips_crlf(self, tmp_path):
        """CRLF 的 \\r 在返回前去掉。"""
        path = tmp_path / "device.log"
        path.write_bytes(b"one\r\ntwo\r\n")

        assert tail_lines(path, 2) == ["one", "two"]

    def test_missing_file_returns_empty(self, tmp_path):
        """文件不存在时返回空列表，不抛异常。"""
        assert tail_lines(tmp_path / "nope.log", 10) == []

    def test_limit_zero_returns_empty(self, tmp_path):
        """limit 为 0（或负数）时直接返回空列表。"""
        path = tmp_path / "device.log"
        path.write_text("a\n", encoding="utf-8")

        assert tail_lines(path, 0) == []
        assert tail_lines(path, -5) == []

    def test_whole_file_shorter_than_limit(self, tmp_path):
        """文件行数不足 limit 时整份返回。"""
        path = tmp_path / "device.log"
        path.write_text("a\nb\n", encoding="utf-8")

        assert tail_lines(path, 100) == ["a", "b"]


class TestKeywordIndexCase:
    """KeywordIndex：行文本与关键词都按小写比较，返回原始写法。"""

    def test_uppercase_keyword_matches_lowercase_line(self):
        """真相源里的关键词带大写时也能命中。"""
        index = KeywordIndex({"Switch_On": [{"id": 0}]})

        assert index.match("device: switch_on done") == [("Switch_On", [{"id": 0}])]

    def test_lowercase_keyword_matches_uppercase_line(self):
        """日志行带大写时照旧命中（行也是小写比较）。"""
        index = KeywordIndex({"switch_on": [{"id": 0}]})

        assert index.match("DEVICE: SWITCH_ON DONE") == [("switch_on", [{"id": 0}])]

    def test_empty_mapping_matches_nothing(self):
        """空索引不匹配任何文本。"""
        assert KeywordIndex().match("switch_on") == []


class TestKeywordIndexFromFile:
    """from_file：文件缺失或损坏时降级为空索引，不向调用方抛异常。"""

    def test_missing_file_returns_empty_index(self, tmp_path):
        """路径不存在时返回空索引。"""
        index = KeywordIndex.from_file(tmp_path / "nope.json")

        assert not index
        assert index.match("switch_on") == []

    def test_non_utf8_file_returns_empty_index(self, tmp_path):
        """非 UTF-8 字节属于「损坏」：降级为空索引，不让 UnicodeDecodeError 冒泡。"""
        path = tmp_path / "keywords.json"
        path.write_bytes(b'{"keywords": {"switch_on": "\xff\xfe"}}')

        index = KeywordIndex.from_file(path)

        assert not index

    def test_loads_keywords_object(self, tmp_path):
        """正常文件从 keywords 段加载。"""
        path = tmp_path / "keywords.json"
        path.write_text(json.dumps({"keywords": {"switch_on": [{"id": 0}]}}), encoding="utf-8")

        index = KeywordIndex.from_file(path)

        assert index.match("switch_on") == [("switch_on", [{"id": 0}])]
