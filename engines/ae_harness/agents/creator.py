from __future__ import annotations

from dataclasses import dataclass

from agentscope.agent import Agent

from .models import create_model

__all__ = ["AgentBundle", "create_agent"]


@dataclass(frozen=True)
class AgentBundle:
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
