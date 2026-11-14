"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/assistant/__init__.py 🏁
模块功能：➡️ 角色调试入口包：执行者与验收者的可运行脚本 🏁
Python 调试：➡️ python -m engines.ae_harness.assistant 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本包只放「某个角色的调试入口」：建角色、挂工具、跑一轮、出报告。
2. 角色的定义（模型 + 提示词 + 名称）在 agents/，不在这里。
3. 新增角色入口一律放本包，不要放回仓库根。
🏁
关联模块：➡️
1. engines.ae_harness.agents: 角色定义与创建。
2. engines.ae_harness.tools: 工具装配。
3. engines.ae_harness.event: 记录与渲染。
4. engines.ae_harness.assistant._bootstrap: 运行时骨架（本包内）。
🏁
测试：➡️
1. python -m engines.ae_harness.assistant.agent_executor "当前在哪个应用"
2. python -m engines.ae_harness.assistant.agent_verifier "屏幕上能看到「设置」"
🏁
"""
