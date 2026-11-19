"""
文件名: ➡️ creator.py 🏁
路径: ➡️ engines/ae_harness/agents/creator.py 🏁
模块功能：➡️ 输出一个智能体角色：模型 + 系统提示词 + 角色名称，并交出用的是哪把密钥 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.creator 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 5.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. AgentBundle: 创建出口的返回值，打包可运行智能体与本次使用的密钥环境变量名。
2. create_agent: 按角色名称、调用方传入的提示词正文与连接参数装配，产出 AgentBundle。
3. 内部只转调 models 造模型；密钥名由 models 顺带交出，本模块不读密钥、不读提示词文件。
4. 只创建不回复；工具不属于角色三要素，由调用方拿到智能体后自行挂载。
🏁
关联模块：➡️
1. engines.ae_harness.agents.models: 造聊天模型，并交出密钥环境变量名。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_creator.py: 两段返回、密钥名透传、未知短名报错
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.agent import Agent

from .models import create_model

__all__ = ["AgentBundle", "create_agent"]


@dataclass(frozen=True)
class AgentBundle:
    """
    创建出口的返回值。

    智能体与「用的是哪把密钥」一起交出，调用方不必再读配置表就能给用量记账。

    Attributes:
        agent: 已装配好的智能体，工具包为空。
        api_key_env: 本次使用的密钥所在的环境变量名；只有名字，没有值。
    """

    agent: Agent
    api_key_env: str


def create_agent(
    name: str,
    system_prompt: str,
    *,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    stream: bool = True,
    observers: list | None = None,
) -> AgentBundle:
    """
    输出一个智能体角色：模型 + 系统提示词 + 角色名称，并附带密钥环境变量名。

    只创建，不调用回复接口；工具由调用方拿到智能体后自行挂载。

    Args:
        name: 角色名称，出现在消息里。
        system_prompt: 系统提示词正文。
        provider: 厂商名，交给 models 决定用哪个客户端。
        api_key_env: 密钥环境变量名，交给 models 自己解析。
        model_name: 厂商正式模型名。
        base_url: 基础地址；空串时由 models 用厂商默认。
        stream: 是否流式输出。
        observers: 只读观测中间件；仅透传给智能体，本模块不认识其实现。

    Returns:
        智能体与密钥环境变量名打包好的 bundle，智能体的工具包为空。

    Raises:
        ValueError: 厂商与密钥名不匹配，密钥没配，或系统提示词为空。
        ValidationError: 连接参数校验不通过。
    """
    if not provider or not api_key_env or not model_name:
        raise ValueError("新建 Agent 必须传入 provider、api_key_env、model_name")
    text = system_prompt.strip()
    if not text:
        raise ValueError("system_prompt 不能为空")
    created = create_model(provider, api_key_env, model_name, base_url, stream=stream)
    return AgentBundle(
        agent=Agent(
            name=name,
            system_prompt=text,
            model=created.model,
            middlewares=list(observers or []),
        ),
        api_key_env=created.api_key_env,
    )


if __name__ == "__main__":
    print(  # noqa: T201
        create_agent(
            "probe",
            "你是探针。",
            provider="openai",
            api_key_env="OPENAI_API_KEY",
            model_name="deepseek-flash",
        ).api_key_env
    )
