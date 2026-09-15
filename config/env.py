"""`.env` 加载 — D0 单一实现（`config.settings` 与 `run.py` 共用）。

规则（与既有实现保持一致）：

- 只处理 `KEY=VALUE` 行；空行与 `#` 注释跳过；
- 值两侧的引号（成对 `"` 或 `'`）会被去掉；
- **已存在的环境变量优先**：真实环境变量不会被 `.env` 覆盖（先到先得）。
"""

import os

from pathlib import Path

# 仓库根目录（config/env.py → config/ → 根）
ROOT = Path(__file__).resolve().parent.parent


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
