from __future__ import annotations

import uuid

from dataclasses import dataclass
from pathlib import Path

from utils.logs import backend_log

DOCUMENT_EXTENSIONS = {".md", ".markdown", ".docx", ".pdf", ".yaml", ".yml"}
CONFIG_EXTENSIONS = {".yaml", ".yml"}
TASK_ATTACHMENT_MAX_SIZE = 20 * 1024 * 1024
MAX_CASE_DOCUMENTS = 5


class AttachmentError(ValueError):
    pass


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


def _fallback_docx(path: str) -> str:
    from docx import Document

    document = Document(path)
    parts: list[str] = []
    for para in document.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue
        style = str(getattr(getattr(para, "style", None), "name", "") or "").lower()
        if style.startswith("heading"):
            digits = "".join(ch for ch in style if ch.isdigit())
            level = min(int(digits or 1), 6)
            parts.append(f"{'#' * level} {text}")
        else:
            parts.append(text)
    for table in document.tables:
        rows = [
            [(cell.text or "").strip().replace("\n", " ") for cell in row.cells]
            for row in table.rows
        ]
        rows = [row for row in rows if any(row)]
        if not rows:
            continue
        width = max(len(row) for row in rows)
        for row in rows:
            row.extend([""] * (width - len(row)))
        parts.append("| " + " | ".join(rows[0]) + " |")
        parts.append("|" + "---|" * width)
        for row in rows[1:]:
            parts.append("| " + " | ".join(row) + " |")
    return "\n\n".join(parts).strip()


def _fallback_pdf(path: str) -> str:
    import fitz

    document = fitz.open(path)
    parts: list[str] = []
    for page in document:
        text = (page.get_text() or "").strip()
        if text:
            parts.append(f"--- Page {page.number + 1} ---\n{text}")
    return "\n\n".join(parts).strip()


def _fallback_convert(path: str) -> str:
    ext = _suffix(Path(path).name)
    if ext == ".docx":
        return _fallback_docx(path)
    if ext == ".pdf":
        return _fallback_pdf(path)
    return ""


def convert_with_markitdown(path: str) -> str:
    from markitdown import MarkItDown

    markitdown_error: Exception | None = None
    try:
        result = MarkItDown().convert(path)
        text = str(getattr(result, "text_content", "") or "").strip()
        if text:
            return text
    except Exception as exc:
        markitdown_error = exc
        backend_log.warning("MarkItDown 解析失败，改用本地兜底: %s: %s", type(exc).__name__, exc)

    try:
        fallback = _fallback_convert(path)
    except Exception as exc:
        backend_log.exception("本地文档解析失败: %s", path)
        raise AttachmentError(f"文档解析失败: {exc}") from exc
    if fallback:
        return fallback
    if markitdown_error is not None:
        raise AttachmentError(f"文档解析失败: {markitdown_error}") from markitdown_error
    raise AttachmentError("文档解析失败: 没有可用文本")


def parse_document_bytes(filename: str, content: bytes) -> tuple[str, str]:
    _check_size(content)
    base = _safe_name(filename)
    ext = _suffix(base)
    if ext not in DOCUMENT_EXTENSIONS:
        raise AttachmentError("文档仅支持 Markdown、Word（.docx）、PDF 与 YAML")
    if ext in {".md", ".markdown", ".yaml", ".yml"}:
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
    if not configs:
        raise AttachmentError("需要一份 YAML 配置")
    if len(configs) != 1:
        raise AttachmentError("只能有一份配置")
    filename, content = _upload_pair(configs[0])
    _check_size(content)
    ext = _suffix(filename)
    if ext not in CONFIG_EXTENSIONS:
        raise AttachmentError("配置只支持 YAML（.yaml / .yml）")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AttachmentError("YAML 必须是 UTF-8") from exc
    prepared = [PreparedUpload(kind="config", filename=filename, body=text, content=content)]
    for item in documents:
        doc_name, doc_bytes = _upload_pair(item)
        markdown, safe = parse_document_bytes(doc_name, doc_bytes)
        prepared.append(
            PreparedUpload(kind="document", filename=safe, body=markdown, content=doc_bytes)
        )
    return prepared


def store_flat_upload(filename: str, content: bytes) -> str:
    from backend.apps.task_list.upload_cleanup import ensure_upload_dir

    root = ensure_upload_dir()
    target = root / f"{uuid.uuid4().hex}_{_safe_name(filename)}"
    target.write_bytes(content)
    return target.name


def validate_milestone_yaml(text: str) -> None:
    import yaml

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AttachmentError(f"不是合法 YAML：{exc}") from exc
    if isinstance(raw, list):
        raise AttachmentError("需要里程碑格式：顶层是 name 与 steps，不接受用例列表")
    if not isinstance(raw, dict):
        raise AttachmentError("需要里程碑格式：顶层必须是映射")
    if (
        not str(raw.get("name") or "").strip()
        or not isinstance(raw.get("steps"), list)
        or not raw["steps"]
    ):
        raise AttachmentError("需要里程碑格式：顶层要有非空 name 与非空 steps")
    for index, item in enumerate(raw["steps"], 1):
        if not isinstance(item, dict):
            raise AttachmentError(f"第 {index} 步必须是映射")
        if "action" in item or "assert" in item:
            raise AttachmentError(
                "需要里程碑格式：步骤使用 subject 与 description，不接受 action / assert"
            )
        if (
            not str(item.get("subject") or "").strip()
            or not str(item.get("description") or "").strip()
        ):
            raise AttachmentError(f"第 {index} 步缺少 subject 或 description")
        attempts = item.get("max_attempts", 3)
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
            raise AttachmentError(f"第 {index} 步的 max_attempts 必须是正整数")


def collect_milestone_file(configs: list) -> PreparedUpload:
    if not configs:
        raise AttachmentError("需要一份 YAML 配置")
    if len(configs) != 1:
        raise AttachmentError("只能有一份配置")
    filename, content = _upload_pair(configs[0])
    _check_size(content)
    if _suffix(filename) not in CONFIG_EXTENSIONS:
        raise AttachmentError("配置只支持 YAML（.yaml / .yml）")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AttachmentError("YAML 必须是 UTF-8") from exc
    validate_milestone_yaml(text)
    return PreparedUpload(kind="config", filename=filename, body=text, content=content)


def collect_document_files(documents: list) -> list[PreparedUpload]:
    if not documents:
        raise AttachmentError("请上传 PRD 或 Word 文档")
    if len(documents) > MAX_CASE_DOCUMENTS:
        raise AttachmentError(f"一次最多上传 {MAX_CASE_DOCUMENTS} 份文档")
    prepared: list[PreparedUpload] = []
    for item in documents:
        doc_name, doc_bytes = _upload_pair(item)
        markdown, safe = parse_document_bytes(doc_name, doc_bytes)
        prepared.append(
            PreparedUpload(kind="document", filename=safe, body=markdown, content=doc_bytes)
        )
    return prepared
