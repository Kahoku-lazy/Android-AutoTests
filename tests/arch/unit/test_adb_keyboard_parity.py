from __future__ import annotations

import pytest

from engines.ae_harness.tools.adb import ime
from utils import adb_keyboard

pytestmark = [pytest.mark.unit]

_FIELDS = ("VERSION", "PACKAGE", "IME_ID", "URL", "SIZE", "SHA256", "CHUNK_CHARS")


def test_constants_are_in_sync() -> None:
    for name in _FIELDS:
        assert getattr(ime, name) == getattr(adb_keyboard, name), name


def test_text_encoding_is_in_sync() -> None:
    sample = "中文😸ABC"
    assert ime.encode_text(sample) == adb_keyboard.encode_text(sample)
    assert ime.split_chunks(sample * 400) == adb_keyboard.split_chunks(sample * 400)
