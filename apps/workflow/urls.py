"""workflow URL routing under /api/workflow/ — 只有 router 一套端点。

历史包袱已收敛（变更 converge-workflow-http-endpoints）：原先还有一套 legacy 平铺视图
（`views.py` 的 13 个函数）与 router 并存，只有 `*/create/`、`documents/import/` 四条字面量
路径真的走 legacy，其余 9 条早被 router 覆盖。两套实现导致返回体有两种形状、URL 表必须手工
排序，并曾引发 `prototypes/create/` 被详情路由当成主键抢占的 405（变更
fix-workflow-create-route-shadowing）。现在创建走集合路由、导入走 router 动作路由
（`url_path="import"`），不再有第二套实现或平铺信封出口。
"""

from rest_framework.routers import DefaultRouter

from .views_api import (
    WorkflowDirectoryViewSet,
    WorkflowDocumentViewSet,
    WorkflowPrototypeViewSet,
)

app_name = "workflow"

router = DefaultRouter()
router.register(r"prototypes", WorkflowPrototypeViewSet, basename="wf_proto")
router.register(r"directories", WorkflowDirectoryViewSet, basename="wf_dir")
router.register(r"documents", WorkflowDocumentViewSet, basename="wf_doc")

urlpatterns = router.urls
