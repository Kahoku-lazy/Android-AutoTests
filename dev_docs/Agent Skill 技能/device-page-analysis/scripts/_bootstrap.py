"""本 skill 脚本共用：定位项目根 + 初始化 Django（幂等）。"""

import os
import sys
from pathlib import Path

_SETUP_DONE = False


def project_root(start=None) -> Path:
    """向上查找项目根：同时含 manage.py 与 config/settings.py 的目录。"""
    here = Path(start or __file__).resolve()
    for cand in [here] + list(here.parents):
        if (cand / "manage.py").is_file() and (cand / "config" / "settings.py").is_file():
            return cand
    raise SystemExit("找不到项目根（需要含 manage.py 与 config/settings.py 的目录）")


def setup_django() -> Path:
    global _SETUP_DONE
    root = project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if not _SETUP_DONE:
        import django

        django.setup()
        _SETUP_DONE = True
    return root


def default_workdir() -> Path:
    """临时产物根目录：项目根下的 temps/（项目约定的临时目录）。"""
    d = project_root() / "temps"
    d.mkdir(parents=True, exist_ok=True)
    return d
