"""element-locator URL routing — 11 endpoints under /api/elements/."""

from django.urls import path

from .views import (
    add_element_to_page,
    api_endpoint_detail,
    api_group_detail,
    batch_add_elements,
    batch_import_web_elements,
    batch_move_api_groups,
    batch_move_web_groups,
    clear_pages,
    create_api_endpoint,
    create_api_group,
    create_page,
    create_web_element,
    create_web_group,
    delete_flow,
    delete_web_flow,
    device_info_view,
    do_action,
    dump_page,
    flows_handler,
    list_api_endpoints,
    list_api_groups,
    list_pages,
    list_web_elements,
    list_web_groups,
    page_detail,
    page_elements,
    pages_batch_move,
    screenshot_snapshot,
    update_element,
    web_element_detail,
    web_flows_handler,
    web_group_detail,
)

app_name = "elements"

urlpatterns = [
    path("dump", dump_page, name="dump"),
    path("action", do_action, name="action"),
    path("device-info", device_info_view, name="device_info"),
    path("screenshot", screenshot_snapshot, name="screenshot"),
    path("pages", list_pages, name="pages_list"),
    path("pages/create", create_page, name="page_create"),
    path("pages/clear", clear_pages, name="pages_clear"),
    path("pages/batch-move", pages_batch_move, name="pages_batch_move"),
    path("pages/<int:page_id>", page_detail, name="page_detail"),
    path("pages/<int:page_id>/items", page_elements, name="page_items"),
    path("pages/<int:page_id>/elements", add_element_to_page, name="page_add_element"),
    path("pages/<int:page_id>/elements/batch", batch_add_elements, name="page_batch_add_elements"),
    path("items/<int:el_id>", update_element, name="item_update"),
    path("flows", flows_handler, name="flows"),
    path("flows/<int:flow_id>", delete_flow, name="flow_delete"),
    # Web element management
    path("web", list_web_elements, name="web_elements_list"),
    path("web/create", create_web_element, name="web_element_create"),
    path("web/batch", batch_import_web_elements, name="web_elements_batch"),
    path("web/<int:el_id>", web_element_detail, name="web_element_detail"),
    # Web group management
    path("web-groups", list_web_groups, name="web_groups_list"),
    path("web-groups/create", create_web_group, name="web_group_create"),
    path("web-groups/batch-move", batch_move_web_groups, name="web_groups_batch_move"),
    path("web-groups/<int:group_id>", web_group_detail, name="web_group_detail"),
    # Web page flows
    path("web-flows", web_flows_handler, name="web_flows_list"),
    path("web-flows/<int:flow_id>", delete_web_flow, name="web_flow_delete"),
    # API group management
    path("api-groups", list_api_groups, name="api_groups_list"),
    path("api-groups/create", create_api_group, name="api_group_create"),
    path("api-groups/batch-move", batch_move_api_groups, name="api_groups_batch_move"),
    path("api-groups/<int:group_id>", api_group_detail, name="api_group_detail"),
    # API endpoints
    path("api-endpoints", list_api_endpoints, name="api_endpoints_list"),
    path("api-endpoints/create", create_api_endpoint, name="api_endpoint_create"),
    path("api-endpoints/<int:el_id>", api_endpoint_detail, name="api_endpoint_detail"),
]
