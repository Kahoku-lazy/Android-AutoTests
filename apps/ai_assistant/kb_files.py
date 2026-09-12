"""知识库文件目录 — data/rag_datas 列表 / 上传 / 预览（Word·PDF 旁路转 md）。"""

from __future__ import annotations

import logging
import re

from pathlib import Path

from django.conf import settings

logger = logging.getLogger("ai_assistant")

RAG_DATAS_DIR = Path(settings.BASE_DIR) / "data" / "rag_datas"

LIST_EXTENSIONS = {".md", ".markdown", ".txt", ".docx", ".pdf"}
TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024

_TYPE_BY_FOLDER = {
    "项目文档": "project_doc",
    "参考": "reference",
    "手动": "manual",
}

_UNSAFE_NAME = re.compile(r'[<>:"|?*]')


class KbFileError(ValueError):
    """用户可见的知识库文件错误。"""


def _ensure_root() -> Path:
    RAG_DATAS_DIR.mkdir(parents=True, exist_ok=True)
    return RAG_DATAS_DIR.resolve()


def _rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_resolve(rel_path: str) -> Path:
    root = _ensure_root()
    raw = (rel_path or "").replace("\\", "/").strip().lstrip("/")
    if not raw or ".." in Path(raw).parts or raw.startswith("/"):
        raise KbFileError("非法文件路径")
    target = (root / raw).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise KbFileError("非法文件路径") from exc
    return target


def _folder_type(rel: str) -> str:
    first = rel.split("/", 1)[0]
    return _TYPE_BY_FOLDER.get(first, "")


def _unique_dest(root: Path, name: str) -> Path:
    dest = root / name
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    n = 1
    while True:
        cand = root / f"{stem}_{n}{suffix}"
        if not cand.exists():
            return cand
        n += 1


def _sanitize_filename(name: str) -> str:
    raw = str(name).replace("\\", "/").strip()
    if not raw or "/" in raw or ".." in raw:
        raise KbFileError("非法文件名")
    base = _UNSAFE_NAME.sub("_", Path(raw).name.strip())
    if not base or base in {".", ".."}:
        raise KbFileError("非法文件名")
    ext = Path(base).suffix.lower()
    if ext not in LIST_EXTENSIONS:
        raise KbFileError("不支持的文件类型")
    return base


def list_rag_files() -> list[dict]:
    """扫描 data/rag_datas，返回前端树所需字段。"""
    root = _ensure_root()
    docs: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in LIST_EXTENSIONS:
            continue
        rel = _rel_posix(path, root)
        docs.append(
            {
                "id": rel,
                "name": path.name,
                "source": rel,
                "type": _folder_type(rel),
                "size": path.stat().st_size,
                "ext": path.suffix.lower().lstrip("."),
            }
        )
    return docs


def save_upload(filename: str, content: bytes, subdir: str = "") -> dict:
    """把上传文件写入 data/rag_datas（可选一级子目录）。"""
    if len(content) > MAX_UPLOAD_SIZE:
        raise KbFileError("文件过大")
    name = _sanitize_filename(filename)
    root = _ensure_root()
    dest_dir = root
    if subdir:
        folder = Path(str(subdir).replace("\\", "/")).name.strip()
        if folder not in _TYPE_BY_FOLDER:
            raise KbFileError("不支持的目标目录")
        dest_dir = root / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, name)
    dest.write_bytes(content)
    rel = _rel_posix(dest, root)
    return {
        "id": rel,
        "name": dest.name,
        "source": rel,
        "type": _folder_type(rel),
        "size": dest.stat().st_size,
        "ext": dest.suffix.lower().lstrip("."),
    }


def _parse_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _parse_pdf(filepath: str) -> str:
    import fitz

    pdf = fitz.open(filepath)
    parts = []
    for page in pdf:
        text = page.get_text()
        if text.strip():
            parts.append(f"## 第 {page.number + 1} 页\n\n{text.strip()}")
    return "\n\n".join(parts) if parts else "（PDF 无可用文本）"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def preview_document(rel_path: str) -> dict:
    """预览：md/txt 原文；docx/pdf 转成同名 .md（已有则直接读）。"""
    path = _safe_resolve(rel_path)
    if not path.is_file():
        raise KbFileError("找不到该文档")
    ext = path.suffix.lower()
    if ext not in LIST_EXTENSIONS:
        raise KbFileError("不支持预览该类型")

    if ext in TEXT_EXTENSIONS:
        kind = "markdown" if ext in {".md", ".markdown"} else "text"
        return {
            "path": _rel_posix(path, _ensure_root()),
            "name": path.name,
            "kind": kind,
            "content": _read_text(path),
            "converted": False,
        }

    sibling = path.with_suffix(".md")
    converted = False
    if sibling.is_file():
        content = _read_text(sibling)
    else:
        try:
            content = _parse_pdf(str(path)) if ext == ".pdf" else _parse_docx(str(path))
        except Exception:
            logger.exception("知识库文档转换失败: %s", path.name)
            raise KbFileError("文档转换失败") from None
        sibling.write_text(content, encoding="utf-8")
        converted = True

    return {
        "path": _rel_posix(sibling, _ensure_root()),
        "name": sibling.name,
        "kind": "markdown",
        "content": content,
        "converted": converted,
    }
