from django.urls import path

from .views import (
    OpsUserBatchDisableView,
    OpsUserDisableView,
    OpsUserEnableView,
    OpsUserGrantAuthorView,
    OpsUserGrantOperatorView,
    OpsUserListView,
    OpsUserModelGrantView,
    OpsUserPurgeView,
    OpsUserResetPasswordView,
    OpsUserRevokeAuthorView,
    OpsUserRevokeOperatorView,
)

app_name = "ops"

urlpatterns = [
    path("users/", OpsUserListView.as_view(), name="ops_user_list"),
    path("users/disable/", OpsUserBatchDisableView.as_view(), name="ops_user_batch_disable"),
    path("users/purge/", OpsUserPurgeView.as_view(), name="ops_user_purge"),
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
        "users/<int:user_id>/model-grants/",
        OpsUserModelGrantView.as_view(),
        name="ops_user_model_grant",
    ),
    path(
        "users/<int:user_id>/grant-author/",
        OpsUserGrantAuthorView.as_view(),
        name="ops_user_grant_author",
    ),
    path(
        "users/<int:user_id>/revoke-author/",
        OpsUserRevokeAuthorView.as_view(),
        name="ops_user_revoke_author",
    ),
    path(
        "users/<int:user_id>/grant-operator/",
        OpsUserGrantOperatorView.as_view(),
        name="ops_user_grant_operator",
    ),
    path(
        "users/<int:user_id>/revoke-operator/",
        OpsUserRevokeOperatorView.as_view(),
        name="ops_user_revoke_operator",
    ),
    path(
        "users/<int:user_id>/reset-password/",
        OpsUserResetPasswordView.as_view(),
        name="ops_user_reset_password",
    ),
]
