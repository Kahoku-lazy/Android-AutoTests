"""结果验收角色：对比断言 + 执行截图 + 设备日志证据，判断操作是否真实达成。

提示词与工具子集取自 `config.py`，另含验收特有的截图工具包装（强制保留落盘路径），
公共主干在 `base.AgentRole`。
"""

from __future__ import annotations

import inspect

from agentscope.message import TextBlock

from engines.ai.base import ToolSpec
from engines.ai.messaging import RoleResult

from .base import AgentRole, RoleSpec
from .config import CHINESE_DEMAND, VERIFIER_PROMPT, VERIFIER_TOOLS


def _force_keep_local_screenshot(handler):
    """验收工具包装：无论模型是否传 keep_local，一律以 keep_local=True 调用并保留路径回传。

    `user_id` 只在被包装的实现声明了它时才转发；否则调用会报 `unexpected keyword argument`。
    """
    try:
        accepts_user_id = "user_id" in inspect.signature(handler).parameters
    except (TypeError, ValueError):  # 内建/不可自省的实现：按不接收处理
        accepts_user_id = False

    def wrapped(serial: str, keep_local: bool = True, user_id: str = "", **kwargs):
        if accepts_user_id:
            return handler(serial, keep_local=True, user_id=user_id, **kwargs)
        return handler(serial, keep_local=True, **kwargs)

    wrapped.__name__ = getattr(handler, "__name__", "screenshot_page")
    wrapped.__doc__ = getattr(handler, "__doc__", "") or ""
    return wrapped


class VerifierRole(AgentRole):
    """验收角色：对比断言与执行截图，输出是否通过（验收是否真实达成）。"""

    spec = RoleSpec(
        role="verifier",
        prompt=VERIFIER_PROMPT,
        tool_names=tuple(VERIFIER_TOOLS),
        vision=True,
        context_config={"max_image_num": 5},
    )

    def _select_tools(self, tools: list[ToolSpec]) -> list[ToolSpec]:
        """验收子集：screenshot_page 强制 keep_local=True，保证证据路径回传。"""
        selected = super()._select_tools(tools)
        out: list[ToolSpec] = []
        for spec in selected:
            if spec.name == "screenshot_page":
                out.append(
                    ToolSpec(
                        name=spec.name,
                        handler=_force_keep_local_screenshot(spec.handler),
                        read_only=spec.read_only,
                        auto_allow=spec.auto_allow,
                    )
                )
            else:
                out.append(spec)
        return out

    async def run(
        self,
        serial: str,
        assertion: str,
        idx: int,
        total: int,
        exec_result: str,
        exec_evidence: str,
        screenshot=None,
        log_evidence: str = "",
        keyword_catalog: str = "",
    ) -> RoleResult:
        """接受任务：对比断言 + 截图 + 日志检查结论，判断操作是否成功。

        Args:
            serial: 目标设备 serial。
            assertion: 本步骤的断言（期望的可观察结果）。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            exec_result: 执行模型的 result（PASS/FAIL）。
            exec_evidence: 平台按执行契约拼装的证据文本（点击前时间戳 + 点击后截图路径；
                无点击 / 未截图时已如实标注）——执行模型不再输出说明文字。
            screenshot: 执行模型产出的操作结果截图（DataBlock，可空）。
            log_evidence: 本步的日志证据文本（可空 = 无日志证据，只看截图）。
            keyword_catalog: 当前日志关键词表文本（关键词 → 功能点；空 = 不附）。

        Returns:
            RoleResult（output 为 {"result","click_timer","logAssertionTimer",
            "logAssertionInfo","screenshot","actual"} JSON）。
        """
        self.mark_scope(f"步骤 {idx}/{total} 验收")
        text = (
            f"当前设备 serial：{serial}\n"
            f"断言 assert：{assertion}\n"
            f"执行结果：result={exec_result}；{exec_evidence}\n"
        )
        if log_evidence:
            text += f"\n{log_evidence}\n"
        text += f"请截图确认，对比断言与实际结果（并结合日志证据与日志检查工具的结论），判断操作是否成功（第 {idx}/{total} 步）。"
        # 判定口径：日志与截图两个条件缺一不可（检查工具未检测到就必须判 FAIL）
        text += (
            "\n判定口径（必须遵守）：**日志检测到 + 截图确认两个条件都满足才可判 PASS**；"
            "调用 check_device_log 检查断言涉及的日志关键词，**未检测到该关键词时必须判 FAIL**"
            "（并在 actual 里写明日志未检测到），MUST NOT 只凭截图判 PASS。"
        )
        if keyword_catalog:
            text += f"\n\n{keyword_catalog}\n"
        # 各字段的取值来源写清楚让模型照抄（取不到就留空串）
        text += (
            "\n输出时：click_timer 抄上面的点击前时间戳（本步没有点击就留空字符串）；"
            "logAssertionTimer 抄 check_device_log 返回的命中时间戳（未检测到就留空字符串）；"
            "logAssertionInfo 由平台按你的检查调用自动填；"
            "screenshot 抄本次截图工具返回的 screenshot_path。"
        )
        text += CHINESE_DEMAND
        content: list = [TextBlock(text=text)]
        if screenshot is not None:
            content.append(screenshot)
        return await self._execute(content)
