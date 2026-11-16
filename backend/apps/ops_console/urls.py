"""运营后台路由 — 挂在 /api/ops/ 下；全部端点路径带尾斜杠。"""

from django.urls import path

from .views import (
    OpsUserDisableView,
    OpsUserEnableView,
    OpsUserListView,
    OpsUserResetPasswordView,
)

app_name = "ops"

urlpatterns = [
    path("users/", OpsUserListView.as_view(), name="ops_user_list"),
    path(
        "users/<int:user_id>/disable/",
        OpsUserDisableView.as_view(),
        name="ops_user_disable",
    ),
    path(
        "users/<int:user_id>/enable/",
        OpsUserEnableView.as_view(),
        name="ops_user_enable",
    ),
    path(
        "users/<int:user_id>/reset-password/",
        OpsUserResetPasswordView.as_view(),
        name="ops_user_reset_password",
    ),
]
