"""element-locator legacy 平铺端点 — 快照导入（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api

logger = logging.getLogger(__name__)

# ── 快照导入（v7.2：供设备检查器 / AI 保存工具调用）──


@csrf_exempt
def import_snapshot(request):
    """POST /api/elements/pages/import-snapshot — 快照导入（检查器 / AI 保存工具）。

    Body: { page_label, folder_path?, package?, activity?,
            ocr_json?, snapshot_id?, elements[] }

    不接受也不保存整屏截图（rework-save-to-elements）：`screenshot_path` 入参已移除。
    响应统一信封 {status, data} / {status, message}（新端点新契约）。
    """
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON 请求体"}, status=400)
    try:
        result = api.import_snapshot_page(
            page_label=(body.get("page_label") or "").strip(),
            folder_path=(body.get("folder_path") or "").strip(),
            package=body.get("package", ""),
            activity=body.get("activity", ""),
            ocr_json=body.get("ocr_json"),
            snapshot_id=body.get("snapshot_id"),
            elements=body.get("elements") or [],
        )
        return JsonResponse({"status": True, "data": result})
    except api.ImportConflictError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=409)
    except ValueError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=400)
    except Exception:
        logger.exception("import_snapshot failed")
        return JsonResponse({"status": False, "message": "导入失败"}, status=500)
