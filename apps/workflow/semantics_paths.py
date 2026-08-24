"""workflow 页面流路径摘要 — 从起点到终点的 DFS 简单路径.

从 ``semantics.py`` 拆出以控制单文件行数（<=400）。依赖 semantics 的
``_str`` / ``_name_of`` / ``_output_port`` 与 MAX_* 常量；semantics 在
``build_graph_digest`` 内延迟 import 本模块，避免循环 import。
"""

from __future__ import annotations

from .semantics import MAX_PATH_DEPTH, MAX_PATHS, _name_of, _output_port, _str

__all__ = ["build_paths"]


def build_paths(nodes: list, links: list, index: dict) -> list[dict]:
    """从起点到终点的路径摘要（DFS 简单路径，防环 + 限深 + 限量）。

    产出 [{text, steps}]：text 为人读文字路径（含点击动作/循环/截断标记），
    steps 为结构化步骤（node_id/name/action）。
    """
    out_map: dict[str, list[dict]] = {}
    for l in links:
        if isinstance(l, dict):
            out_map.setdefault(_str(l.get("origin_id")), []).append(l)

    paths: list[dict] = []

    def emit(steps: list[dict], parts: list[str]) -> bool:
        paths.append({"text": " → ".join(parts), "steps": [dict(s) for s in steps]})
        return True

    def dfs(node: dict, depth: int, steps: list[dict], parts: list[str]):
        if len(paths) >= MAX_PATHS:
            return
        if depth > MAX_PATH_DEPTH:
            parts.append("…(超深截断)")
            emit(steps, parts)
            parts.pop()
            return
        nid = _str(node.get("id"))
        if any(s.get("node_id") == nid for s in steps):
            parts.append(f"{_name_of(node)}(循环)")
            emit(steps, parts)
            parts.pop()
            return
        steps.append({"node_id": nid, "name": _name_of(node)})
        parts.append(_name_of(node))
        if node.get("type") == "EndNode":
            emit(steps, parts)
        else:
            outs = out_map.get(nid, [])
            if not outs:
                parts.append("(无出边，终止)")
                emit(steps, parts)
                parts.pop()
            else:
                for l in outs:
                    if len(paths) >= MAX_PATHS:
                        break
                    op = _output_port(node, l.get("origin_slot"))
                    action = None
                    if isinstance(op, dict) and isinstance(op.get("el"), dict):
                        action = {
                            "element_id": _str(op["el"].get("id")),
                            "label": _str(op["el"].get("label")) or _str(op.get("name")),
                        }
                        steps[-1]["action"] = action
                        parts.append(f"(点击「{action['label']}」)")
                    target = index.get(_str(l.get("target_id")))
                    if target is None:
                        parts.append("目标节点缺失")
                        emit(steps, parts)
                        parts.pop()
                    else:
                        dfs(target, depth + 1, steps, parts)
                    if action:
                        parts.pop()
                        steps[-1].pop("action", None)
        steps.pop()
        parts.pop()

    for n in nodes:
        if len(paths) >= MAX_PATHS:
            break
        if isinstance(n, dict) and n.get("type") == "StartNode":
            dfs(n, 0, [], [])
    return paths
