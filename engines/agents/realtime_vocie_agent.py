"""
文件名: ➡️ realtime_vocie_agent.py 🏁
路径: ➡️ engines/agents/realtime_vocie_agent.py 🏁
模块功能：➡️ 语音演示的过渡入口 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie_agent 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.2.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本文件只再导出 realtime_vocie.demo，供尚未改导入路径的调用方使用。
🏁
关联模块：➡️
1. engines.agents.realtime_vocie.demo: 本地麦克风演示的实现。
🏁
测试：➡️
1. tests/engines/agents/unit/test_voice_workflow_exit.py: 旧路径与新路径导出同一函数
🏁
"""

from engines.agents.realtime_vocie.demo import build_realtime_vocie_agent, main, run_local_s2s

__all__ = ["build_realtime_vocie_agent", "main", "run_local_s2s"]


if __name__ == "__main__":
    main()
