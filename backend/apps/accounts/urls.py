"""
认证接口路径，挂在 /api/auth/ 下：登录、注册、续期、登出、当前用户。路径都带尾斜杠。
"""

from django.urls import path

from .views import LoginView, LogoutView, MeView, RefreshView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
