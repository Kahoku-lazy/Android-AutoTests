"""JWT 核心库单元测试 — 零 I/O，不依赖 Redis / DB。

覆盖：
- Token 创建（access / refresh / pair）
- Token 验证（合法 / 过期 / 类型错误 / 篡改）
- 黑名单（加入 / 检查 / Redis 不可用行为）
- 配置（TTL / 生产环境强制 SECRET_KEY）
"""

import time
from unittest.mock import MagicMock, patch, Mock

import jwt as pyjwt
import pytest

from shared.auth.jwt_auth import (
    JWTConfig,
    BlacklistUnavailableError,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_token,
    get_user_id_from_token,
    blacklist_token,
    is_blacklisted,
    _blacklist_contains,
    _blacklist_add,
    _get_redis,
)


# ═══════════════════════════════════════════════════════════════════
# Token 创建
# ═══════════════════════════════════════════════════════════════════


class TestCreateAccessToken:
    """create_access_token"""

    def test_contains_required_claims(self):
        """payload 必须包含 sub / jti / iat / exp / type=access"""
        token = create_access_token("42")
        payload = decode_token(token)

        assert payload["sub"] == "42"
        assert payload["type"] == "access"
        assert isinstance(payload["jti"], str) and len(payload["jti"]) > 0
        assert isinstance(payload["iat"], int) and payload["iat"] > 0
        assert isinstance(payload["exp"], int) and payload["exp"] > payload["iat"]

    def test_different_user_ids_produce_different_tokens(self):
        """不同用户 不同 token"""
        t1 = create_access_token("1")
        t2 = create_access_token("2")
        assert t1 != t2

    def test_same_user_produces_different_jti(self):
        """同一用户两次调用 jti 不同"""
        t1 = create_access_token("42")
        t2 = create_access_token("42")
        assert decode_token(t1)["jti"] != decode_token(t2)["jti"]

    def test_extra_claims_merged_into_payload(self):
        """extra 参数合并到 payload"""
        token = create_access_token("42", extra={"role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"


class TestCreateRefreshToken:
    """create_refresh_token"""

    def test_type_is_refresh(self):
        """refresh token 的 type 声明是 refresh"""
        token = create_refresh_token("42")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_longer_ttl_than_access(self):
        """refresh token 有效期比 access token 长"""
        cfg = JWTConfig()
        access_token = create_access_token("42")
        refresh_token = create_refresh_token("42")

        access_exp = decode_token(access_token)["exp"]
        refresh_exp = decode_token(refresh_token)["exp"]

        # refresh TTL >= access TTL
        assert refresh_exp >= access_exp


class TestCreateTokenPair:
    """create_token_pair"""

    def test_returns_both_tokens_and_bearer_type(self):
        """返回 access_token + refresh_token + token_type=bearer"""
        result = create_token_pair("42")

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["access_token"] != result["refresh_token"]

    def test_both_tokens_refer_to_same_user(self):
        """两个 token 的 sub 相同"""
        result = create_token_pair("42")
        access_payload = decode_token(result["access_token"])
        refresh_payload = decode_token(result["refresh_token"])
        assert access_payload["sub"] == "42"
        assert refresh_payload["sub"] == "42"


# ═══════════════════════════════════════════════════════════════════
# Token 验证
# ═══════════════════════════════════════════════════════════════════


class TestVerifyTokenSuccess:
    """验证成功"""

    def test_valid_access_token_passes(self):
        """合法 access token 验证通过"""
        token = create_access_token("42")
        payload = verify_token(token, expected_type="access")
        assert payload["sub"] == "42"

    def test_valid_refresh_token_passes(self):
        """合法 refresh token 验证通过"""
        token = create_refresh_token("42")
        payload = verify_token(token, expected_type="refresh")
        assert payload["sub"] == "42"

    def test_without_expected_type_any_token_passes(self):
        """不传 expected_type 时不验证类型"""
        access = create_access_token("42")
        refresh = create_refresh_token("42")
        assert verify_token(access)["type"] == "access"
        assert verify_token(refresh)["type"] == "refresh"


class TestVerifyTokenFailure:
    """验证失败"""

    def test_expired_token_raises(self):
        """过期 token → ExpiredSignatureError"""
        cfg = JWTConfig()
        now = int(time.time())
        payload = {
            "sub": "42", "jti": "expired-jti",
            "iat": now - 7200, "exp": now - 3600, "type": "access",
        }
        token = pyjwt.encode(payload, cfg.secret, algorithm=cfg.algorithm)

        with pytest.raises(pyjwt.ExpiredSignatureError):
            verify_token(token, expected_type="access")

    def test_tampered_token_raises(self):
        """篡改的 token → InvalidSignatureError"""
        token = create_access_token("42")
        tampered = token[:-1] + ("Q" if token[-1] != "Q" else "Z")

        with pytest.raises(pyjwt.InvalidSignatureError):
            verify_token(tampered, expected_type="access")

    def test_malformed_token_raises(self):
        """格式错误的 token → DecodeError"""
        with pytest.raises(pyjwt.DecodeError):
            verify_token("not.a.token.but.too.short", expected_type="access")

    def test_empty_token_raises(self):
        """空字符串 → DecodeError"""
        with pytest.raises(pyjwt.DecodeError):
            verify_token("", expected_type="access")

    def test_refresh_token_rejected_as_access(self):
        """refresh token 当 access 用 → InvalidTokenError + type mismatch"""
        token = create_refresh_token("42")

        with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token type"):
            verify_token(token, expected_type="access")

    def test_access_token_rejected_as_refresh(self):
        """access token 当 refresh 用 → InvalidTokenError"""
        token = create_access_token("42")

        with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token type"):
            verify_token(token, expected_type="refresh")


# ═══════════════════════════════════════════════════════════════════
# 黑名单
# ═══════════════════════════════════════════════════════════════════


class TestBlacklist:
    """黑名单操作（需要 mock Redis）"""

    @patch("shared.auth.jwt_auth._get_redis")
    def test_blacklisted_token_verification_fails(self, mock_get_redis):
        """已撤销的 token 验证失败 → InvalidTokenError + 'revoked'"""
        # 构造真实 token
        token = create_access_token("42")

        # mock Redis：exists 返回 True（表示在黑名单中）
        mock_client = MagicMock()
        mock_client.exists.return_value = True
        mock_get_redis.return_value = mock_client

        with pytest.raises(pyjwt.InvalidTokenError, match="revoked"):
            verify_token(token, expected_type="access")

    @patch("shared.auth.jwt_auth._get_redis")
    def test_blacklist_token_calls_setex_with_correct_ttl(self, mock_get_redis):
        """blacklist_token 以正确的 key 和 TTL 写入 Redis"""
        mock_client = MagicMock()
        mock_get_redis.return_value = mock_client

        token = create_access_token("42")
        blacklist_token(token)

        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        # key: jwt:blacklist:{jti}
        assert args[0].startswith("jwt:blacklist:")
        # value: "1"
        assert args[2] == "1"
        # TTL > 0
        assert args[1] > 0

    @patch("shared.auth.jwt_auth._get_redis")
    def test_blacklist_add_without_jti_is_noop(self, mock_get_redis):
        """jti 为空时不操作 Redis"""
        mock_client = MagicMock()
        mock_get_redis.return_value = mock_client

        _blacklist_add("", 3600)
        mock_client.setex.assert_not_called()

    @patch("shared.auth.jwt_auth._get_redis")
    def test_is_blacklisted_returns_true_when_in_blacklist(self, mock_get_redis):
        """jti 在黑名单中 → True"""
        mock_client = MagicMock()
        mock_client.exists.return_value = True
        mock_get_redis.return_value = mock_client

        token = create_access_token("42")
        assert is_blacklisted(token) is True

    @patch("shared.auth.jwt_auth._get_redis")
    def test_is_blacklisted_returns_false_when_not_in_blacklist(self, mock_get_redis):
        """jti 不在黑名单中 → False"""
        mock_client = MagicMock()
        mock_client.exists.return_value = False
        mock_get_redis.return_value = mock_client

        token = create_access_token("42")
        assert is_blacklisted(token) is False


class TestBlacklistRedisUnavailable:
    """Redis 不可用时的行为"""

    @patch("shared.auth.jwt_auth._get_redis")
    def test_logout_without_redis_raises_blacklist_unavailable(self, mock_get_redis):
        """登出时 Redis 不可用 → BlacklistUnavailableError"""
        mock_get_redis.return_value = None

        token = create_access_token("42")
        with pytest.raises(BlacklistUnavailableError):
            blacklist_token(token)

    @patch("shared.auth.jwt_auth._get_redis")
    def test_verify_when_redis_down_falls_back_to_pass(self, mock_get_redis):
        """验证 token 时 Redis 不可用 → 降级放行（不锁死所有用户）"""
        mock_get_redis.return_value = None

        token = create_access_token("42")
        payload = verify_token(token, expected_type="access")
        assert payload["sub"] == "42"

    @patch("shared.auth.jwt_auth._get_redis")
    def test_blacklist_contains_when_redis_down_returns_false(self, mock_get_redis):
        """检查黑名单时 Redis 不可用 → False（安全默认值）"""
        mock_get_redis.return_value = None
        assert _blacklist_contains("some-jti") is False


# ═══════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════


class TestJWTConfig:
    """JWTConfig 配置校验"""

    def test_default_ttls_are_positive(self):
        """默认 TTL 是正数"""
        cfg = JWTConfig()
        assert cfg.access_ttl > 0
        assert cfg.refresh_ttl > 0

    def test_refresh_ttl_longer_than_access(self):
        """refresh TTL > access TTL"""
        cfg = JWTConfig()
        assert cfg.refresh_ttl > cfg.access_ttl

    @patch("shared.auth.jwt_auth.settings", create=True)
    def test_production_empty_secret_key_raises(self, mock_settings):
        """生产环境 + 空 SECRET_KEY → RuntimeError"""
        mock_settings.DEBUG = False
        mock_settings.SECRET_KEY = ""
        mock_settings.JWT_ACCESS_TTL = 3600
        mock_settings.JWT_REFRESH_TTL = 604800

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            JWTConfig()


class TestGetUserIdFromToken:
    """get_user_id_from_token"""

    def test_returns_correct_user_id(self):
        """返回 payload.sub"""
        token = create_access_token("99")
        assert get_user_id_from_token(token) == "99"


class TestDecodeToken:
    """decode_token（不验证过期）"""

    def test_expired_token_still_decodeable(self):
        """即使过期也能解码（因为不验证过期）"""
        cfg = JWTConfig()
        now = int(time.time())
        payload_data = {
            "sub": "42", "jti": "x",
            "iat": now - 7200, "exp": now - 3600, "type": "access",
        }
        token = pyjwt.encode(payload_data, cfg.secret, algorithm=cfg.algorithm)

        decoded = decode_token(token)
        assert decoded["sub"] == "42"
        assert decoded["exp"] < now  # 确认已过期
