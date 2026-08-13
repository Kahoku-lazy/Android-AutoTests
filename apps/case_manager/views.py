"""case-manager HTTP views — step-type query entry point."""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from models.step_types import get_step_types_by_target


@csrf_exempt
def list_step_types(request):
    """GET /api/cases/step-types?target=android|web|api
    返回指定平台可用的所有操作类型。前端 StepEditor 由此拉取步骤列表。
    """
    target = request.GET.get("target", "android")
    types = get_step_types_by_target(target)
    return JsonResponse({"status": True, "data": {"types": types}})
