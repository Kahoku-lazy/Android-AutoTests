"""element_locator DRF ViewSets — WebGroup, ApiGroup, WebElement, ApiEndpoint, flows.

Page tree + Page elements (device-dependent, complex validation) remain
as plain Django views in views_pages.py / views_page_elements.py.
"""

from django.db import models as db_models
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from . import api
from .models import (
    ApiEndpoint,
    ApiGroup,
    PageFlow,
    WebElement,
    WebGroup,
    WebPageFlow,
)
from .serializers import (
    ApiEndpointSerializer,
    ApiGroupSerializer,
    PageFlowSerializer,
    WebElementSerializer,
    WebGroupSerializer,
    WebPageFlowSerializer,
)

# ═══════════════════════════════════════════════════════
# WebGroup ViewSet
# ═══════════════════════════════════════════════════════


class GroupWriteRetired(APIException):
    """分组树写接口已停用 —— 产品决策：所有写操作一律 410 Gone。

    必须覆盖 create/update/partial_update/destroy **本身**，而不是 perform_* 钩子：
    perform_* 在序列化校验之后才跑，空 body 会先变成 400，就丢掉了"接口已停用"的语义。
    """

    status_code = 410
    default_detail = "分组树写接口已停用，请改用项目目录 API"


class GroupWriteRetiredMixin:
    """分组树的写操作一律 410（list / retrieve 不受影响）。"""

    def create(self, request, *args, **kwargs):
        raise GroupWriteRetired()

    def update(self, request, *args, **kwargs):
        raise GroupWriteRetired()

    def partial_update(self, request, *args, **kwargs):
        raise GroupWriteRetired()

    def destroy(self, request, *args, **kwargs):
        raise GroupWriteRetired()


class WebGroupViewSet(GroupWriteRetiredMixin, viewsets.ModelViewSet):
    """Web element grouping tree — 只读 + batch-move 410."""

    serializer_class = WebGroupSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return WebGroup.objects.prefetch_related("children").order_by("sort_order", "id")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(parent__isnull=True)
        return Response(WebGroupSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="batch-move")
    def batch_move(self, request):
        """POST /web-groups/batch-move/ — retired."""
        return Response(
            {"message": "分组树写接口已停用，请改用项目目录 API"},
            status=410,
        )


# ═══════════════════════════════════════════════════════
# WebElement ViewSet
# ═══════════════════════════════════════════════════════


class WebElementViewSet(viewsets.ModelViewSet):
    """Web element CRUD — list with filters, batch import."""

    serializer_class = WebElementSerializer

    def get_queryset(self):
        qs = WebElement.objects.select_related("group").order_by("-updated_at")
        search = self.request.query_params.get("search")
        locator_type = self.request.query_params.get("locator_type")
        page_url = self.request.query_params.get("page_url")
        is_test_point = self.request.query_params.get("is_test_point")
        group_id = self.request.query_params.get("group_id")

        if search:
            qs = qs.filter(
                db_models.Q(name__icontains=search) | db_models.Q(locator_value__icontains=search)
            )
        if locator_type:
            qs = qs.filter(locator_type=locator_type)
        if page_url:
            qs = qs.filter(page_url=page_url)
        if is_test_point is not None:
            qs = qs.filter(is_test_point=is_test_point.lower() in ("true", "1", "yes"))
        if group_id and group_id.isdigit():
            qs = qs.filter(group_id=int(group_id))

        return qs

    def perform_update(self, serializer):
        # 写库经 api.py（D3 契约）；api 不返回 ORM，故按 id 只读回取
        instance = serializer.instance
        api.update_web_element(instance.id, dict(serializer.validated_data))
        serializer.instance = WebElement.objects.get(id=instance.id)

    @action(detail=False, methods=["post"], url_path="batch")
    def batch_import(self, request):
        """POST /web/batch/ — batch import web elements."""
        items = request.data if isinstance(request.data, list) else request.data.get("items", [])
        if not items:
            return Response({"message": "items is required"}, status=400)

        created = 0
        for item in items:
            group_id = item.get("group_id")
            group = None
            if group_id:
                try:
                    group = WebGroup.objects.get(id=group_id)
                except WebGroup.DoesNotExist:
                    continue
            api.create_web_element(
                group,
                item.get("name", ""),
                item.get("locator_type", "css_selector"),
                item.get("locator_value", ""),
                page_url=item.get("page_url", ""),
                description=item.get("description", ""),
                is_test_point=item.get("is_test_point", False),
            )
            created += 1

        return Response({"created": created})


