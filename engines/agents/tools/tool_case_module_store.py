"""
python -m 调试路径: engines.agents.workflow.case_module_store

本模块的业务功能如下：
1. ModuleStore: 一次任务内按模块 KEY 保存用例文档与报告。
2. build_writer_store_tools: 给编写角色装配「保存/读取当前模块文档」工具。
3. build_verifier_store_tools: 给验收角色装配「读取当前模块文档」工具。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

# 写工具走平台内部存储，不需要人工授权。
_ALLOW = PermissionDecision(PermissionBehavior.ALLOW, "平台内部模块文档存储")


@dataclass
class ModuleStore:
    """
    一次用例编写任务内的模块文档存储。

    Attributes:
        documents: 模块 KEY → 完整 Markdown 文档。
        reports: 模块 KEY → 编写角色的交付摘要。
    """

    documents: dict[str, str] = field(default_factory=dict)
    reports: dict[str, str] = field(default_factory=dict)

    def save(self, key: str, markdown: str) -> None:
        """保存一个模块的完整文档。"""
        self.documents[key] = str(markdown or "")

    def get(self, key: str) -> str:
        """读取一个模块的完整文档；没有时返回空串。"""
        return self.documents.get(key, "")


def _save_tool(store: ModuleStore, key: str) -> FunctionTool:
    """构造当前模块的保存工具；KEY 由闭包固定，模型不能写错模块。"""

    async def save_case_module_document(markdown: str) -> str:
        """保存当前模块的完整七节 Markdown 文档，返回保存结果。"""
        text = str(markdown or "")
        if len(text.strip()) < 200:
            return f"保存失败：文档正文过短（{len(text)} 字符），请提交完整七节文档。"
        store.save(key, text)
        return f"已保存模块 {key}，共 {len(text)} 字符。"

    return FunctionTool(
        save_case_module_document,
        name="save_case_module_document",
        description=(
            f"保存模块 {key} 的完整七节 Markdown 用例文档。"
            "必须一次传入完整正文；保存成功后最终 report 只写摘要。"
        ),
        # 平台内部存储不是外部副作用；按只读工具放行，避免 GoalPipeline 停在人工授权上。
        is_read_only=True,
        permission=_ALLOW,
    )


def _read_tool(store: ModuleStore, key: str) -> FunctionTool:
    """构造当前模块的读取工具。"""

    async def read_case_module_document() -> str:
        """读取当前模块已保存的完整文档；没有时返回提示。"""
        text = store.get(key)
        if not text:
            return f"模块 {key} 还没有保存任何文档。"
        return text

    return FunctionTool(
        read_case_module_document,
        name="read_case_module_document",
        description=f"读取模块 {key} 当前已保存的完整 Markdown 文档。",
        is_read_only=True,
        permission=_ALLOW,
    )


def build_writer_store_tools(store: ModuleStore, key: str) -> list[FunctionTool]:
    """编写角色的模块存储工具：保存 + 读取。"""
    return [_save_tool(store, key), _read_tool(store, key)]


def build_verifier_store_tools(store: ModuleStore, key: str) -> list[FunctionTool]:
    """验收角色的模块存储工具：只读。"""
    return [_read_tool(store, key)]
