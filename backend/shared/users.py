import logging

logger = logging.getLogger(__name__)


def resolve_username(user_id):
    if not user_id:
        return ""
    s = str(user_id)
    if not s.isdigit():
        return s
    try:
        from django.contrib.auth.models import User

        return User.objects.get(id=int(s)).username
    except Exception:
        return s


def is_superuser(user_id) -> bool:
    if not user_id:
        return False
    try:
        from django.contrib.auth import get_user_model

        return get_user_model().objects.filter(pk=int(str(user_id)), is_superuser=True).exists()
    except (ValueError, TypeError):
        return False


OPERATOR_GROUP = "运营"


def is_assistant_author(user_id) -> bool:
    if is_superuser(user_id):
        return True
    if not user_id:
        return False
    try:
        from backend.apps.ai_assistant.api import has_assistant_author_grant

        return has_assistant_author_grant(int(str(user_id)))
    except (ValueError, TypeError):
        return False


def is_operator(user_id) -> bool:
    if not user_id:
        return False
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Q

        return (
            get_user_model()
            .objects.filter(pk=int(str(user_id)))
            .filter(Q(is_superuser=True) | Q(groups__name=OPERATOR_GROUP))
            .exists()
        )
    except (ValueError, TypeError):
        return False