# ═══════════════════════════════════════════════════════
# ApiGroup ViewSet
# ═══════════════════════════════════════════════════════


class ApiGroupViewSet(GroupWriteRetiredMixin, viewsets.ModelViewSet):
    """API endpoint grouping tree — 只读 + batch-move 410."""

    serializer_class = ApiGroupSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return ApiGroup.objects.prefetch_related("children").order_by("sort_order", "id")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(parent__isnull=True)
        return Response(ApiGroupSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="batch-move")
    def batch_move(self, request):
        return Response(
            {"message": "分组树写接口已停用，请改用项目目录 API"},
            status=410,
        )


# ═══════════════════════════════════════════════════════
# ApiEndpoint ViewSet
# ═══════════════════════════════════════════════════════


class ApiEndpointViewSet(viewsets.ModelViewSet):
    """API endpoint CRUD — list with filters."""

    serializer_class = ApiEndpointSerializer

    def get_queryset(self):
        qs = ApiEndpoint.objects.select_related("group").order_by("-updated_at")
        search = self.request.query_params.get("search")
        method = self.request.query_params.get("method")
        is_test_point = self.request.query_params.get("is_test_point")
        group_id = self.request.query_params.get("group_id")

        if search:
            qs = qs.filter(db_models.Q(name__icontains=search) | db_models.Q(url__icontains=search))
        if method:
            qs = qs.filter(method=method.upper())
        if is_test_point is not None:
            qs = qs.filter(is_test_point=is_test_point.lower() in ("true", "1", "yes"))
        if group_id and group_id.isdigit():
            qs = qs.filter(group_id=int(group_id))

        return qs


# ═══════════════════════════════════════════════════════
# PageFlow ViewSet (Android)
# ═══════════════════════════════════════════════════════


class PageFlowViewSet(viewsets.ModelViewSet):
    """Android page navigation flow — list + create + destroy."""

    serializer_class = PageFlowSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return PageFlow.objects.select_related("from_page", "to_page", "trigger_element").order_by(
            "-created_at"
        )


# ═══════════════════════════════════════════════════════
# WebPageFlow ViewSet
# ═══════════════════════════════════════════════════════


class WebPageFlowViewSet(viewsets.ModelViewSet):
    """Web page navigation flow — list + create + destroy."""

    serializer_class = WebPageFlowSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return WebPageFlow.objects.select_related("from_group", "to_group").order_by("-created_at")

    def perform_create(self, serializer):
        data = serializer.validated_data
        from_group = WebGroup.objects.filter(pk=data.get("from_group_id")).first()
        to_group = WebGroup.objects.filter(pk=data.get("to_group_id")).first()
        if from_group and from_group.is_folder:
            raise ValidationError({"from_group_id": "源节点不能是目录"})
        if to_group and to_group.is_folder:
            raise ValidationError({"to_group_id": "目标节点不能是目录"})
        # 写库经 api.py（D3 契约）；api 不返回 ORM，故按 id 只读回取
        result = api.create_web_page_flow(
            from_group,
            to_group,
            trigger_element_id=data.get("trigger_element_id"),
            trigger_action=data.get("trigger_action", "click"),
        )
        serializer.instance = WebPageFlow.objects.get(id=result["id"])
