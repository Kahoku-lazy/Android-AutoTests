"""运营后台接口测试的视图直调助手。"""

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
    """用请求工厂直调视图：模拟网关注入 user_id，并让 DRF 鉴权通过。

    Args:
        view_cls: 目标视图类。
        method: HTTP 方法名。
        path: 完整路径；查询参数直接拼在路径里。
        user: 已登录账号；None 表示未登录。
        data: 请求体。
        **url_kwargs: 路径里的 `<int:user_id>` 等参数。

    Returns:
        DRF Response。
    """
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **url_kwargs)
