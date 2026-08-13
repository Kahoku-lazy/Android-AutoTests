"""Auth serializers — login / register / refresh input validation."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=False,
    )
    password = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        if not username and not password:
            raise serializers.ValidationError("请输入用户名和密码")
        if not username:
            raise serializers.ValidationError("请输入用户名")
        if not password:
            raise serializers.ValidationError("请输入密码")
        if not str(username).strip():
            raise serializers.ValidationError("用户名不能为空白")
        if len(str(username)) > 150:
            raise serializers.ValidationError("用户名过长，最多150个字符")

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("用户名或密码错误")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(required=False, allow_blank=True, default="")
    password2 = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        username = str(attrs.get("username", "")).strip()
        password = str(attrs.get("password", "")).strip()
        password2 = str(attrs.get("password2", "")).strip()
        email = str(attrs.get("email", "")).strip()

        if not username and not password:
            raise serializers.ValidationError("请输入用户名和密码")
        if not username:
            raise serializers.ValidationError("请输入用户名")
        if not password:
            raise serializers.ValidationError("请输入密码")
        if len(username) < 3:
            raise serializers.ValidationError("用户名至少 3 个字符")
        if len(username) > 20:
            raise serializers.ValidationError("用户名最多 20 个字符")
        if len(password) < 6:
            raise serializers.ValidationError("密码至少 6 位")
        if password != password2:
            raise serializers.ValidationError("两次密码不一致")
        if not email:
            raise serializers.ValidationError("请输入邮箱")
        if "@" not in email:
            raise serializers.ValidationError("邮箱格式不正确")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("用户名已存在")

        attrs["username"] = username
        attrs["password"] = password
        attrs["email"] = email
        return attrs


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True, default="")
