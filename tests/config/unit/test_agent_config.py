"""config 包：密钥加解密、配置文件读取与返回结构。

只测两件事（按约定的颗粒度）：
1. api_key 加密 / 解密与打码；
2. 两份配置文件能读出来，且返回结构符合既定格式。

不测模型创建、不测角色装配——那是 models / agent 的测试范围。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.agents.config.config import (
    AGENT_CONFIG_PATH,
    CONFIG_INI_PATH,
    MODEL_CONFIG_PATH,
    SecretKey,
    _decrypt,
    _encrypt,
    ini_io,
    load_agent_config,
    load_model_config,
)

pytestmark = [pytest.mark.unit]

_ROLE_KEYS = {
    "UI_EXECUTOR_ROLE_CONFIG",
    "UI_VERIFIER_ROLE_CONFIG",
    "CASE_WRITER_ROLE_CONFIG",
    "CASE_VERIFIER_ROLE_CONFIG",
    "OMNI_ROLE_CONFIG",
    "KNOWLEDGE_CHAT_ROLE_CONFIG",
}

_MODEL_KEYS = {
    "deepseek_flash",
    "deepseek_pro",
    "qwen_plus",
    "omni",
    "text_embedding_v4",
    "qwen3_tts",
}

_FAMILIES = {"chat", "realtime", "embedding", "tts"}
_PROVIDERS = {"deepseek", "dashscope"}
_KEY_ENVS = {"DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY"}


# ── 一、密钥加解密 ──────────────────────────────────────────


def test_encrypt_decrypt_round_trip():
    """明文加密后能还原成原文。"""
    plain = "sk-live-0123456789abcdef"

    token = _encrypt(plain)

    assert _decrypt(token) == plain


def test_ciphertext_does_not_leak_plaintext():
    """密文与明文不同，且不含明文片段。"""
    plain = "sk-secret-value-abcdef"

    token = _encrypt(plain)

    assert token != plain
    assert plain not in token
    assert plain[:8] not in token


def test_same_plaintext_encrypts_differently():
    """同一明文两次加密结果不同（随机 IV），但都能解回原文。"""
    plain = "sk-same-value"

    first = _encrypt(plain)
    second = _encrypt(plain)

    assert first != second
    assert _decrypt(first) == _decrypt(second) == plain


def test_round_trip_handles_unicode_and_long_key():
    """中文、符号与超长密钥都能原样往返。"""
    for plain in ("密钥-中文-🔑", "a" * 512, "sk-" + "x" * 64):
        assert _decrypt(_encrypt(plain)) == plain


def test_decrypt_rejects_foreign_token():
    """不是本进程加密出来的密文会报错，而不是返回垃圾。"""
    with pytest.raises(ValueError, match="密钥密文非法"):
        _decrypt("not-a-valid-token")


def test_secret_key_reveal_returns_plaintext():
    """SecretKey.reveal() 取回明文。"""
    key = SecretKey(_encrypt("sk-reveal-me"), env_name="DEEPSEEK_API_KEY")

    assert key.reveal() == "sk-reveal-me"


def test_secret_key_masks_in_repr_and_str():
    """repr / str / f-string 都不出现明文。"""
    plain = "sk-never-print-me"
    key = SecretKey(_encrypt(plain), env_name="DEEPSEEK_API_KEY")

    for text in (repr(key), str(key), f"{key}"):
        assert plain not in text
        assert "****" in text


def test_secret_key_without_token_is_falsy_and_raises_on_reveal():
    """没配到密钥时是假值，reveal() 才报错并点出环境变量名。"""
    key = SecretKey(None, env_name="DEEPSEEK_API_KEY")

    assert bool(key) is False
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        key.reveal()


def test_secret_key_requires_token_or_env_name():
    """密文与环境变量名不能同时为空。"""
    with pytest.raises(ValueError, match="不能同时为空"):
        SecretKey(None, env_name="")


# ── 二、配置文件读取与返回结构 ──────────────────────────────


def test_paths_come_from_config_ini():
    """路径只有一个来源：config.ini。"""
    assert CONFIG_INI_PATH == "engines/agents/config/config.ini"
    assert AGENT_CONFIG_PATH == ini_io.get(
        CONFIG_INI_PATH, "agent_config", "agent_config_file_path"
    )
    assert MODEL_CONFIG_PATH == ini_io.get(
        CONFIG_INI_PATH, "model_config", "model_config_file_path"
    )
    assert Path(AGENT_CONFIG_PATH).is_file()
    assert Path(MODEL_CONFIG_PATH).is_file()


def test_agent_config_returns_role_mapping():
    """角色配置返回「角色键 → 节」，六个已知角色齐全。"""
    config = load_agent_config()

    assert isinstance(config, dict)
    assert _ROLE_KEYS <= set(config)
    assert all(isinstance(section, dict) for section in config.values())


def test_agent_config_sections_have_model_and_role():
    """每个角色节都带可用的 ModelConfig 与 RoleConfig。"""
    config = load_agent_config()

    for name, section in config.items():
        assert "ModelConfig" in section, f"{name} 缺 ModelConfig"
        assert "RoleConfig" in section, f"{name} 缺 RoleConfig"

        model = section["ModelConfig"]
        assert isinstance(model["model"], str) and model["model"].strip()
        if "stream" in model:
            assert isinstance(model["stream"], bool)

        role = section["RoleConfig"]
        assert isinstance(role["name"], str) and role["name"].strip()
        assert isinstance(role["system_prompt"], str) and role["system_prompt"].strip()


def test_model_config_returns_six_models():
    """模型表返回六个短名，四族齐全。"""
    catalog = load_model_config()

    assert isinstance(catalog, dict)
    assert set(catalog) == _MODEL_KEYS
    assert {entry["family"] for entry in catalog.values()} == _FAMILIES


def test_model_config_entries_have_required_fields():
    """每条条目都带合法 family / provider / model_name / api_key_env。"""
    catalog = load_model_config()

    for name, entry in catalog.items():
        assert entry["family"] in _FAMILIES, f"{name}.family 非法"
        assert entry["provider"] in _PROVIDERS, f"{name}.provider 非法"
        assert isinstance(entry["model_name"], str) and entry["model_name"].strip()
        assert entry["api_key_env"] in _KEY_ENVS, f"{name}.api_key_env 非法"


def test_model_config_injects_secret_key():
    """每条条目都被注入 SecretKey，而不是明文。"""
    catalog = load_model_config()

    for name, entry in catalog.items():
        assert isinstance(entry["api_key"], SecretKey), f"{name}.api_key 不是 SecretKey"


def test_model_config_never_returns_plaintext(monkeypatch):
    """环境变量里的明文不会出现在返回数据里。"""
    sentinel = "sk-sentinel-must-not-leak"
    monkeypatch.setenv("DEEPSEEK_API_KEY", sentinel)
    monkeypatch.setenv("DASHSCOPE_API_KEY", sentinel)

    catalog = load_model_config()

    assert sentinel not in repr(catalog)
    assert catalog["deepseek_flash"]["api_key"].reveal() == sentinel


def test_model_config_tolerates_missing_key(monkeypatch):
    """缺环境变量不阻断装载：照常返回六条，密钥对象为假值。"""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    catalog = load_model_config()

    assert len(catalog) == len(_MODEL_KEYS)
    assert bool(catalog["deepseek_flash"]["api_key"]) is False
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        catalog["deepseek_flash"]["api_key"].reveal()


def test_model_config_reads_explicit_path(tmp_path, monkeypatch):
    """显式路径优先于 config.ini，且同样注入 SecretKey。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-temp")
    path = tmp_path / "models.yaml"
    path.write_text(
        "probe:\n"
        "  family: chat\n"
        "  provider: deepseek\n"
        "  model_name: deepseek-flash\n"
        "  api_key_env: DEEPSEEK_API_KEY\n",
        encoding="utf-8",
    )

    catalog = load_model_config(path)

    assert list(catalog) == ["probe"]
    assert isinstance(catalog["probe"]["api_key"], SecretKey)
    assert catalog["probe"]["api_key"].reveal() == "sk-temp"


def test_model_config_rejects_non_mapping_top_level(tmp_path):
    """顶层不是映射表时报错。"""
    path = tmp_path / "models.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(ValueError, match="顶层必须是映射表"):
        load_model_config(path)


def test_missing_config_file_raises():
    """路径不存在时抛 FileNotFoundError。"""
    missing = Path("engines/agents/config/data/not-exist.yaml")

    with pytest.raises(FileNotFoundError):
        load_agent_config(str(missing))
