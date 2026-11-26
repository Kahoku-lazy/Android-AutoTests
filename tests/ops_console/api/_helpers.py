from __future__ import annotations

from rest_framework.test import APIRequestFactory, force_authenticate


def call(
    view_cls,
    *,
    method: str = "get",
    path: str = "/api/ops/users/",
    user=None,
    data=None,
    **url_kwargs,
):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **url_kwargs)
