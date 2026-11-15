"""
文件名: ➡️ probe.py 🏁
路径: ➡️ engines/agents/rag/probe.py 🏁
模块功能：➡️ 知识库探针：打印索引数量和未经改写的检索命中 🏁
Python 调试：➡️ python -m engines.agents.rag.probe 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_project_env(): 按平台规则加载仓库 .env，不覆盖已有环境变量。
2. run_index(): 索引一个库并返回探针文本。
3. run_retrieve(): 检索一个库并返回原始命中文本。
🏁
关联模块：➡️
1. engines.agents.rag.service: 导入 KnowledgeBaseService
2. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/engines/agents/unit/test_rag_probe.py: 无命中与配置错误的退出码
🏁
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from backend.config.env import load_dotenv
from engines.agents.rag.service import KnowledgeBaseService, KnowledgeHit


def load_project_env() -> None:
    """加载仓库 `.env`；已存在的环境变量优先。"""
    load_dotenv()


def format_index(base: str, indexed: int, error: str) -> str:
    """
    格式化索引探针输出。

    Args:
        base: 库名。
        indexed: 本次重建文件数。
        error: 可读错误；成功时为空。

    Returns:
        多行探针文本。
    """
    return f"base: {base}\nindexed: {indexed}\nerror: {error}\n"


def format_hits(base: str, hits: list[KnowledgeHit], error: str) -> str:
    """
    格式化检索探针输出。

    Args:
        base: 库名。
        hits: 原始命中。
        error: 可读错误；无命中时可以为空。

    Returns:
        多行探针文本。
    """
    lines = [f"base: {base}", f"hits: {len(hits)}", f"error: {error}"]
    for index, hit in enumerate(hits, start=1):
        lines.extend(
            [
                "",
                f"[{index}] score={hit.score:.2f} chunk={hit.chunk_index} source={hit.source}",
                hit.text,
            ]
        )
    return "\n".join(lines) + "\n"


async def run_index(base: str) -> tuple[str, int]:
    """
    索引一个库。

    Args:
        base: 库名。

    Returns:
        探针文本和退出码。
    """
    try:
        service = KnowledgeBaseService.from_env()
    except ValueError as exc:
        return f"error: {exc}\n", 1
    if not service.enabled:
        return "error: 嵌入检索未启用\n", 1
    indexed = await service.ensure_index(base)
    error = service.error(base)
    return format_index(base, indexed, error), 1 if error else 0


async def run_retrieve(base: str, query: str) -> tuple[str, int]:
    """
    检索一个库。

    Args:
        base: 库名。
        query: 检索问题。

    Returns:
        探针文本和退出码。没有命中时退出码为 0。
    """
    try:
        service = KnowledgeBaseService.from_env()
    except ValueError as exc:
        return f"error: {exc}\n", 1
    if not service.enabled:
        return "error: 嵌入检索未启用\n", 1
    hits = await service.retrieve(base, query)
    error = service.error(base)
    failed = bool(error) and error != "检索问题不能为空"
    if not query.strip():
        failed = True
    return format_hits(base, hits, error), 1 if failed and not hits else 0


def main(argv: list[str] | None = None) -> int:
    """
    运行知识库探针。

    Args:
        argv: 命令参数；None 时读取进程参数。

    Returns:
        进程退出码。配置或参数错误为 1，没有命中为 0。
    """
    parser = argparse.ArgumentParser(prog="python -m engines.agents.rag")
    sub = parser.add_subparsers(dest="command", required=True)
    index = sub.add_parser("index")
    index.add_argument("base")
    retrieve = sub.add_parser("retrieve")
    retrieve.add_argument("base")
    retrieve.add_argument("query")
    args = parser.parse_args(argv)
    load_project_env()
    if args.command == "index":
        text, code = asyncio.run(run_index(args.base))
    else:
        text, code = asyncio.run(run_retrieve(args.base, args.query))
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
