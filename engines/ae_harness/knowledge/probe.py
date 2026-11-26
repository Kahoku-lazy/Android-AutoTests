from __future__ import annotations

import argparse
import asyncio
import sys

from .config import build_config
from .service import KnowledgeRetriever

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m engines.ae_harness.knowledge")
    parser.add_argument("--model-name", required=True, help="向量模型名")
    parser.add_argument("--dimensions", required=True, type=int, help="向量维度")
    parser.add_argument("--api-key-env", required=True, help="密钥环境变量名")
    parser.add_argument("--base", required=True, help="库名")
    parser.add_argument("--data-dir", required=True, help="资料目录绝对路径")
    parser.add_argument("--description", default="探针库", help="库说明")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="对一个库增量建索引")
    retrieve_cmd = sub.add_parser("retrieve", help="检索一个库并打印原始命中")
    retrieve_cmd.add_argument("query", help="检索问题")
    retrieve_cmd.add_argument("--top-k", type=int, default=None, help="返回条数")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    try:
        config = build_config(
            {
                "provider": "dashscope",
                "api_key": args.api_key_env,
                "model_name": args.model_name,
                "dimensions": args.dimensions,
            },
            [
                {
                    "name": args.base,
                    "description": args.description,
                    "data_dir": args.data_dir,
                    "enabled": True,
                }
            ],
        )
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
