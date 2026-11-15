"""
文件名: ➡️ tool.py 🏁
路径: ➡️ engines/ae_harness/knowledge/tool.py 🏁
模块功能：➡️ 把知识库检索包成只读工具，返回结构化命中 JSON 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.tool 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_knowledge_tools(): 产出只读 search_knowledge 工具，供调用方挂到 Agent。
2. 挂载时不读配置：首次调用检索时才装载配置并创建检索器。
3. 成功返回 hits；库可用但没命中单独给 no_hit 文案；检索不可用时返回 status=false。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.service: KnowledgeRetriever 与 KnowledgeHit。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_tool.py: 三种返回文案与只读标记
🏁
"""

from __future__ import annotations

import json

from datetime import datetime

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

from .service import KnowledgeRetriever, Retrieval

__all__ = ["build_knowledge_tools"]

# 只读检索，不需要逐次确认。
_ALLOW = PermissionDecision(behavior=PermissionBehavior.ALLOW, message="知识库只读检索，允许执行")


class _LazyRetriever:
    """
    首次调用检索时才装载配置并创建检索器。

    这样 import 与挂载都不碰 yaml；配置写坏只会让工具返回「检索不可用」，
    不会把调用方的入口一起炸掉。
    """

    def __init__(self) -> None:
        self._retriever: KnowledgeRetriever | None = None

    async def retrieve(
        self,
        query: str,
        *,
        base: str | None = None,
        top_k: int | None = None,
    ) -> Retrieval:
        """
        转调真实检索器，首次调用时创建。

        Args:
            query: 检索问题。
            base: 指定库名；None 表示全部启用库。
            top_k: 覆盖返回条数。

        Returns:
            检索结果。
        """
        if self._retriever is None:
            self._retriever = KnowledgeRetriever.from_config()
        return await self._retriever.retrieve(query, base=base, top_k=top_k)


def _stamp() -> str:
    """
    产出操作时间戳。

    Returns:
        形如 2026-11-15_10-53-12.321 的字符串，毫秒三位。
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def _ok(**payload: object) -> str:
    """
    产出成功结果。

    Args:
        **payload: 命中列表等要返回的字段。

    Returns:
        JSON 文本，含 timestamp、status=true 与载荷字段。
    """
    return json.dumps({"timestamp": _stamp(), "status": True, **payload}, ensure_ascii=False)


def _fail(error: str) -> str:
    """
    产出失败结果。

    Args:
        error: 可读原因。

    Returns:
        JSON 文本，含 timestamp、status=false 与 error。
    """
    return json.dumps(
        {"timestamp": _stamp(), "status": False, "error": error},
        ensure_ascii=False,
    )


def build_knowledge_tools(retriever: KnowledgeRetriever | None = None) -> list[FunctionTool]:
    """
    产出知识库检索工具。

    只返回工具对象：不读配置、不连库、不建索引。真正的初始化发生在第一次调用时。
    不传 retriever 时用一个惰性检索器：首次调用才装载配置，配置写坏也只降级成工具报错。

    Args:
        retriever: 已建好的检索器；None 时用惰性检索器。

    Returns:
        只含一个只读工具的列表。
    """
    service = retriever if retriever is not None else _LazyRetriever()

    async def search_knowledge(query: str, base: str = "", top_k: int = 0) -> str:
        """
        在知识库里按语义检索，返回相关片段与相似度，不做改写、不给答案。

        Args:
            query: 检索问题，用自然语言描述要找的内容。
            base: 库名；留空表示检索全部启用库。
            top_k: 返回条数；0 表示用配置默认值。

        Returns:
            JSON 文本：有命中时 hits 为片段数组；没命中时 hits 为空并给 no_hit 说明；
            检索不可用时 status 为 false 并给 error。
        """
        try:
            result = await service.retrieve(query, base=base or None, top_k=top_k or None)
        except Exception as exc:  # noqa: BLE001 - 工具不向上抛，交给模型读错误
            return _fail(f"检索不可用：{exc}")
        if result.status == "unavailable":
            return _fail(f"检索不可用：{result.error}")
        hits = [hit.as_dict() for hit in result.hits]
        if result.status == "no_hit":
            return _ok(hits=[], count=0, note="没有命中：资料里没有与查询相关的内容")
        return _ok(hits=hits, count=len(hits))

    return [
        FunctionTool(
            search_knowledge,
            is_read_only=True,
            is_concurrency_safe=True,
            permission=_ALLOW,
        ),
    ]
