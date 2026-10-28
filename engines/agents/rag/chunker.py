"""
python -m 调试路径: engines.agents.rag.chunker

本模块的业务功能如下：
1. MarkdownHeadingChunker: 按 Markdown ##+ 标题边界切块，保留文档标题上下文。
2. 单段超过 chunk_size 时回退到近似 token 切分，并给子块带上标题前缀。
"""

from __future__ import annotations

import re

from bisect import bisect_right
from itertools import accumulate
from typing import Any

from agentscope.message import DataBlock, TextBlock
from agentscope.rag import Chunk, ChunkerBase
from agentscope.rag._document import Section
from pydantic import Field, model_validator

# 写入 index_state，策略变更时强制全量重建。
CHUNKER_VERSION: str = "markdown_heading_v1"

_HEADING_RE = re.compile(r"(?m)^(#{2,}\s+\S.*)$")
_DOC_TITLE_RE = re.compile(r"(?m)^(#{1}\s+\S.*)$")


class MarkdownHeadingChunker(ChunkerBase):
    """
    功能设计说明：按 Markdown ##+ 标题切块，避免功能小节被 token 切碎。

    Attributes:
        parameters: chunk_size / overlap（近似 token）。
    """

    chunker_type = "markdown_heading"

    class Parameters(ChunkerBase.Parameters):
        """Markdown 标题切块参数。"""

        chunk_size: int = Field(
            default=400,
            ge=1,
            title="Chunk Size",
            description="Maximum approximate tokens per chunk.",
        )
        overlap: int = Field(
            default=60,
            ge=0,
            title="Overlap",
            description="Overlap approximate tokens between token-split pieces.",
        )

        @model_validator(mode="after")
        def _overlap_less_than_chunk_size(
            self,
        ) -> "MarkdownHeadingChunker.Parameters":
            if self.overlap >= self.chunk_size:
                raise ValueError(
                    "overlap must be less than chunk_size, got "
                    f"overlap={self.overlap}, chunk_size={self.chunk_size}.",
                )
            return self

    def __init__(
        self,
        parameters: "MarkdownHeadingChunker.Parameters | None" = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化标题感知切块器。

        Args:
            parameters: chunk_size / overlap。
            **kwargs: 兼容旧写法的 chunk_size=/overlap=。

        Raises:
            TypeError: parameters 类型不正确。
            ValueError: overlap >= chunk_size。
        """
        if parameters is not None and not isinstance(parameters, self.Parameters):
            raise TypeError(
                "The first argument of MarkdownHeadingChunker must be a "
                "MarkdownHeadingChunker.Parameters instance, got "
                f"{type(parameters).__name__}.",
            )
        legacy = {
            key: kwargs[key]
            for key in ("chunk_size", "overlap")
            if key in kwargs
        }
        if legacy:
            base = parameters.model_dump() if parameters is not None else {}
            parameters = self.Parameters(**{**base, **legacy})
        super().__init__(parameters)

    @property
    def chunk_size(self) -> int:
        """每块最大近似 token 数。"""
        return self.parameters.chunk_size

    @property
    def overlap(self) -> int:
        """token 回退切分时的重叠近似 token 数。"""
        return self.parameters.overlap

    async def chunk(self, sections: list[Section]) -> list[Chunk]:
        """
        将 Sections 切成 Chunks：先按 ##+ 标题，再按近似 token。

        Args:
            sections: 解析器输出的文档片段。

        Returns:
            连续编号的 Chunk 列表。
        """
        chunks: list[Chunk] = []
        for section in sections:
            contents: list[TextBlock | DataBlock]
            if isinstance(section.content, TextBlock):
                contents = [
                    TextBlock(text=piece)
                    for piece in self._split_text(section.content.text)
                    if piece.strip()
                ]
            else:
                contents = [section.content]

            chunks.extend(
                Chunk(
                    content=content,
                    source=section.source,
                    chunk_index=0,
                    total_chunks=0,
                    metadata=dict(section.metadata),
                )
                for content in contents
            )

        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index
            chunk.total_chunks = len(chunks)
        return chunks

    def _split_text(self, text: str) -> list[str]:
        """
        按 ##+ 标题切分；过大段再按近似 token 切，并保留标题前缀。

        Args:
            text: 原始 Markdown 文本。

        Returns:
            非空文本块列表。
        """
        doc_title = _extract_doc_title(text)
        pieces: list[str] = []
        for segment in _split_by_headings(text):
            body = segment.strip("\n")
            if not body.strip():
                continue
            heading = _first_heading_line(body)
            if self._approx_count_tokens(body) <= self.chunk_size:
                pieces.append(_with_doc_title(body, doc_title))
                continue
            for part in self._split_by_tokens(body):
                part = part.strip("\n")
                if not part.strip():
                    continue
                pieces.append(_enrich_token_piece(part, doc_title, heading))
        return pieces

    def _split_by_tokens(self, text: str) -> list[str]:
        """按近似 token 窗口切分，带 overlap。"""
        if self._approx_count_tokens(text) <= self.chunk_size:
            return [text]

        byte_offsets = [0, *accumulate(len(c.encode("utf-8")) for c in text)]
        chunk_bytes = self.chunk_size * 4
        overlap_bytes = self.overlap * 4
        pieces: list[str] = []
        start = 0
        while start < len(text):
            end = bisect_right(byte_offsets, byte_offsets[start] + chunk_bytes) - 1
            end = max(end, start + 1)
            pieces.append(text[start:end])
            if end >= len(text):
                break
            next_start = (
                bisect_right(byte_offsets, byte_offsets[end] - overlap_bytes) - 1
            )
            start = max(next_start, start + 1)
        return pieces

    @staticmethod
    def _approx_count_tokens(text: str) -> int:
        """近似 token 数：UTF-8 字节数 // 4。"""
        return len(text.encode("utf-8")) // 4


def _extract_doc_title(text: str) -> str:
    """取文首一级标题行（# 标题），没有则空串。"""
    match = _DOC_TITLE_RE.search(text)
    if not match:
        return ""
    first_h2 = _HEADING_RE.search(text)
    if first_h2 and match.start() > first_h2.start():
        return ""
    return match.group(1).strip()


def _split_by_headings(text: str) -> list[str]:
    """
    在 ##+ 标题处切开；标题前的导言单独成段。

    Args:
        text: Markdown 全文。

    Returns:
        按标题分段的文本列表。
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [text] if text.strip() else []

    segments: list[str] = []
    preamble = text[: matches[0].start()]
    if preamble.strip():
        segments.append(preamble)

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segments.append(text[match.start() : end])
    return segments


def _first_heading_line(text: str) -> str:
    """返回段首 ##+ 标题行。"""
    match = _HEADING_RE.match(text.lstrip("\n"))
    return match.group(1).strip() if match else ""


def _with_doc_title(body: str, doc_title: str) -> str:
    """给非文档标题段补上一级标题，便于检索带型号的问题。"""
    if not doc_title:
        return body
    stripped = body.lstrip()
    if stripped.startswith(doc_title):
        return body
    if stripped.startswith("# ") and not stripped.startswith("##"):
        return body
    return f"{doc_title}\n\n{body}"


def _enrich_token_piece(part: str, doc_title: str, heading: str) -> str:
    """
    给 token 回退切出的子块补文档标题与小节标题。

    Args:
        part: 子块正文。
        doc_title: 文首 # 标题。
        heading: 本段 ##+ 标题行。

    Returns:
        补齐上下文后的文本。
    """
    stripped = part.lstrip()
    prefixes: list[str] = []
    if doc_title and not stripped.startswith(doc_title):
        prefixes.append(doc_title)
    if heading and heading not in stripped[: len(heading) + 8]:
        prefixes.append(heading)
    if not prefixes:
        return part
    return "\n\n".join([*prefixes, part])
