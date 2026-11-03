"""
文件名: ➡️ realtime_model.py 🏁
路径: ➡️ engines/agents/models/realtime_model.py 🏁
模块功能：➡️ Omni 实时语音模型：全仓唯一的构造实现，角色与会话共用 🏁
Python 调试：➡️ python -m engines.agents.models.realtime_model 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. build_realtime_model: 按密钥 / 模型名 / 音色 / 可选 Parameters 造 DashScopeRealtimeModel
2. _import_dashscope_realtime: 延迟导入框架实时模型，缺额外依赖时给出安装提示
3. 角色装配与会话路径都走这里，不再各写一套 Omni 构造
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_realtime_vocie_models.py: 会话路径经门面建 Omni 模型
2. tests/engines/agents/test_agents.py: Omni 角色装配连通性
🏁
"""

from __future__ import annotations

from typing import Any

from agentscope.credential import DashScopeCredential

__all__ = ["build_realtime_model"]


def _import_dashscope_realtime():
    """延迟导入 agentscope realtime；缺额外依赖时给出安装提示。

    Returns:
        `agentscope.realtime.DashScopeRealtimeModel` 类。

    Raises:
        RuntimeError: 未安装 `agentscope[realtime]`。
    """
    try:
        from agentscope.realtime import DashScopeRealtimeModel
    except ImportError as exc:
        raise RuntimeError(
            '创建实时语音模型需要 agentscope realtime 额外依赖：pip install "agentscope[realtime]"'
        ) from exc
    return DashScopeRealtimeModel


def build_realtime_model(
    *,
    api_key: str,
    model_name: str,
    base_url: str = "",
    voice: str | None = None,
    parameters: Any = None,
    **parameter_kwargs: Any,
):
    """造一个 DashScope Omni 实时语音模型。

    Args:
        api_key: DashScope 密钥。
        model_name: 实时模型名，如 qwen3.5-omni-plus-realtime。
        base_url: 可选；空则交给框架默认地址。
        voice: 音色名；None 时用框架默认音色。
        parameters: 已构造好的框架 Parameters；与关键字参数互斥。
        parameter_kwargs: 直接传给框架 Parameters 的关键字（如 turn_detection / vad_threshold）。

    Returns:
        `DashScopeRealtimeModel` 实例。

    Raises:
        RuntimeError: 未安装 `agentscope[realtime]`。
        TypeError: `parameters` 与关键字参数同时传入。
        ValueError: 模型名或音色不被框架接受。
    """
    DashScopeRealtimeModel = _import_dashscope_realtime()
    if parameters is not None and (parameter_kwargs or voice is not None):
        raise TypeError("build_realtime_model 不能同时传 parameters 与关键字参数")
    if base_url:
        credential = DashScopeCredential(api_key=api_key, base_url=base_url)
    else:
        credential = DashScopeCredential(api_key=api_key)
    params = parameters
    if params is None:
        kwargs = dict(parameter_kwargs)
        if voice is not None:
            kwargs["voice"] = voice
        params = DashScopeRealtimeModel.Parameters(**kwargs)
    return DashScopeRealtimeModel(
        model=model_name,
        credential=credential,
        parameters=params,
    )
