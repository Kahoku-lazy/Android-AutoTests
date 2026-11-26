from __future__ import annotations

import json

from datetime import datetime

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

from .service import KnowledgeRetriever

__all__ = ["build_knowledge_tools"]

_ALLOW = PermissionDecision(behavior=PermissionBehavior.ALLOW, message="知识库只读检索，允许执行")


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def _ok(**payload: object) -> str:
    return json.dumps({"timestamp": _stamp(), "status": True, **payload}, ensure_ascii=False)


def _fail(error: str) -> str:
    return json.dumps(
        {"timestamp": _stamp(), "status": False, "error": error},
        ensure_ascii=False,
    )


def build_knowledge_tools(retriever: KnowledgeRetriever) -> list[FunctionTool]:
    service = retriever

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
