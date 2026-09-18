"""element-locator URL routing —— DRF router 是 web / web-groups / api-groups /
api-endpoints / flows / web-flows 的**唯一实现**。

此前同一资源被注册两遍（router + 同名 legacy 手写路由），靠「无尾斜杠走 legacy /
带尾斜杠走 router」同时存活 —— 两套实现返回的信封形状还不一样。随着
`api-path-convention` 统一尾斜杠，这种遮蔽关系无法继续，legacy 版本已删除。

仍保留手写路由的只有确实没有 router 对应的路径：move / files / pages / items。
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import (
    ApiEndpointViewSet,
    ApiGroupViewSet,
    PageFlowViewSet,
    WebElementViewSet,
    WebGroupViewSet,
    WebPageFlowViewSet,
)
from .views_page_element_batch import batch_add_elements
from .views_page_elements import (
    add_element_to_page,
    page_elements,
    update_element,
)
from .views_pages import clear_pages, create_page, list_pages, page_detail, pages_batch_move
from .views_projects_drf import (
    LocatorDirectoryViewSet,
    LocatorProjectViewSet,
    batch_delete_files,
    move_items,
)
from .views_snapshot import import_snapshot

app_name = "elements"

# ── DRF router ──
router = DefaultRouter()
router.register(r"projects", LocatorProjectViewSet, basename="el_project")
router.register(r"directories", LocatorDirectoryViewSet, basename="el_directory")
router.register(r"web-groups", WebGroupViewSet, basename="el_web_group")
router.register(r"web", WebElementViewSet, basename="el_web_el")
router.register(r"api-groups", ApiGroupViewSet, basename="el_api_group")
router.register(r"api-endpoints", ApiEndpointViewSet, basename="el_api_ep")
router.register(r"flows", PageFlowViewSet, basename="el_flow")
router.register(r"web-flows", WebPageFlowViewSet, basename="el_web_flow")

urlpatterns = [
    path("move/", move_items, name="el_move"),
    path("files/batch-delete/", batch_delete_files, name="el_files_batch_delete"),
    # pages / items 没有 router 对应，保留手写实现
    path("pages/", list_pages, name="pages_list"),
    path("pages/create/", create_page, name="page_create"),
    path("pages/import-snapshot/", import_snapshot, name="pages_import_snapshot"),
    path("pages/clear/", clear_pages, name="pages_clear"),
    path("pages/batch-move/", pages_batch_move, name="pages_batch_move"),
    path("pages/<int:page_id>/", page_detail, name="page_detail"),
    path("pages/<int:page_id>/items/", page_elements, name="page_items"),
    path("pages/<int:page_id>/elements/", add_element_to_page, name="page_add_element"),
    path("pages/<int:page_id>/elements/batch/", batch_add_elements, name="page_batch_add_elements"),
    path("items/<int:el_id>/", update_element, name="item_update"),
]

urlpatterns = router.urls + urlpatterns
