"""
模块功能：➡️ `.env` 加载 — D0 单一实现（`config.settings` 与 `run.py` 共用） 🏁
Python 调试：➡️ python -m backend.config.env 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_env_loader.py: 覆盖本模块
🏁
"""

import os

from pathlib import Path

# 仓库根目录（backend/config/env.py → backend/config → backend → 根）
ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(env_file: Path | None = None) -> None:
    """把 `.env` 的键值注入 `os.environ`（已存在的键不覆盖）。"""
    path = env_file or ROOT / ".env"
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
