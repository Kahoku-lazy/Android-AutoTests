"""
看板数据生成器模板（repo-viz-board）。

复制到目标仓库的看板目录后，只改「配置区」这一段，其余可直接用。

    python tools/gen_xxx_data.py          # 写数据
    python tools/gen_xxx_data.py --check  # 只比对，不一致退出码 1（给 CI / 提交前用）

产出：
    data/board.json   机器读
    data/board.js     window.__BOARD__ = ...（页面读；file:// 不能 fetch）
    data/history.json 历史快照（append-only）
    data/history.js   window.__HISTORY__ = ...
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# ─────────────────────────── 配置区（按目标仓库改这里）───────────────────────────

REPO = Path(__file__).resolve().parents[3]  # 看板目录在 repo/dev_docs/<x>/tools 下时据此上溯
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# 模块根目录：模块 = 这个目录下的一个直接子目录
MODULE_ROOT = "backend/apps"

# 模块顺序与中文名（决定页面顺序；必须与真实目录一致，缺的会被跳过）
MODULES = (
    ("accounts", "账号"),
    ("ai_assistant", "AI 助手"),
    # ... 补齐
)

# 统计单元时跳过的目录/文件（包标记与缓存不参与统计）
SKIP_DIRS = {"__pycache__", "migrations", "logs", "vendor"}
SKIP_FILES = {"__init__.py"}

# 历史快照保留条数
HISTORY_LIMIT = 60
TZ = ZoneInfo("Asia/Shanghai")

# ─────────────────────────── 采集 ───────────────────────────


def _loc(paths: list[Path]) -> int:
    """非空物理行合计。"""
    total = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        total += sum(1 for line in text.splitlines() if line.strip())
    return total


def collect_modules() -> dict[str, Any]:
    """按「一层」统计每个模块：直接子目录整体算一个单元，直接 .py 各算一个。"""
    root = REPO / MODULE_ROOT
    modules: list[dict[str, Any]] = []
    module_of_path: dict[str, str] = {}

    for key, label in MODULES:
        base = root / key
        if not base.is_dir():
            continue
        units: list[dict[str, Any]] = []
        owned: list[Path] = []
        for item in sorted(base.iterdir()):
            if item.name in SKIP_FILES or item.name in SKIP_DIRS:
                continue
            if item.is_dir():
                files = [
                    f
                    for f in sorted(item.rglob("*.py"))
                    if "__pycache__" not in f.parts and f.name not in SKIP_FILES
                ]
                if not files:
                    continue
                units.append(
                    {"name": item.name + "/", "kind": "dir", "files": len(files), "loc": _loc(files)}
                )
                owned.extend(files)
            elif item.suffix == ".py":
                units.append({"name": item.name, "kind": "file", "files": 1, "loc": _loc([item])})
                owned.append(item)
        units.sort(key=lambda unit: (-int(unit["loc"]), unit["name"]))
        for path in owned:
            module_of_path[path.as_posix()] = key
        modules.append(
            {
                "key": key,
                "label": label,
                "units": units,
                "totals": {
                    "units": len(units),
                    "files": sum(int(unit["files"]) for unit in units),
                    "loc": sum(int(unit["loc"]) for unit in units),
                },
            }
        )

    return {"modules": modules, "relations": _relations(module_of_path), "totals": _totals(modules)}


def _relations(module_of_path: dict[str, str]) -> list[dict[str, Any]]:
    """模块间 import 次数：只算模块之间存在引用，不猜运行期调用。"""
    known = {key for key, _ in MODULES}
    cross: dict[tuple[str, str], int] = {}
    for path, source in module_of_path.items():
        try:
            tree = ast.parse(Path(path).read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                # 按目标仓库的包路径前缀改这一行，例如 ("backend", "apps", <key>)
                for index, part in enumerate(parts[:-1]):
                    if part == "apps" and parts[index + 1] in known:
                        if parts[index + 1] != source:
                            targets.add(parts[index + 1])
        for target in targets:
            cross[(source, target)] = cross.get((source, target), 0) + 1
    return [
        {"from": source, "to": target, "count": count}
        for (source, target), count in sorted(cross.items(), key=lambda item: (-item[1], item[0]))
    ]


def _totals(modules: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "modules": len(modules),
        "units": sum(int(m["totals"]["units"]) for m in modules),
        "files": sum(int(m["totals"]["files"]) for m in modules),
        "loc": sum(int(m["totals"]["loc"]) for m in modules),
    }


# ─────────────────────────── 历史与对比 ───────────────────────────


def _snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """一条历史：每个模块 × 每个单元的行数（用于最近三次对比）。"""
    units: dict[str, dict[str, int]] = {}
    for module in payload["modules"]:
        units[module["key"]] = {unit["name"]: int(unit["loc"]) for unit in module["units"]}
    return {"at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"), "units": units}


def _read_history() -> list[dict[str, Any]]:
    path = DATA_DIR / "history.json"
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _append_history(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """数值没变就不追加，避免历史里塞满重复条目。"""
    rows = _read_history()
    snapshot = _snapshot(payload)
    if rows and rows[-1].get("units") == snapshot["units"]:
        return rows[-HISTORY_LIMIT:]
    rows.append(snapshot)
    return rows[-HISTORY_LIMIT:]


def _comparison(payload: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """最近三次（本次在前）；缺的位是 None，页面显示「待记录」，绝不补 0。"""
    scope = 3
    entries = history[-scope:]
    ats = [row.get("at", "") for row in reversed(entries)]
    while len(ats) < scope:
        ats.append("")
    units: dict[str, dict[str, list[int | None]]] = {}
    totals: dict[str, list[int | None]] = {}
    for module in payload["modules"]:
        units[module["key"]] = {unit["name"]: [] for unit in module["units"]}
        totals[module["key"]] = []
    for row in reversed(entries):
        slice_ = row.get("units") or {}
        for module in payload["modules"]:
            values = slice_.get(module["key"]) or {}
            subtotal = 0
            for unit in module["units"]:
                has = unit["name"] in values
                units[module["key"]][unit["name"]].append(int(values[unit["name"]]) if has else None)
                if has:
                    subtotal += int(values[unit["name"]])
            totals[module["key"]].append(subtotal if values else None)
    for per_unit in units.values():
        for values in per_unit.values():
            while len(values) < scope:
                values.append(None)
    for values in totals.values():
        while len(values) < scope:
            values.append(None)
    return {"at": ats, "units": units, "totals": totals, "scope": scope}


# ─────────────────────────── 写盘 ───────────────────────────


def write_outputs(payload: dict[str, Any], *, check_only: bool) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = _read_history() if check_only else _append_history(payload)
    comparison = _comparison(payload, history)
    payload["comparison"] = comparison

    for module in payload["modules"]:
        key = module["key"]
        for unit in module["units"]:
            trend = comparison["units"].get(key, {}).get(unit["name"]) or []
            unit["trend"] = (trend + [None, None, None])[:3]
        module["totalTrend"] = (comparison["totals"].get(key) or []) + [None, None, None]
        module["totalTrend"] = module["totalTrend"][:3]

    payload["generated_at"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    payload["commit"] = _commit()

    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    js_text = "window.__BOARD__ = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    history_json = json.dumps(history, ensure_ascii=False, indent=2) + "\n"
    history_js = "window.__HISTORY__ = " + json.dumps(history, ensure_ascii=False) + ";\n"

    files = {
        DATA_DIR / "board.json": json_text,
        DATA_DIR / "board.js": js_text,
        DATA_DIR / "history.json": history_json,
        DATA_DIR / "history.js": history_js,
    }

    if check_only:
        stale = [path.name for path, text in files.items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
        # generated_at / commit 漂移不算过期
        if stale:
            print("数据已过期：" + "、".join(stale))
            return 1
        print("数据最新")
        return 0

    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    totals = payload["totals"]
    print(
        f"已写出 board.json / board.js / history.js：{totals['modules']} 个模块 · "
        f"{totals['units']} 个单元 · {totals['files']} 个文件 · {totals['loc']} 行 · 历史 {len(history)} 次"
    )
    return 0


def _commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="生成看板数据快照")
    parser.add_argument("--check", action="store_true", help="只比对现有快照，不写盘")
    args = parser.parse_args()
    payload = collect_modules()
    return write_outputs(payload, check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
