from __future__ import annotations

from pathlib import Path

from engines.backend_bridge.result import UiRunResult
from engines.backend_bridge.session import open_session

__all__ = ["UiRunResult", "run_ui_task"]


async def run_ui_task(
    task: str,
    *,
    system_prompt: str,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    report_root: Path | None = None,
    controls: list | None = None,
) -> UiRunResult:
    session = await open_session(
        "",
        system_prompt=system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        controls=controls,
    )
    return await session.run_turn(task, report_root=report_root)


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        run_ui_task(
            "只回复 OK 两个字母，不要调用任何工具。",
            system_prompt="你是 UI 执行者。",
            provider="openai",
            api_key_env="OPENAI_API_KEY",
            model_name="deepseek-flash",
        )
    )
    print(result.report_path)  # noqa: T201 - 模块自测入口
