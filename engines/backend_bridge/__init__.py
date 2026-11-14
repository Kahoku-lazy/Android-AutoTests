"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/__init__.py 🏁
模块功能：➡️ 平台侧智能体角色的唯一落点：库形态的装配、运行与报告产出 🏁
Python 调试：➡️ python -m engines.backend_bridge 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本包只服务平台：后端任务与前端卡片使用的智能体角色在这里创建与运行。
2. 控制台调试入口在 engines/ae_harness/assistant/，本包不复用、不调用。
3. 只共享 ae_harness 的原语：create_agent、设备工具、事件记录器、报告渲染器、观测中间件。
4. 不引 Django、不写数据库、不打印、不读命令行；结果通过返回值交给调用方。
🏁
关联模块：➡️
1. engines.ae_harness.agents: 导入 create_agent，装配平台角色。
2. engines.ae_harness.tools: 导入设备工具，挂到执行角色上。
3. engines.ae_harness.event: 导入记录器、渲染器与用量汇总。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/: 路径、角色装配、导入守卫
🏁
"""

from __future__ import annotations
