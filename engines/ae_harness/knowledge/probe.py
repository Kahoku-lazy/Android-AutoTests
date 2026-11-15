"""
文件名: ➡️ probe.py 🏁
路径: ➡️ engines/ae_harness/knowledge/probe.py 🏁
模块功能：➡️ 知识库探针：建索引或打印未经改写的检索命中，不创建智能体 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.probe retrieve product_manuals "指示灯" 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_parser(): 两个子命令 index / retrieve。
2. main(): 不创建 Agent、不调用聊天模型；配置错误返回 1，没命中返回 0。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.service: KnowledgeRetriever。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_probe.py: 退出码区分无命中与配置错误
🏁
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .config import load_config
from .service import KnowledgeRetriever

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """
    构建命令行解析器。

    Returns:
        带 index / retrieve 两个子命令的解析器。
    """
    parser = argparse.ArgumentParser(prog="python -m engines.ae_harness.knowledge")
    sub = parser.add_subparsers(dest="command", required=True)
    index_cmd = sub.add_parser("index", help="对一个库增量建索引")
    index_cmd.add_argument("base", help="库名")
    retrieve_cmd = sub.add_parser("retrieve", help="检索一个库并打印原始命中")
    retrieve_cmd.add_argument("base", help="库名")
    retrieve_cmd.add_argument("query", help="检索问题")
    retrieve_cmd.add_argument("--top-k", type=int, default=None, help="返回条数")
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    运行探针。

    Args:
        argv: 命令行参数；None 时读 sys.argv。

    Returns:
        退出码：0 表示探针正常结束（含没命中），1 表示配置或参数有问题。
    """
    args = build_parser().parse_args(argv)
    try:
        config = load_config()
    except ValueError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 1
    retriever = KnowledgeRetriever(config)
    if args.command == "index":
        count = asyncio.run(retriever.ensure_index(args.base))
        error = retriever.error(args.base)
        if error:
            print(f"索引失败：{error}", file=sys.stderr)
            return 1
        print(f"{args.base}: 本次重建 {count} 个文件")
        return 0
    result = asyncio.run(
        retriever.retrieve(args.query, base=args.base, top_k=args.top_k),
    )
    if result.status == "unavailable":
        print(f"检索不可用：{result.error}", file=sys.stderr)
        return 1
    if result.status == "no_hit":
        print(f"{args.base}: 没有命中")
        return 0
    for hit in result.hits:
        print(f"[{hit.score:.4f}] {hit.source}#{hit.chunk_index} ({hit.document_id})")
        print(hit.text)
    return 0
