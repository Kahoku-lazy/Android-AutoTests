"""File upload endpoints — avatars and chat attachments."""

import base64
import json
import logging
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..decorators import require_auth
from ..upload_cleanup import ensure_upload_dir, remove_upload_file

logger = logging.getLogger("ai_assistant")

UPLOAD_DIR = ensure_upload_dir()

ALLOWED_EXTENSIONS = {
    "txt",
    "log",
    "md",
    "markdown",
    "json",
    "xml",
    "csv",
    "py",
    "js",
    "html",
    "css",
    "yaml",
    "yml",
    "docx",
    "xlsx",
    "pdf",
}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB


def _parse_docx(filepath: str) -> str:
    try:
        from docx import Document

        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX parse error: {e}]"


def _parse_xlsx(filepath: str) -> str:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(filepath, data_only=True)
        parts = []
        for name in wb.sheetnames:
            ws = wb[name]
            parts.append(f"--- Sheet: {name} ---")
            for row in ws.iter_rows(values_only=True):
                parts.append("\t".join(str(c) if c is not None else "" for c in row))
        return "\n".join(parts)
    except Exception as e:
        return f"[XLSX parse error: {e}]"


def _parse_pdf(filepath: str) -> str:
    try:
        import fitz

        doc = fitz.open(filepath)
        parts = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                parts.append(f"--- Page {page.number + 1} ---\n{text}")
        return "\n".join(parts) if parts else "[PDF has no extractable text]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def _parse_markdown(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[MD parse error: {e}]"


@csrf_exempt
@require_auth
def upload_avatar(request):
    """Upload an avatar image and return a data URI stored directly in the DB.

    Avatars are stored as data URIs (data:image/png;base64,...) in the
    AIAgent.avatar field so they travel with the database — no disk files
    that can get lost between environments.
    """
    try:
        data = json.loads(request.body)
        img_b64 = data.get("image", "")
        if not img_b64:
            return JsonResponse({"ok": False, "error": "no image data"})
        # Normalise: strip the data: prefix if present, so we can prepend our own
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        # Validate that it's actually decodable base64
        base64.b64decode(img_b64)
        data_uri = f"data:image/png;base64,{img_b64}"
        return JsonResponse({"ok": True, "url": data_uri})
    except Exception:
        logger.exception("Avatar upload failed")
        return JsonResponse({"ok": False, "error": "头像上传失败，请重试"}, status=500)


@csrf_exempt
@require_auth
def upload_and_parse_file(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"ok": False, "error": "No file uploaded"}, status=400)

    ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse(
            {
                "ok": False,
                "error": f"Unsupported file type: .{ext}. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            },
            status=400,
        )

    if uploaded.size > MAX_UPLOAD_SIZE:
        return JsonResponse(
            {
                "ok": False,
                "error": f"File too large ({uploaded.size} bytes). Max: {MAX_UPLOAD_SIZE} bytes",
            },
            status=400,
        )

    saved_name = f"{uuid.uuid4().hex}_{uploaded.name}"
    filepath = UPLOAD_DIR / saved_name
    try:
        with open(filepath, "wb") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        text_extensions = {
            "txt",
            "log",
            "json",
            "xml",
            "csv",
            "py",
            "js",
            "html",
            "css",
            "yaml",
            "yml",
        }
        content = ""
        parse_error = None

        try:
            if ext in text_extensions:
                content = open(filepath, "r", encoding="utf-8", errors="replace").read()
            elif ext in ("md", "markdown"):
                content = _parse_markdown(str(filepath))
            elif ext == "docx":
                content = _parse_docx(str(filepath))
            elif ext == "xlsx":
                content = _parse_xlsx(str(filepath))
            elif ext == "pdf":
                content = _parse_pdf(str(filepath))
        except Exception as e:
            parse_error = str(e)
            content = f"[Parse error: {e}]"

        if len(content) > 50000:
            content = content[:50000] + f"\n\n[... truncated {len(content) - 50000} chars]"

        return JsonResponse(
            {
                "ok": True,
                "data": {
                    "filename": uploaded.name,
                    "size": uploaded.size,
                    "type": ext,
                    "content": content,
                    "preview": content[:300] + ("..." if len(content) > 300 else ""),
                    "error": parse_error,
                },
            }
        )
    finally:
        remove_upload_file(filepath)
