"""任务附件解析 — 配置 YAML 原样保留，文档转为 Markdown。"""

from __future__ import annotations

import uuid

from dataclasses import dataclass
from pathlib import Path

from utils.logs import backend_log

DOCUMENT_EXTENSIONS = {".md", ".docx", ".pdf"}
CONFIG_EXTENSIONS = {".yaml", ".yml"}
REJECTED_CONFIG_EXTENSIONS = {".csv", ".json"}
TASK_ATTACHMENT_MAX_SIZE = 20 * 1024 * 1024


class AttachmentError(ValueError):
    """用户可见的任务附件错误。"""


def _suffix(filename: str) -> str:
    return Path(str(filename or "")).suffix.lower()


def _safe_name(filename: str) -> str:
    raw = str(filename or "").replace("\\", "/").strip()
    base = Path(raw).name.strip()
    if not base or base in {".", ".."}:
        raise AttachmentError("非法文件名")
    return base


def _check_size(content: bytes) -> None:
    if len(content) > TASK_ATTACHMENT_MAX_SIZE:
        raise AttachmentError("文件过大")


def convert_with_markitdown(path: str) -> str:
    """用 MarkItDown 把 Word 或 PDF 转成 Markdown。"""
    from markitdown import MarkItDown

    result = MarkItDown().convert(path)
    text = str(getattr(result, "text_content", "") or "").strip()
    if not text:
        raise AttachmentError("文档解析失败: 没有可用文本")
    return text


def parse_document_bytes(filename: str, content: bytes) -> tuple[str, str]:
    """文档附件 → (markdown, 安全文件名)。失败抛 AttachmentError。"""
    _check_size(content)
    base = _safe_name(filename)
    ext = _suffix(base)
    if ext not in DOCUMENT_EXTENSIONS:
        raise AttachmentError("文档仅支持 Markdown、Word（.docx）与 PDF")
    if ext == ".md":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AttachmentError("Markdown 必须是 UTF-8") from exc
        return text, base
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        try:
            text = convert_with_markitdown(tmp_path)
        except AttachmentError:
            raise
        except Exception as exc:
            backend_log.exception("任务附件解析失败: %s", base)
            raise AttachmentError(f"文档解析失败: {exc}") from None
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return text, base


def parse_task_attachment_bytes(filename: str, content: bytes) -> tuple[str, str]:
    """兼容旧调用名，行为与 parse_document_bytes 相同。"""
    return parse_document_bytes(filename, content)


@dataclass(frozen=True)
class PreparedUpload:
    kind: str
    filename: str
    body: str
    content: bytes


def _upload_pair(item) -> tuple[str, bytes]:
    if hasattr(item, "read"):
        return _safe_name(getattr(item, "name", "") or "file"), item.read()
    filename, content = item
    return _safe_name(filename), content


def collect_task_files(configs: list, documents: list) -> list[PreparedUpload]:
    """检查一次提交的配置与文档。失败抛 AttachmentError。不写库、不落盘。"""
    from engines.agents.workflow.case_file import validate_platform_yaml

    if not configs:
        raise AttachmentError("需要一份 YAML 配置")
    if len(configs) != 1:
        raise AttachmentError("只能有一份配置")
    filename, content = _upload_pair(configs[0])
    _check_size(content)
    ext = _suffix(filename)
    if ext in REJECTED_CONFIG_EXTENSIONS:
        raise AttachmentError("csv 与 json 暂不可用")
    if ext not in CONFIG_EXTENSIONS:
        raise AttachmentError("配置只支持 YAML")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AttachmentError("YAML 必须是 UTF-8") from exc
    _cases, reason = validate_platform_yaml(text)
    if reason:
        raise AttachmentError(reason)
    prepared = [PreparedUpload(kind="config", filename=filename, body=text, content=content)]
    for item in documents:
        doc_name, doc_bytes = _upload_pair(item)
        markdown, safe = parse_document_bytes(doc_name, doc_bytes)
        prepared.append(
            PreparedUpload(kind="document", filename=safe, body=markdown, content=doc_bytes)
        )
    return prepared


def store_flat_upload(filename: str, content: bytes) -> str:
    """把原件写成上传目录第一层的文件，返回相对文件名。"""
    from apps.task_list.upload_cleanup import ensure_upload_dir

    root = ensure_upload_dir()
    target = root / f"{uuid.uuid4().hex}_{_safe_name(filename)}"
    target.write_bytes(content)
    return target.name
