"""
文件名: ➡️ __main__.py 🏁
路径: ➡️ engines/agents/rag/__main__.py 🏁
模块功能：➡️ 知识库探针命令入口 🏁
Python 调试：➡️ python -m engines.agents.rag 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. 把命令行参数交给 probe.main。
🏁
关联模块：➡️
1. engines.agents.rag.probe: 导入 main
🏁
测试：➡️
1. tests/engines/agents/unit/test_rag_probe.py: 命令行探针退出码
🏁
"""

from .probe import main

if __name__ == "__main__":
    raise SystemExit(main())
