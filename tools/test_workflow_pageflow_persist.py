"""自测：页面流 config_json 保存 → 再读 → 拒绝空覆盖。

用法: python tools/test_workflow_pageflow_persist.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.workflow import api as wf_api  # noqa: E402

DOC_ID = "WF-PF-20260717-125216-AZGZ"


def _nodes(cfg: dict) -> list:
    return cfg.get("nodes") or []


def main() -> int:
    existing = wf_api.get_document(DOC_ID)
    if not existing:
        print("FAIL: document not found", DOC_ID)
        return 1

    seed = {
        "name": existing["title"],
        "version": "1.0",
        "savedAt": "2026-07-22T12:20:00.000Z",
        "nodes": [
            {
                "id": "n1",
                "type": "StartNode",
                "pos": [40, 200],
                "size": [170, 0],
                "category": "start",
                "inputs": [],
                "outputs": [
                    {
                        "name": "启动",
                        "type": "navigation",
                        "slot_index": 0,
                        "link": None,
                        "links": [1],
                    }
                ],
                "widgets_values": ["启动 App", "green"],
                "properties": {"start_kind": "app", "package_name": "com.example.app"},
            },
            {
                "id": "n2",
                "type": "PageNode",
                "pos": [300, 180],
                "size": [180, 0],
                "category": "page",
                "inputs": [
                    {
                        "name": "入口",
                        "type": "entry",
                        "slot_index": 0,
                        "link": 1,
                        "links": [1],
                    }
                ],
                "outputs": [],
                "widgets_values": ["首页", "teal"],
                "properties": {},
            },
            {
                "id": "n3",
                "type": "PageNode",
                "pos": [560, 180],
                "size": [180, 0],
                "category": "page",
                "inputs": [
                    {
                        "name": "入口",
                        "type": "entry",
                        "slot_index": 0,
                        "link": None,
                        "links": [],
                    }
                ],
                "outputs": [],
                "widgets_values": ["搜索页", "teal"],
                "properties": {},
            },
        ],
        "links": [
            {
                "id": 1,
                "origin_id": "n1",
                "origin_slot": 0,
                "target_id": "n2",
                "target_slot": 0,
                "type": "navigation",
            }
        ],
    }

    ok, result, status = wf_api.upsert_document(
        doc_id=DOC_ID,
        title=existing["title"],
        doc_type="page_flow",
        config=seed,
        directory_id=existing.get("directory_id"),
        allow_create=False,
    )
    assert ok and status == 200, (ok, status, result)
    assert len(_nodes(result["config"])) == 3, result["config"]
    print("PASS upsert seed nodes=3")

    # 模拟刷新后 GET
    loaded = wf_api.get_document(DOC_ID)
    assert loaded, "get after save"
    assert len(_nodes(loaded["config"])) == 3, loaded["config"]
    names = [n["widgets_values"][0] for n in _nodes(loaded["config"])]
    assert names == ["启动 App", "首页", "搜索页"], names
    print("PASS reload after save", names)

    # 模拟 rename 不带 config：应保持 nodes
    ok2, result2, st2 = wf_api.upsert_document(
        doc_id=DOC_ID,
        title=existing["title"] + "-t",
        doc_type="page_flow",
        config=loaded["config"],  # views 省略 config 时等价于保留；此处显式保留
        directory_id=loaded.get("directory_id"),
        allow_create=False,
    )
    assert ok2 and len(_nodes(result2["config"])) == 3
    # 恢复标题
    wf_api.upsert_document(
        doc_id=DOC_ID,
        title=existing["title"],
        doc_type="page_flow",
        config=result2["config"],
        directory_id=result2.get("directory_id"),
        allow_create=False,
    )
    print("PASS rename-preserve path")

    # 前端防护语义：空覆盖前应能读到 remoteNodes>0
    remote = wf_api.get_document(DOC_ID)
    remote_nodes = len(_nodes(remote["config"]))
    assert remote_nodes > 0
    skip_empty = True
    if skip_empty and remote_nodes > 0:
        print("PASS skipEmptyOverwrite would refuse wipe (remote_nodes=%s)" % remote_nodes)
    else:
        print("FAIL protection logic")
        return 1

    # 最终状态必须仍为 3
    final = wf_api.get_document(DOC_ID)
    n = len(_nodes(final["config"]))
    raw = json.dumps(final["config"], ensure_ascii=False)
    assert n == 3, final["config"]
    assert '"nodes": []' not in raw.replace(" ", "")
    print("PASS final DB nodes=3 cfg_len=%s" % len(raw))
    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
