"""case-manager HTTP views — facade re-exporting from sub-modules."""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from models.step_types import get_step_types_by_target

# Directory endpoints
from .views_directories import (  # noqa: E402, F401
    directory_batch_move,
    directory_create,
    directory_detail,
    directory_list,
    directory_permission,
)

# Shared helper (no circular deps)
from .views_helpers import resolve_username as _resolve_username  # noqa: F401 — compat alias

# Lock & visibility endpoints
from .views_lock import (  # noqa: E402, F401
    acquire_edit_lock,
    case_lock,
    case_unlock,
    release_edit_lock,
    set_visibility,
)

# UI automation endpoints
from .views_ui import (  # noqa: E402, F401
    definition_detail,
    definitions_batch,
    definitions_handler,
    download_export,
    export_yaml,
    list_exports,
)

# ── 操作类型查询（全平台统一入口）──


@csrf_exempt
def list_step_types(request):
    """GET /api/cases/step-types?target=android|web|api
    返回指定平台可用的所有操作类型。前端 StepEditor 由此拉取步骤列表。
    """
    target = request.GET.get("target", "android")
    types = get_step_types_by_target(target)
    return JsonResponse({"status": True, "data": {"types": types}})
