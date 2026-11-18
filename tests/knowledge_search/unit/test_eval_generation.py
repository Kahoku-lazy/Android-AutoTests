"""出题真实路径回归：UserMsg 块列表构造、pydantic 块文本提取、JSON 解析与端到端出题。

此前集成测试用替身出题函数，漏掉了 Msg content 校验与 TextBlock 对象形状两个真 bug；
本文件直接打真实构造路径（模型仍用替身，不联网）。
"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock, ThinkingBlock
from agentscope.model import ChatResponse

from backend.apps.knowledge_search.eval_generation import (
    _call,
    extract_text,
    generate_positive_questions,
    parse_json_payload,
)

pytestmark = [pytest.mark.unit]


class _CapturingModel:
    """替身聊天模型：记录收到的消息并返回预置响应。"""

    def __init__(self, response: ChatResponse) -> None:
        self.response = response
        self.seen: list = []

    async def __call__(self, messages, **kwargs):
        self.seen.append(messages)
        return self.response


def _text_response(text: str) -> ChatResponse:
    """造一条含 pydantic TextBlock 的响应（真实模型形状）。"""
    return ChatResponse(content=[TextBlock(text=text)], is_last=True)


async def test_call_builds_user_msg_with_block_list():
    """裸 str 提示经 UserMsg 归一成块列表，不再触发 Msg content 校验错误。"""
    model = _CapturingModel(_text_response("[]"))
    await _call(model, "你是评测题集生成器")
    messages = model.seen[0]
    assert len(messages) == 1
    msg = messages[0]
    assert msg.role == "user"
    assert isinstance(msg.content, list)
    assert msg.content[0].text == "你是评测题集生成器"


def test_extract_text_handles_pydantic_and_dict_blocks():
    """pydantic 对象块与 dict 块都能提取；thinking 块忽略。"""
    response = ChatResponse(
        content=[
            ThinkingBlock(thinking="想一想"),
            TextBlock(text="你好"),
            {"type": "text", "text": "世界"},
        ],
        is_last=True,
    )
    assert extract_text(response) == "你好世界"
    assert extract_text(ChatResponse(content=[], is_last=True)) == ""


def test_parse_json_payload_tolerates_fences():
    """代码围栏与裸 JSON 都能解析；坏文本返回 None。"""
    assert parse_json_payload('```json\n[{"i":0,"q":"问题"}]\n```') == [{"i": 0, "q": "问题"}]
    assert parse_json_payload('["a"]') == ["a"]
    assert parse_json_payload("不是 JSON") is None


async def test_generate_positive_questions_real_parse_path():
    """端到端出题：真实 UserMsg 构造 + pydantic 块提取 + JSON 映射 + 用量收集。"""
    payload = '[{"i":0,"q":"指示灯红色代表什么"},{"i":1,"q":"如何恢复出厂"}]'
    model = _CapturingModel(_text_response(payload))
    chunks = [
        {"source": "a.md", "relative_path": "a.md", "chunk_index": 0, "text": "红灯常亮表示缺水"},
        {"source": "b.md", "relative_path": "b.md", "chunk_index": 0, "text": "长按十秒恢复出厂"},
    ]
    questions, usages = await generate_positive_questions(
        model, chunks, api_key_env="DASHSCOPE_API_KEY", model_name="qwen-flash"
    )
    assert [item["question"] for item in questions] == ["指示灯红色代表什么", "如何恢复出厂"]
    assert questions[0]["chunk"]["source"] == "a.md"
    assert questions[1]["chunk"]["source"] == "b.md"
    assert usages == []  # 替身响应不带 usage，不产事件
    assert len(model.seen) == 1
