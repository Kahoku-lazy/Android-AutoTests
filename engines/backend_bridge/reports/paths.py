"""
文件名: ➡️ paths.py 🏁
路径: ➡️ engines/backend_bridge/reports/paths.py 🏁
模块功能：➡️ 平台报告根目录的唯一来源 🏁
Python 调试：➡️ python -m engines.backend_bridge.reports.paths 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. REPORT_ROOT: 平台报告根目录，全仓唯一来源；其它模块只接收 Path，不拼字符串。
2. 本次运行的子目录由事件记录器按时间戳创建，本模块不重复建一层。
🏁
关联模块：➡️
1. 无本地依赖：只依赖标准库 pathlib。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_paths.py: 根目录末三级与绝对路径
🏁
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["REPORT_ROOT"]

# engines/backend_bridge/reports/paths.py 往上三级是仓库根。
_REPO_ROOT = Path(__file__).resolve().parents[3]

# 平台报告根：与 ae_harness 自己的 logs/ 分开，避免两条链路的产物混在一起。
REPORT_ROOT = _REPO_ROOT / "logs" / "agents" / "backend_bridge"


if __name__ == "__main__":
    print(REPORT_ROOT)  # noqa: T201 - 模块自测入口
