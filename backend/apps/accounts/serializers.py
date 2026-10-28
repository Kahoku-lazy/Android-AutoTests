"""
登录、注册、续期的入参校验。

业务：
1. 登录：账号必填且不能为空白、最长 150 字；密码必填。对不上则视为账号或密码错误。
2. 注册：账号 3–20 字，邮箱需含 @，密码至少 6 位，两次密码一致。用户名是否已占用不在这里判断。
3. 续期：接收续期凭证，是否有效由续期接口判断。
"""

from django.contrib.auth import authenticate
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

        # 唯一性不在此校验：它是数据不变量，由写口按数据库唯一约束保证（见 api.py）
        attrs["username"] = username
        attrs["password"] = password
        attrs["email"] = email
        return attrs


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True, default="")
