"""把已评审的平台架构 spec 转成看板可读的快照（1.1 平台架构的数据源）。

口径：
    输入 = dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json（人工语义，已评审）
    输出 = dev_docs/project-viz/data/architecture.json + architecture.js

为什么不让页面直接读 spec：
    看板用 file:// 打开，fetch 会被 CORS 拦；且页面只读快照、不读仓库文件。

为什么不做推理：
    spec 里的组件、连线、标签是**人工写的语义**，这里只做「校验 + 转格式 + 附来源」，
    不推断、不补全、不改写。页面必须原样呈现，缺什么就是缺什么。

用法：
    .venv\\Scripts\\python.exe dev_docs/project-viz/tools/gen_arch_data.py
    .venv\\Scripts\\python.exe dev_docs/project-viz/tools/gen_arch_data.py --check
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
VIZ_DIR = TOOLS_DIR.parent
REPO_ROOT = VIZ_DIR.parent.parent
SPEC_PATH = REPO_ROOT / "dev_docs" / "ARCH_PRD" / "ARCH-平台架构图.spec.json"
DATA_DIR = VIZ_DIR / "data"

VALID_KINDS = {"frontend", "backend", "database", "security", "external", "messagebus", "cloud"}


def fail(message: str) -> None:
    """打印校验失败并退出（退出码 1，供 --check 与 CI 判定）。"""
    print(f"校验失败：{message}", file=sys.stderr)
    raise SystemExit(1)


def load_spec() -> dict:
    """读 spec 并做结构性校验：id 唯一、连线两端存在、边界成员存在、类型合法。"""
    if not SPEC_PATH.exists():
        fail(f"找不到 spec：{SPEC_PATH}")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    components = spec.get("components") or []
    if not components:
        fail("components 为空")

    ids = [c.get("id") for c in components]
    if any(not isinstance(i, str) or not i for i in ids):
        fail("存在空 id")
    if len(set(ids)) != len(ids):
        fail("component id 重复")
    known = set(ids)

    for comp in components:
        kind = comp.get("type")
        if kind not in VALID_KINDS:
            fail(f"未知 type：{comp.get('id')} -> {kind}")
        if not comp.get("label"):
            fail(f"缺 label：{comp.get('id')}")

    for conn in spec.get("connections") or []:
        for side in ("from", "to"):
            if conn.get(side) not in known:
                fail(f"连线指向不存在的组件：{conn.get('id')} -> {conn.get(side)}")

    for boundary in spec.get("boundaries") or []:
        for member in boundary.get("wraps") or []:
            if member not in known:
                fail(f"边界包了不存在的组件：{boundary.get('label')} -> {member}")

    return spec


def build_payload(spec: dict) -> dict:
    """转成页面快照：只保留渲染需要的事实，外加来源信息（不改写任何语义）。"""
    components = []
    for comp in spec["components"]:
        components.append(
            {
                "id": comp["id"],
                "type": comp["type"],
                "label": comp["label"],
                "sublabel": comp.get("sublabel") or "",
                "tag": comp.get("tag") or "",
            }
        )

    connections = []
    for conn in spec.get("connections") or []:
        connections.append(
            {
                "id": conn.get("id") or f'{conn["from"]}-{conn["to"]}',
                "from": conn["from"],
                "to": conn["to"],
                "label": conn.get("label") or "",
                "variant": conn.get("variant") or "default",
            }
        )

    boundaries = []
    for boundary in spec.get("boundaries") or []:
        boundaries.append(
            {
                "kind": boundary.get("kind") or "region",
                "label": boundary.get("label") or "",
                "wraps": list(boundary.get("wraps") or []),
                "pad": boundary.get("pad", 22),
            }
        )

    cards = []
    for card in spec.get("cards") or []:
        cards.append({"dot": card.get("dot") or "", "title": card.get("title") or "", "items": list(card.get("items") or [])})

    kind_counts: dict[str, int] = {}
    for comp in components:
        kind_counts[comp["type"]] = kind_counts.get(comp["type"], 0) + 1

    return {
        "source": {
            "path": SPEC_PATH.relative_to(REPO_ROOT).as_posix(),
            "title": (spec.get("meta") or {}).get("title") or "",
            "note": "人工语义：组件、连线、标签来自 spec，不是 AST 静态解析",
        },
        "title": (spec.get("meta") or {}).get("title") or "",
        "kindCounts": kind_counts,
        "components": components,
        "connections": connections,
        "boundaries": boundaries,
        "cards": cards,
    }


def write_outputs(payload: dict, check_only: bool) -> int:
    """写 architecture.json / architecture.js；--check 只比对不落盘。

    快照里不放时间戳：这份数据的“新鲜度”由 spec 内容决定，加时间会让 --check 永远报过期。
    """
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    js_text = "window.__ARCH__ = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"

    json_path = DATA_DIR / "architecture.json"
    js_path = DATA_DIR / "architecture.js"

    if check_only:
        stale = []
        if not json_path.exists():
            stale.append(json_path.name)
        else:
            try:
                current = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                stale.append(json_path.name)
            else:
                if current != payload:
                    stale.append(json_path.name)
        if not js_path.exists() or js_path.read_text(encoding="utf-8") != js_text:
            stale.append(js_path.name)
        if stale:
            print("架构快照已过期：" + "、".join(stale) + "（重跑 gen_arch_data.py）")
            return 1
        print("架构快照最新")
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_text, encoding="utf-8")
    js_path.write_text(js_text, encoding="utf-8")
    kinds = " ".join(f"{k}={v}" for k, v in sorted(payload["kindCounts"].items()))
    print(
        f"已写出 architecture.json / architecture.js："
        f"{len(payload['components'])} 组件 / {len(payload['connections'])} 连线 / "
        f"{len(payload['boundaries'])} 边界 / {len(payload['cards'])} 卡片（{kinds}）"
    )
    return 0


def main(argv: list[str]) -> int:
    """入口：--check 只比对，默认写盘。"""
    check_only = "--check" in argv
    spec = load_spec()
    return write_outputs(build_payload(spec), check_only)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
