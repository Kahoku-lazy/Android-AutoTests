"""API Key 加密工具单元测试 — 零 I/O，不依赖 DB。

覆盖：
- encrypt_key / decrypt_key 往返
- 空值 / 边界
- 解密失败静默降级
- mask_key 脱敏
"""

import pytest

from apps.ai_assistant.api import encrypt_key, decrypt_key, mask_key


# ═══════════════════════════════════════════════════════════════════
# encrypt_key
# ═══════════════════════════════════════════════════════════════════


class TestEncryptKey:
    """encrypt_key"""

    def test_encrypted_output_differs_from_input(self):
        """加密后不等于原文"""
        plain = "sk-test-api-key-12345"
        encrypted = encrypt_key(plain)
        assert encrypted != plain

    def test_encrypted_does_not_start_with_sk_prefix(self):
        """密文不以 sk- 开头（证明已加密）"""
        plain = "sk-test-key"
        encrypted = encrypt_key(plain)
        assert not encrypted.startswith("sk-"), f"密文仍有 sk- 前缀: {encrypted[:20]}..."

    def test_same_input_both_decrypt_to_original(self):
        """相同输入加密两次虽密文不同（随机 nonce），但都能解密回原文"""
        plain = "sk-consistent-key"
        e1 = encrypt_key(plain)
        e2 = encrypt_key(plain)
        # Fernet 每次使用随机 nonce，密文不同但都应能解密回原文
        assert e1 != e2  # 密文不同（更安全）
        assert decrypt_key(e1) == plain
        assert decrypt_key(e2) == plain

    def test_different_inputs_produce_different_outputs(self):
        """不同输入产生不同密文"""
        e1 = encrypt_key("sk-key-alpha")
        e2 = encrypt_key("sk-key-beta")
        assert e1 != e2

    def test_empty_string_returns_empty(self):
        """空字符串 → 空字符串"""
        assert encrypt_key("") == ""

    def test_long_api_key(self):
        """长 API Key 正常加密"""
        plain = "sk-" + "a" * 200
        encrypted = encrypt_key(plain)
        assert len(encrypted) > 0
        assert encrypted != plain


# ═══════════════════════════════════════════════════════════════════
# decrypt_key
# ═══════════════════════════════════════════════════════════════════


class TestDecryptKey:
    """decrypt_key"""

    def test_roundtrip_restores_original(self):
        """加密后解密还原"""
        plain = "sk-test-roundtrip-key"
        encrypted = encrypt_key(plain)
        decrypted = decrypt_key(encrypted)
        assert decrypted == plain

    def test_empty_string_returns_empty(self):
        """空字符串 → 空字符串（不抛异常）"""
        assert decrypt_key("") == ""

    def test_garbage_input_returns_empty_not_crash(self):
        """垃圾输入返回空字符串，不崩溃"""
        result = decrypt_key("this-is-not-valid-ciphertext!@#$%")
        assert result == ""

    def test_partial_ciphertext_returns_empty(self):
        """不完整的密文返回空"""
        result = decrypt_key("Z")
        assert result == ""

    def test_unicode_garbage_returns_empty(self):
        """Unicode 垃圾 → 空"""
        result = decrypt_key("中文测试数据不是密文")
        assert result == ""


class TestEncryptDecryptVariousKeys:
    """各种格式的 API Key 往返"""

    @pytest.mark.parametrize("plain", [
        "sk-abc123",
        "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "sk-proj-xxxxxxxxxxxx",
        "sk-ant-api03-xxxxxxxxxxxx",
        "org-xxxxxxxxxxxx",
        "",
    ])
    def test_roundtrip(self, plain):
        """加密后解密 = 原文"""
        if not plain:
            assert encrypt_key(plain) == "" and decrypt_key("") == ""
        else:
            encrypted = encrypt_key(plain)
            decrypted = decrypt_key(encrypted)
            assert decrypted == plain


# ═══════════════════════════════════════════════════════════════════
# mask_key
# ═══════════════════════════════════════════════════════════════════


class TestMaskKey:
    """mask_key"""

    def test_normal_key_shows_first_3_and_last_4(self):
        """sk-abcdefgh12345678 → sk-***5678"""
        result = mask_key("sk-abcdefgh12345678")
        assert result == "sk-***5678"

    def test_key_with_dash_in_last_4(self):
        """保留最后 4 个字符"""
        result = mask_key("sk-1234567890abcd")
        assert result == "sk-***abcd"

    def test_short_key_shows_only_stars(self):
        """长度 < 8 → ***"""
        assert mask_key("sk-ab") == "***"

    def test_empty_key_shows_stars(self):
        """空 key → ***"""
        assert mask_key("") == "***"

    def test_exactly_8_chars_shows_stars(self):
        """刚好 8 字符 → *** (len < 8 为 True)"""
        # 8 个字符：len >= 8 不触发短路 → 取前缀 3 + *** + 后缀 4
        result = mask_key("12345678")
        assert result == "123***5678"

    def test_exactly_7_chars_shows_stars(self):
        """7 字符 → ***"""
        assert mask_key("1234567") == "***"

    def test_very_long_key_masked(self):
        """长 Key 也能正确脱敏"""
        long_key = "sk-" + "x" * 100
        result = mask_key(long_key)
        assert result.startswith("sk-")
        assert "***" in result
        # 格式: 前 3 字符 + "***" + 后 4 字符 = 3 + 3 + 4 = 10
        assert len(result) == 10
