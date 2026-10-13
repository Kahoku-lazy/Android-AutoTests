"""手工运行一次设备检查。

在仓库根目录执行：python -m engines.agents.agents logs/01/case.yaml
"""

from __future__ import annotations

import argparse
import os
import time

from pathlib import Path

import yaml

from agentscope.sop import SOP

from .role.base import BaseRole
from .role.config import ModelConfig
from .role.executor import ExecutorRole, VerifierRole
from .workflow import SopRunner, SopStepInput, SopSteps


def parse_case_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析用例路径。未提供路径时退出并打印用法。

    Args:
        argv: 命令行参数；省略时读取进程参数。

    Returns:
        含 case 路径的参数。
    """
    parser = argparse.ArgumentParser(
        prog="python -m engines.agents.agents",
        description="从 YAML 读出用例，每条单独跑一遍设备检查",
    )
    parser.add_argument("case", help="用例 YAML 路径")
    return parser.parse_args(argv)


def load_sop_cases(path: str | Path) -> list[tuple[str, list[SopStepInput]]]:
    """读取 YAML 里的全部用例，顺序与文件一致。

    Args:
        path: 用例文件路径。

    Returns:
        每条用例的流程名称和步骤。单个映射视为一条。

    Raises:
        ValueError: 文件不存在、没有用例，或某条缺少标题、步骤字段缺失、为空白。
    """
    target = Path(path)
    if not target.is_file():
        raise ValueError(f"用例文件不存在：{target}")
    loaded = _case_mappings(yaml.safe_load(target.read_text(encoding="utf-8")), target)
    cases: list[tuple[str, list[SopStepInput]]] = []
    for case_index, case in enumerate(loaded, start=1):
        title = str(case.get("title") or "").strip()
        raw_steps = case.get("steps")
        if not title:
            raise ValueError(f"第 {case_index} 条用例缺少标题：{target}")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError(f"第 {case_index} 条用例步骤为空：{target}")
        steps: list[SopStepInput] = []
        for step_index, raw in enumerate(raw_steps, start=1):
            if not isinstance(raw, dict):
                raise ValueError(f"第 {case_index} 条第 {step_index} 步不是映射：{target}")
            action = str(raw.get("action") or "").strip()
            assertion = str(raw.get("assert") or "").strip()
            if not action or not assertion:
                raise ValueError(
                    f"第 {case_index} 条第 {step_index} 步的 action 和 assert 都不能为空：{target}"
                )
            steps.append(SopStepInput(action, assertion))
        cases.append((title, steps))
    return cases


def build_case_sops(executor: BaseRole, verifier: BaseRole, path: str | Path) -> list[SOP]:
    """把文件中的每条用例装配成一份流程。重试上限固定为 2。

    Args:
        executor: 已启动的执行角色。
        verifier: 已启动的验收角色。
        path: 用例文件路径。

    Returns:
        与文件顺序一致的 SOP 列表。

    Raises:
        ValueError: 用例文件不能用。
    """
    return [
        SopSteps(executor, verifier, steps, name=title, max_attempts=2).build()
        for title, steps in load_sop_cases(path)
    ]


def _case_mappings(loaded: object, target: Path) -> list[dict]:
    """把根节点收成用例映射列表。

    Args:
        loaded: yaml.safe_load 的结果。
        target: 报错时用的文件路径。

    Returns:
        至少一条用例映射。

    Raises:
        ValueError: 根节点不是映射或映射列表，或列表为空。
    """
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list):
        if not loaded:
            raise ValueError(f"用例文件没有用例：{target}")
        if all(isinstance(item, dict) for item in loaded):
            return loaded
        raise ValueError(f"用例文件中的每条都必须是映射：{target}")
    raise ValueError(f"用例文件格式无法识别：{target}")


def final_summary(
    elapsed: float,
    reports: list[dict],
    cases: list[tuple[str, object, list[dict]]],
) -> str:
    """按用例汇总结果、失败点，并给出全部用例的耗时和用量。

    Args:
        elapsed: 从开始到全部用例结束的秒数。
        reports: 每条用例的 cost_report()。
        cases: (标题, 运行阶段, summary 行) 列表。

    Returns:
        要打印的汇总文本。每条用例用标题标识，后接 PASS 或 FAIL。
    """
    lines = ["汇总"]
    for title, phase, rows in cases:
        phase_value = str(getattr(phase, "value", phase))
        failed = [
            f"第 {index} 步 {row['subject']}：{row['message'] or '（无驳回说明）'}"
            for index, row in enumerate(rows, start=1)
            if row["phase"] == "failed" or row["passed"] is False
        ]
        if phase_value == "completed":
            lines.append(f"{title}：PASS")
            continue
        lines.append(f"{title}：FAIL")
        lines.append("  失败点：")
        lines.extend(f"  {item}" for item in (failed or [f"运行阶段 {phase_value}"]))
    calls = sum(item["calls"] for item in reports)
    input_tokens = sum(item["input_tokens"] for item in reports)
    output_tokens = sum(item["output_tokens"] for item in reports)
    cache_hit_tokens = sum(item["cache_hit_tokens"] for item in reports)
    total_cost = round(sum(item["total_cost"] for item in reports), 4)
    lines.append(f"总耗时：{elapsed:.2f} 秒")
    lines.append(
        f"用量与费用：模型调用 {calls} 次 | "
        f"输入 {input_tokens} / 输出 {output_tokens} / "
        f"缓存命中 {cache_hit_tokens} tokens | 合计 {total_cost} 元"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """读出全部用例，每条单独启动角色并跑一遍 SOP。

    Raises:
        SystemExit: 未设置 `DEEPSEEK_API_KEY` 环境变量（提示不要把 key 写进源码）。
    """
    args = parse_case_args(argv)
    cases = load_sop_cases(args.case)
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY（不要把 key 写进源码）")

    config = ModelConfig(
        provider="deepseek",
        model_name="deepseek-flash",
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )

    executor = ExecutorRole(config)
    verifier = VerifierRole(config)
    total = len(cases)
    timer = time.time()
    reports: list[dict] = []
    outcomes: list[tuple[str, object, list[dict]]] = []
    for index, (title, steps) in enumerate(cases, start=1):
        executor.start()
        verifier.start()
        sop = SopSteps(executor, verifier, steps, name=title, max_attempts=2).build()
        runner = SopRunner(
            sop,
            model=config.model_name,
            provider=config.provider,
        )
        print(f"用例 {index}/{total}：{title}")  # noqa: T201
        phase = runner.run("设备ID是：R5CT62RH88F")
        print(f"运行阶段：{phase}")  # noqa: T201
        rows = runner.summary()
        outcomes.append((title, phase, rows))
        for row in rows:
            print(  # noqa: T201
                f"  [{row['phase']}] {row['subject']}"
                f" | 判决者={row['verifier'] or '-'} | {row['message'] or '（无驳回说明）'}"
            )

        report = runner.cost_report()
        reports.append(report)
        print(  # noqa: T201
            f"用量与费用：模型调用 {report['calls']} 次 | "
            f"输入 {report['input_tokens']} / 输出 {report['output_tokens']} / "
            f"缓存命中 {report['cache_hit_tokens']} tokens | 合计 {report['total_cost']} 元"
        )
        for name, data in report["per_agent"].items():
            print(  # noqa: T201
                f"  {name}：调用 {data['calls']} 次 | 输入 {data['input_tokens']} / "
                f"输出 {data['output_tokens']} / 缓存命中 {data['cache_hit_tokens']} tokens | "
                f"{data['total_cost']} 元"
            )

        state_file = Path(f"logs/temps/sop_state_{index}.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(runner.dump_state(), encoding="utf-8")
        print(f"运行状态已存到 {state_file}，可续跑")  # noqa: T201
        if runner.dialogue is not None:
            print(f"对话稿已存到 {runner.dialogue.path}")  # noqa: T201
    print(final_summary(time.time() - timer, reports, outcomes))  # noqa: T201


if __name__ == "__main__":
    main()
