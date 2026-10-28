"""RAG Markdown 标题切块单测：不联网。"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.rag._document import Section

from engines.agents.rag.chunker import MarkdownHeadingChunker

pytestmark = [pytest.mark.unit]

SAMPLE = """# H717D Smart Ice Maker - 7.1 固件需求

## 1. 机器上电
- **上电自检**：产品在上电时自检

## 2. 制冰尺寸模式选择（SELECT）
- **模式循环**：Large / Medium / Small

## 3. 清洁模式（CLEAN）
- **开启条件**：清洁模式仅在待机状态下可开启，无断电记忆
- **开启清洁**：设备在待机状态下，点击清洁模式按键开启一键清洁模式
- **完成清洁**：完成清洁模式后蜂鸣3s提醒用户已完成清洁
- **取消清洁**：清洁中点击清洁模式按键或者电源按键关闭
- **清洁中缺水**：清洁模式下缺水持续蜂鸣5s后设备进入缺水状态

## 6. 缺水保护
- **上电缺水检测**：设备在上电状态下检测缺水
"""


@pytest.mark.asyncio
async def test_markdown_heading_chunker_keeps_section_three_intact():
    """## 3. 清洁模式 整段成块，不被 token 切碎。"""
    chunker = MarkdownHeadingChunker(
        parameters=MarkdownHeadingChunker.Parameters(chunk_size=400, overlap=60),
    )
    sections = [
        Section(content=TextBlock(text=SAMPLE), source="7_1.md", metadata={}),
    ]

    chunks = await chunker.chunk(sections)
    texts = [chunk.content.text for chunk in chunks]

    clean_chunks = [text for text in texts if "## 3. 清洁模式" in text]
    assert len(clean_chunks) == 1
    assert "开启条件" in clean_chunks[0]
    assert "清洁中缺水" in clean_chunks[0]
    assert "## 6. 缺水保护" not in clean_chunks[0]
    assert "H717D Smart Ice Maker" in clean_chunks[0]


@pytest.mark.asyncio
async def test_markdown_heading_chunker_splits_oversized_section():
    """单节超过 chunk_size 时回退 token 切分，并保留标题前缀。"""
    heading = "## 8. 预约定时"
    body = "\n".join([f"- 条款{i}：" + ("预约说明" * 40) for i in range(30)])
    text = f"# 文档标题\n\n{heading}\n{body}\n"
    chunker = MarkdownHeadingChunker(
        parameters=MarkdownHeadingChunker.Parameters(chunk_size=80, overlap=10),
    )
    sections = [Section(content=TextBlock(text=text), source="x.md", metadata={})]

    chunks = await chunker.chunk(sections)

    assert len(chunks) >= 2
    assert all("文档标题" in chunk.content.text for chunk in chunks)
