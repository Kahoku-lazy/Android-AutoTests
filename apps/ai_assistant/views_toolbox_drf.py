"""ai-assistant DRF views — 工具箱（Batch 3 迁移）。

路径与方法保持旧契约不变（等行为迁移）：
  GET  /api/ai/toolbox                          共享工具箱列表（含 enabled 状态）
  POST /api/ai/toolbox/create                   新增 mcp/extension 项
  POST /api/ai/toolbox/{id}/update              更新
  POST /api/ai/toolbox/{id}/delete              删除（skill 同步清目录）
  POST /api/ai/toolbox/{id}/toggle              启停（直接决定平台唯一智能体是否使用）
  POST /api/ai/toolbox/upload-skill             上传共享 skill 文件夹

写库全部经 api.py。平台唯一智能体：MCP/Skill 直接启用/停用，无 per-agent 副本与导入。
"""

import json
import logging
import os

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response

from . import api
from .models import AISharedTool

logger = logging.getLogger("ai_assistant")


class Conflict(APIException):
    """409 冲突（DRF 无内置，项目多处沿用旧契约 409 语义）。"""

    status_code = 409
    default_detail = "Conflict"
    default_code = "conflict"


# Shared skill uploads land in data/shared_skills/{tool_id}/
_SHARED_SKILLS_DIR = os.path.join("data", "shared_skills")
_SHARED_SKILL_MAX_MB = 50
_SKILL_EXTENSIONS = {
    ".py",
    ".sh",
    ".bash",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".markdown",
    ".txt",
    ".toml",
    ".cfg",
    ".ini",
    ".env",
}


def _detect_skill_features(file_names: list[str]) -> str:
    """Return a human-readable summary of file types in a skill folder."""
    exts: dict[str, int] = {}
    has_cli = False
    for name in file_names:
        _, ext = os.path.splitext(name)
        if ext:
            ext = ext.lower()
            exts[ext] = exts.get(ext, 0) + 1
        if ext in (".sh", ".bash", ".py") or name in ("run", "start", "main"):
            has_cli = True
    parts = []
    for ext in sorted(exts):
        label = ext.lstrip(".").upper()
        parts.append(f"{label}: {exts[ext]}")
    if has_cli:
        parts.insert(0, "1 CLI tool")
    return ", ".join(parts) if parts else "Unknown"


# ═══════════════════════════════════════════════════════════════════
# 共享工具箱 ViewSet
# ═══════════════════════════════════════════════════════════════════


class ToolboxViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """AI 工具箱（全局共享，无 owner 概念 — 与旧实现一致）。"""

    queryset = AISharedTool.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        items = AISharedTool.objects.order_by("-updated_at")
        return Response(
            {
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "item_type": item.item_type,
                        "description": item.description,
                        "config_json": item.config_json,
                        "enabled": item.enabled,
                        "created_at": str(item.created_at),
                    }
                    for item in items
                ]
            }
        )

    @action(detail=False, methods=["post"], url_path="create")
    def create_item(self, request, *args, **kwargs):
        name = (request.data.get("name") or "").strip()
        if not name:
            raise ValidationError("name is required")

        item_type = (request.data.get("item_type") or "").strip()
        if item_type not in ("mcp", "extension"):
            raise ValidationError("item_type must be 'mcp' or 'extension'")

        config_json = request.data.get("config_json", "{}")
        if isinstance(config_json, dict):
            config_json = json.dumps(config_json)

        item = api.create_shared_tool(
            name=name,
            item_type=item_type,
            description=request.data.get("description", ""),
            config_json=config_json,
        )
        return Response({"id": item.id})

    @action(detail=True, methods=["post"], url_path="update")
    def update_item(self, request, *args, **kwargs):
        item_id = kwargs.get("pk", "")
        try:
            item = AISharedTool.objects.get(id=int(item_id))
        except (ValueError, AISharedTool.DoesNotExist):
            raise NotFound("not found")

        name = None
        description = None
        config_json = None
        if "name" in request.data:
            name = request.data["name"].strip()
        if "description" in request.data:
            description = request.data["description"]
        if "config_json" in request.data:
            cfg = request.data["config_json"]
            config_json = json.dumps(cfg) if isinstance(cfg, dict) else cfg

        api.update_shared_tool(item, name, description, config_json)
        return Response({})

    @action(detail=True, methods=["post"], url_path="delete")
    def delete_item(self, request, *args, **kwargs):
        item_id = kwargs.get("pk", "")
        try:
            item = AISharedTool.objects.get(id=int(item_id))
        except (ValueError, AISharedTool.DoesNotExist):
            raise NotFound("not found")
        api.delete_shared_tool(item)
        return Response({})

    @action(detail=True, methods=["post"], url_path="toggle")
    def toggle_item(self, request, *args, **kwargs):
        item_id = kwargs.get("pk", "")
        try:
            item = AISharedTool.objects.get(id=int(item_id))
        except (ValueError, AISharedTool.DoesNotExist):
            raise NotFound("not found")
        enabled = bool(request.data.get("enabled", True))
        api.set_shared_tool_enabled(item, enabled)
        return Response({"enabled": item.enabled})

    @action(detail=False, methods=["post"], url_path="upload-skill")
    def upload_skill(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")
        skill_name = (request.data.get("name") or "").strip()
        if not files:
            raise ValidationError("no files uploaded")
        if not skill_name:
            raise ValidationError("name is required")

        # Validate files
        total_size = 0
        file_names = []
        for f in files:
            if ".." in f.name or f.name.startswith("/"):
                raise ValidationError(f"非法文件名: {f.name}")
            _, ext = os.path.splitext(f.name)
            if ext.lower() not in _SKILL_EXTENSIONS:
                raise ValidationError(f"不支持的文件类型: {ext or '无后缀'}")
            total_size += f.size
            file_names.append(f.name)

        size_mb = total_size / (1024 * 1024)
        if size_mb > _SHARED_SKILL_MAX_MB:
            raise ValidationError(f"总大小 {size_mb:.1f}MB 超过 {_SHARED_SKILL_MAX_MB}MB 限制")

        # Create DB record first (so we have an ID for the directory)
        features = _detect_skill_features(file_names)
        item = api.create_shared_skill(skill_name, len(files), total_size, features)

        # Save files to data/shared_skills/{id}/
        skill_dir = os.path.join(_SHARED_SKILLS_DIR, str(item.id))
        os.makedirs(skill_dir, exist_ok=True)
        for f in files:
            dest = os.path.join(skill_dir, f.name)
            os.makedirs(os.path.dirname(dest) or skill_dir, exist_ok=True)
            with open(dest, "wb") as dst:
                for chunk in f.chunks():
                    dst.write(chunk)

        return Response({"id": item.id})
