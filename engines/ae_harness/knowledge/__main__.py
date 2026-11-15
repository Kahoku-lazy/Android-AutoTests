"""
文件名: ➡️ __main__.py 🏁
路径: ➡️ engines/ae_harness/knowledge/__main__.py 🏁
模块功能：➡️ 知识库探针命令入口 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge index product_manuals 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. 把 python -m engines.ae_harness.knowledge 交给 probe.main。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.probe: 导入 main。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_probe.py: 命令行退出码
🏁
"""

from __future__ import annotations

import sys

from .probe import main

if __name__ == "__main__":
    sys.exit(main())
