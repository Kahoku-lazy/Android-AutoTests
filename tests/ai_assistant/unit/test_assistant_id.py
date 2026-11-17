"""助手编号：日期下划线 + 3 位大写，与运营 role_id 的小写集分开。"""

from __future__ import annotations

import re

import pytest

from django.utils import timezone

from backend.apps.ai_assistant.services.assistant_id import (
    ASSISTANT_ID_ALPHABET,
    generate_assistant_id,
    generate_unique_assistant_id,
)
from backend.apps.ai_assistant.services.role_id import ROLE_ID_ALPHABET

pytestmark = [pytest.mark.unit]

_ASSISTANT_ID = re.compile(r"^\d{8}_[0-9A-Z]{3}$")


def test_assistant_id_matches_date_underscore_format():
    now = timezone.now()
    today = (timezone.localtime(now) if timezone.is_aware(now) else now).strftime("%Y%m%d")
    assistant_id = generate_assistant_id()
    assert _ASSISTANT_ID.match(assistant_id)
    assert assistant_id.startswith(f"{today}_")


def test_assistant_ids_are_unique_across_many_draws():
    drawn = {generate_assistant_id() for _ in range(500)}
    assert len(drawn) > 490


def test_alphabet_is_uppercase_and_distinct_from_role_id():
    assert ASSISTANT_ID_ALPHABET == "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert ASSISTANT_ID_ALPHABET != ROLE_ID_ALPHABET
    assert "_" not in ROLE_ID_ALPHABET


def test_unique_generator_skips_taken_ids(monkeypatch):
    sequence = iter(["20261116_AAA", "20261116_AAB"])
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.assistant_id.generate_assistant_id",
        lambda: next(sequence),
    )
    taken = {"20261116_AAA"}
    assert generate_unique_assistant_id(taken.__contains__) == "20261116_AAB"


def test_unique_generator_fails_when_space_exhausted(monkeypatch):
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.assistant_id.generate_assistant_id",
        lambda: "20261116_AAA",
    )
    with pytest.raises(RuntimeError, match="已耗尽"):
        generate_unique_assistant_id(lambda _candidate: True)
