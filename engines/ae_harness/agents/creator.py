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
2. create_agent: 按角色名称、模型短名与提示词文件名装配，产出 AgentBundle。
3. 内部只转调 config 读提示词、models 造模型；密钥名由 models 顺带交出，本模块不读配置表。
4. 只创建不回复；工具不属于角色三要素，由调用方拿到智能体后自行挂载。
🏁
关联模块：➡️
1. engines.ae_harness.agents.config: 读提示词正文。
2. engines.ae_harness.agents.models: 造聊天模型，并交出密钥环境变量名。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_creator.py: 两段返回、密钥名透传、未知短名报错
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.agent import Agent

from .config import load_prompt
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
    prompt: str,
    model_short: str,
    *,
    catalog: dict | None = None,
    stream: bool = True,
    observers: list | None = None,
) -> AgentBundle:
    """
    输出一个智能体角色：模型 + 系统提示词 + 角色名称，并附带密钥环境变量名。

    只创建，不调用回复接口；工具由调用方拿到智能体后自行挂载。

    Args:
        name: 角色名称，出现在消息里。
        prompt: 提示词文件名，不带 .md，由 config 读成正文。
        model_short: 模型短名，由 models 造出实例并交出密钥名。
        catalog: 模型表；不传则交给 create_model 现读。
        stream: 是否流式输出。
        observers: 只读观测中间件；仅透传给智能体，本模块不认识其实现。

    Returns:
        智能体与密钥环境变量名打包好的 bundle，智能体的工具包为空。

    Raises:
        ValueError: 模型短名不存在或密钥没配。
        ValidationError: 模型配置校验不通过。
        FileNotFoundError: 提示词文件不存在。
    """
    created = create_model(model_short, catalog=catalog, stream=stream)
    return AgentBundle(
        agent=Agent(
            name=name,
            system_prompt=load_prompt(prompt),
            model=created.model,
            middlewares=list(observers or []),
        ),
        api_key_env=created.api_key_env,
    )


if __name__ == "__main__":
    print(create_agent("probe", "UI_EXECUTOR_PROMPT", "govee_chat_flash").api_key_env)  # noqa: T201
