"""执行模型步骤级跑测工具 —— 直接驱动引擎，不经平台任务链路。

它做的事：读一个 JSON（多条步骤）→ 逐条交给引擎侧执行模型 → 当场打印
**模型思考过程 / 工具调用与返回记录 / 截图路径 / 输出 JSON / token 与费用**，
末尾打印总计，并把完整记录写到 `tests/reports/engines/`（git 忽略）。

步骤 JSON 形状（与平台任务输入的四键口径一致，多余键忽略）::

    {
      "serial": "R5CT62RH88F",
      "steps": [
        {"action": "启动 govee 应用（com.govee.home）", "assert": "前台为 govee 首页", "log_check": false},
        {"action": "在设备主页向上滑动一次", "assert": "列表发生滚动", "log_check": false}
      ]
    }

用法（命令行）::

    $env:EXECUTOR_API_KEY = "sk-..."            # 必需；不落盘
    python tests/engines/test_executor_steps.py tests/engines/steps.sample.json
    python tests/engines/test_executor_steps.py my_steps.json --serial R5CT62RH88F --fresh-context

模型连接从环境变量读取（默认 deepseek + deepseek-flash + 官方 base_url）::

    EXECUTOR_PROVIDER / EXECUTOR_MODEL / EXECUTOR_API_KEY / EXECUTOR_BASE_URL

pytest 下默认**跳过**：需要同时设置 `EXECUTOR_API_KEY` 与 `EXECUTOR_STEPS_RUN=1`（避免默认套件误连真机与产生费用）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from engines.ai.agents import DeviceExecutionConfig, ExecutorRole, ModelConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_STEPS = Path(__file__).with_name("steps.sample.json")
DEFAULT_REPORT_DIR = REPO_ROOT / "tests" / "reports" / "engines"

DEFAULT_PROVIDER = "deepseek"
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

MAX_TEXT = 600  # 单条打印上限（完整内容仍写进 JSONL 记录）


class HarnessConfigError(RuntimeError):
    """跑测前置条件不满足（缺密钥 / 缺步骤等），带可读指引。"""


# ── 输入与配置 ────────────────────────────────────────────────────


def load_steps(path: str | Path) -> tuple[str, list[dict]]:
    """读步骤 JSON → (serial, steps)；步骤项可以是对象或纯字符串。"""
    target = Path(path)
    if not target.is_file():
        raise HarnessConfigError(f"步骤文件不存在：{target}")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HarnessConfigError(f"步骤文件不是合法 JSON：{target}（{exc}）") from exc

    raw_steps = payload.get("steps") if isinstance(payload, dict) else payload
    if not isinstance(raw_steps, list) or not raw_steps:
        raise HarnessConfigError(f"步骤文件里没有 steps 数组或为空：{target}")

    steps: list[dict] = []
    for index, item in enumerate(raw_steps, 1):
        if isinstance(item, str):
            steps.append({"action": item, "assert": "", "log_check": False})
        elif isinstance(item, dict) and str(item.get("action") or "").strip():
            steps.append(
                {
                    "action": str(item["action"]).strip(),
                    "assert": str(item.get("assert") or "").strip(),
                    "log_check": bool(item.get("log_check", False)),
                }
            )
        else:
            raise HarnessConfigError(f"第 {index} 条步骤缺少 action 字段：{item!r}")

    serial = str((payload.get("serial") if isinstance(payload, dict) else "") or "").strip()
    return serial, steps


def build_config() -> DeviceExecutionConfig:
    """从环境变量组装执行模型的连接配置（缺密钥给可读指引）。"""
    api_key = os.environ.get("EXECUTOR_API_KEY", "").strip()
    if not api_key:
        raise HarnessConfigError(
            "缺少 EXECUTOR_API_KEY：跑测会真实调用模型。设置示例（PowerShell）：\n"
            '  $env:EXECUTOR_API_KEY = "sk-..."\n'
            "可选：EXECUTOR_PROVIDER（默认 deepseek）/ EXECUTOR_MODEL（默认 deepseek-flash）"
            "/ EXECUTOR_BASE_URL（默认 https://api.deepseek.com/v1）"
        )
    model = ModelConfig(
        provider=os.environ.get("EXECUTOR_PROVIDER", DEFAULT_PROVIDER).strip() or DEFAULT_PROVIDER,
        model_name=os.environ.get("EXECUTOR_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        api_key=api_key,
        base_url=os.environ.get("EXECUTOR_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
    )
    return DeviceExecutionConfig(executor=model)


def missing_prerequisites(steps_path: Path) -> str:
    """返回跳过原因（空串 = 可执行）。"""
    if not steps_path.is_file():
        return f"步骤文件不存在：{steps_path}"
    if os.environ.get("EXECUTOR_STEPS_RUN", "").strip() != "1":
        return "未开启跑测：需设置 EXECUTOR_STEPS_RUN=1（避免默认套件连真机、产生费用）"
    if not os.environ.get("EXECUTOR_API_KEY", "").strip():
        return "缺少 EXECUTOR_API_KEY"
    return ""


# ── 打印 ──────────────────────────────────────────────────────────


def _short(text: object, limit: int = MAX_TEXT) -> str:
    value = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False, default=str)
    value = value.replace("\n", " ")
    return (
        value
        if len(value) <= limit
        else value[:limit] + f"…（截断，完整内容见 JSONL，共 {len(value)} 字符）"
    )


def print_thinking(thinking: list[str]) -> None:
    print(f"  [思考] {len(thinking)} 段")
    for index, item in enumerate(thinking, 1):
        print(f"    ({index}) {_short(item)}")


def print_tool_usage(tool_usage: list[dict]) -> None:
    calls = [row for row in tool_usage if row.get("type") == "call"]
    results = [row for row in tool_usage if row.get("type") == "result"]
    print(f"  [工具调用] {len(calls)} 次调用 / {len(results)} 条返回")
    for row in tool_usage:
        kind = row.get("type")
        if kind == "call":
            print(f"    → 调 {row.get('name')} 入参={_short(row.get('input'), 300)}")
        elif kind == "result":
            print(
                f"    ← {row.get('name')} 状态={row.get('state') or '-'} "
                f"返回={_short(row.get('output'), 300)}"
            )
            if row.get("screenshot_path"):
                print(f"      截图：{row['screenshot_path']}")
        elif kind == "image":
            print(f"    [图片] {row.get('media_type')}")


@dataclass
class StepRecord:
    """单步记录（打印 + 落 JSONL 用）。"""

    index: int
    total: int
    action: str
    assertion: str = ""
    log_check: bool = False
    ok: bool = True
    error: str = ""
    output: str = ""
    thinking: list[str] = field(default_factory=list)
    tool_usage: list[dict] = field(default_factory=list)
    screenshot_path: str = ""
    usage: dict = field(default_factory=dict)
    cost: float = 0.0
    seconds: float = 0.0

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "total": self.total,
            "action": self.action,
            "assert": self.assertion,
            "log_check": self.log_check,
            "ok": self.ok,
            "error": self.error,
            "output": self.output,
            "thinking": self.thinking,
            "tool_usage": self.tool_usage,
            "screenshot_path": self.screenshot_path,
            "usage": self.usage,
            "cost": self.cost,
            "seconds": round(self.seconds, 2),
        }


# ── 执行 ──────────────────────────────────────────────────────────


def run_steps(
    serial: str,
    steps: list[dict],
    *,
    fresh_context: bool = False,
    report_dir: Path = DEFAULT_REPORT_DIR,
) -> list[StepRecord]:
    """逐条执行步骤并打印过程；返回每步记录。"""
    if not serial:
        raise HarnessConfigError("缺少设备 serial：请在步骤 JSON 里给 serial，或用 --serial 指定")

    config = build_config()
    shots_dir = report_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    role = ExecutorRole(
        config.executor,
        [],  # 设备动作工具由引擎自带（登记清单），无需平台注入
        user_id="harness",
        skill_dirs=[],
        media_root=str(shots_dir),
    )

    print("=" * 78)
    print(
        f"执行模型跑测 · serial={serial} · 模型={config.executor.provider}/{config.executor.model_name}"
        f" · 步骤数={len(steps)}"
    )
    print("=" * 78)

    loop = asyncio.new_event_loop()
    records: list[StepRecord] = []
    try:
        for index, step in enumerate(steps, 1):
            if fresh_context:
                role.reset_context()
            record = StepRecord(
                index=index,
                total=len(steps),
                action=step["action"],
                assertion=step.get("assert", ""),
                log_check=bool(step.get("log_check")),
            )
            print(f"\n── 步骤 {index}/{len(steps)} ──")
            print(f"  action  : {record.action}")
            if record.assertion:
                print(f"  assert  : {record.assertion}")
            print(f"  log_check: {record.log_check}")
            started = time.time()
            try:
                result = loop.run_until_complete(role.run(serial, record.action, index, len(steps)))
            except Exception as exc:  # noqa: BLE001 - 单步失败不中断整轮
                record.ok = False
                record.error = f"{type(exc).__name__}: {exc}"
                record.seconds = time.time() - started
                print(f"  ✗ 执行异常：{record.error}")
                records.append(record)
                continue

            record.seconds = time.time() - started
            record.output = result.output
            record.thinking = list(result.thinking or [])
            record.tool_usage = list(result.tool_usage or [])
            record.screenshot_path = result.screenshot_path or ""
            record.usage = dict(result.usage or {})
            record.cost = float(result.cost or 0.0)

            print_thinking(record.thinking)
            print_tool_usage(record.tool_usage)
            print(f"  [截图路径] {record.screenshot_path or '(本步未产生截图)'}")
            print(f"  [输出] {_short(record.output)}")
            print(
                f"  [用量] 输入 {record.usage.get('input_tokens', 0)} / 输出 "
                f"{record.usage.get('output_tokens', 0)} / 缓存命中 "
                f"{record.usage.get('cache_input_tokens', 0)} · 费用 {record.cost:.6f} · 耗时 {record.seconds:.1f}s"
            )
            records.append(record)
    finally:
        loop.close()

    _write_report(records, report_dir)
    _print_summary(records, report_dir)
    return records


def _write_report(records: list[StepRecord], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    target = report_dir / f"run-{stamp}.jsonl"
    target.write_text(
        "\n".join(json.dumps(row.as_dict(), ensure_ascii=False, default=str) for row in records),
        encoding="utf-8",
    )
    return target


def _print_summary(records: list[StepRecord], report_dir: Path) -> None:
    total_cost = sum(row.cost for row in records)
    total_in = sum(int(row.usage.get("input_tokens", 0) or 0) for row in records)
    total_out = sum(int(row.usage.get("output_tokens", 0) or 0) for row in records)
    failed = [row.index for row in records if not row.ok]

    print("\n" + "=" * 78)
    print("汇总")
    print("-" * 78)
    for row in records:
        state = "OK " if row.ok else "失败"
        print(
            f"  {row.index}/{row.total} [{state}] {row.action[:40]:<40} "
            f"费用 {row.cost:.6f} · 输入 {row.usage.get('input_tokens', 0)} / "
            f"输出 {row.usage.get('output_tokens', 0)} · {row.seconds:.1f}s"
        )
        if row.output:
            print(f"        输出：{_short(row.output, 160)}")
    print("-" * 78)
    print(
        f"  步数 {len(records)} · 失败 {len(failed) or 0} 步{('（' + ', '.join(map(str, failed)) + '）') if failed else ''}"
    )
    print(f"  费用合计 {total_cost:.6f} · 输入 {total_in} / 输出 {total_out} tokens")
    print(f"  完整记录与截图：{report_dir}")
    print("=" * 78)


# ── 入口：命令行 + pytest ──────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="执行模型步骤级跑测（直接驱动引擎）")
    parser.add_argument("steps", nargs="?", default=str(SAMPLE_STEPS), help="步骤 JSON 路径")
    parser.add_argument("--serial", default="", help="设备 serial（覆盖 JSON 里的 serial）")
    parser.add_argument(
        "--fresh-context", action="store_true", help="每步清空上下文（默认累积，与生产一致）"
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="记录与截图目录")
    args = parser.parse_args(argv)

    try:
        serial, steps = load_steps(args.steps)
        records = run_steps(
            args.serial or serial,
            steps,
            fresh_context=args.fresh_context,
            report_dir=Path(args.report_dir),
        )
    except HarnessConfigError as exc:
        print(f"[配置错误] {exc}")
        return 2
    return 0 if all(row.ok for row in records) else 1


@pytest.mark.e2e
@pytest.mark.ai_assistant
@pytest.mark.slow
def test_executor_steps_from_json() -> None:
    """读 JSON 步骤逐条执行（真机 + 付费密钥；未开启跑测时跳过）。

    开启方式：`EXECUTOR_STEPS_RUN=1` + `EXECUTOR_API_KEY=sk-...`
    （步骤文件可用 `EXECUTOR_STEPS` 指定，默认用同目录的 steps.sample.json）。
    """
    steps_path = Path(os.environ.get("EXECUTOR_STEPS", str(SAMPLE_STEPS)))
    reason = missing_prerequisites(steps_path)
    if reason:
        pytest.skip(reason)

    serial, steps = load_steps(steps_path)
    records = run_steps(serial, steps, report_dir=DEFAULT_REPORT_DIR)

    assert records, "至少应有一条步骤记录"
    assert all(row.error == "" for row in records), "不应有步骤抛异常"
    assert all(row.output for row in records), "每步都应有模型输出"
    assert all(row.tool_usage for row in records), "每步都应有工具调用记录"
    assert sum(row.cost for row in records) > 0, "应统计到费用"


if __name__ == "__main__":
    sys.exit(main())
