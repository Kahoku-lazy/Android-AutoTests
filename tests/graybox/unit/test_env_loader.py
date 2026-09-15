"""`.env` 加载单一实现（`config/env.py`）的行为契约。"""

from __future__ import annotations

import os

import pytest

from config.env import load_dotenv

pytestmark = [pytest.mark.unit]


def _write(tmp_path, text: str):
    path = tmp_path / ".env"
    path.write_text(text, encoding="utf-8")
    return path


def test_three_quote_styles(tmp_path, monkeypatch):
    """三种写法都要能解析：KEY=v / KEY="v" / KEY='v'。"""
    monkeypatch.delenv("D0_PLAIN", raising=False)
    monkeypatch.delenv("D0_DOUBLE", raising=False)
    monkeypatch.delenv("D0_SINGLE", raising=False)
    path = _write(tmp_path, "D0_PLAIN=v\nD0_DOUBLE=\"v\"\nD0_SINGLE='v'\n")
    load_dotenv(path)
    assert os.environ["D0_PLAIN"] == "v"
    assert os.environ["D0_DOUBLE"] == "v"
    assert os.environ["D0_SINGLE"] == "v"


def test_existing_environment_wins(tmp_path, monkeypatch):
    """真实环境变量优先：.env 不得覆盖已存在的键。"""
    monkeypatch.setenv("D0_EXISTING", "from-env")
    path = _write(tmp_path, "D0_EXISTING=from-file\n")
    load_dotenv(path)
    assert os.environ["D0_EXISTING"] == "from-env"


def test_comments_blank_lines_and_invalid_lines_skipped(tmp_path, monkeypatch):
    monkeypatch.delenv("D0_KEPT", raising=False)
    path = _write(tmp_path, "# comment\n\nD0_KEPT=1\nnot-a-pair\n")
    load_dotenv(path)
    assert os.environ["D0_KEPT"] == "1"
    assert "not-a-pair" not in os.environ


def test_missing_file_is_noop(tmp_path):
    """文件不存在时静默返回（显式忽略，不抛异常）。"""
    load_dotenv(tmp_path / "nope.env")


def test_value_with_equals_sign_is_preserved(tmp_path, monkeypatch):
    """值里含 `=` 时只按第一个 `=` 切分。"""
    monkeypatch.delenv("D0_URL", raising=False)
    path = _write(tmp_path, "D0_URL=mysql://u:p@h/db?a=1\n")
    load_dotenv(path)
    assert os.environ["D0_URL"] == "mysql://u:p@h/db?a=1"
