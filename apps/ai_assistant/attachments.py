"""任务附件解析 — Word / PDF 旁路转 Markdown（任务发布用，不落盘）。"""

from __future__ import annotations

import logging

from pathlib import Path

logger = logging.getLogger("ai_assistant")

TASK_ATTACHMENT_EXTENSIONS = {".docx", ".pdf"}
TASK_ATTACHMENT_MAX_SIZE = 20 * 1024 * 1024  # 20MB，与通用上传对齐


class AttachmentError(ValueError):
    """用户可见的任务附件错误。"""


def parse_docx_to_markdown(filepath: str) -> str:
    """Word → Markdown 文本（段落拼接）。"""
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_pdf_to_markdown(filepath: str) -> str:
    """PDF → Markdown 文本（按页加二级标题）。"""
    import fitz

    pdf = fitz.open(filepath)
    parts = []
    for page in pdf:
        text = page.get_text()
        if text.strip():
            parts.append(f"## 第 {page.number + 1} 页\n\n{text.strip()}")
    return "\n\n".join(parts) if parts else "（PDF 无可用文本）"


def parse_task_attachment_bytes(filename: str, content: bytes) -> tuple[str, str]:
    """任务附件：仅 .docx/.pdf → (markdown, 安全文件名)。失败抛 AttachmentError。"""
    if len(content) > TASK_ATTACHMENT_MAX_SIZE:
        raise AttachmentError("文件过大")
    raw = str(filename or "").replace("\\", "/").strip()
    base = Path(raw).name.strip()
    if not base or base in {".", ".."}:
        raise AttachmentError("非法文件名")
    ext = Path(base).suffix.lower()
    if ext not in TASK_ATTACHMENT_EXTENSIONS:
        raise AttachmentError("仅支持 Word（.docx）与 PDF")
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        try:
            md = (
                parse_pdf_to_markdown(tmp_path)
                if ext == ".pdf"
                else parse_docx_to_markdown(tmp_path)
            )
        except AttachmentError:
            raise
        except Exception as exc:
            logger.exception("任务附件解析失败: %s", base)
            raise AttachmentError(f"文档解析失败: {exc}") from None
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return md, base
