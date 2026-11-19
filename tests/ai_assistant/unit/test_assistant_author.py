"""助手作者授权：授予、收回、重复授予，以及四类身份判定。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.apps.accounts.api import set_user_active
from backend.apps.ai_assistant.api import (
    grant_assistant_author,
    has_assistant_author_grant,
    revoke_assistant_author,
)
from backend.apps.ai_assistant.models import AssistantAuthorGrant
from backend.shared.users import OPERATOR_GROUP, is_assistant_author, is_operator

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _user(name: str, *, superuser: bool = False):
    return get_user_model().objects.create_user(
        username=name,
        password="pass",
        is_superuser=superuser,
    )


def test_grant_revoke_and_repeat_grant():
    user = _user("author-target")

    first = grant_assistant_author(user.id)
    second = grant_assistant_author(user.id)

    assert first.pk == second.pk
    assert AssistantAuthorGrant.objects.filter(user_id=user.id).count() == 1
    assert has_assistant_author_grant(user.id) is True

    assert revoke_assistant_author(user.id) is True
    assert has_assistant_author_grant(user.id) is False
    assert revoke_assistant_author(user.id) is False


def test_author_check_covers_four_identities():
    superuser = _user("author-root", superuser=True)
    author = _user("author-granted")
    operator = _user("author-operator")
    plain = _user("author-plain")
    operator.groups.add(Group.objects.create(name=OPERATOR_GROUP))
    grant_assistant_author(author.id)

    assert is_assistant_author(superuser.id) is True
    assert is_assistant_author(author.id) is True
    assert is_assistant_author(operator.id) is False
    assert is_assistant_author(plain.id) is False
    assert is_operator(operator.id) is True
    assert is_operator(superuser.id) is True


def test_disabling_account_removes_author_grant():
    author = _user("author-disabled")
    grant_assistant_author(author.id)

    set_user_active(author.id, False)
    set_user_active(author.id, True)

    assert has_assistant_author_grant(author.id) is False
    assert is_assistant_author(author.id) is False
