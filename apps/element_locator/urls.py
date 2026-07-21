"""element-locator URL routing — 11 endpoints under /api/elements/."""
from django.urls import path
from .views import (
    dump_page, do_action, device_info_view, screenshot_snapshot,
    list_pages, create_page, page_detail, clear_pages, page_elements,
    add_element_to_page, batch_add_elements, update_element,
    flows_handler, delete_flow, pages_batch_move,
)

app_name = 'elements'

urlpatterns = [
    path('dump', dump_page, name='dump'),
    path('action', do_action, name='action'),
    path('device-info', device_info_view, name='device_info'),
    path('screenshot', screenshot_snapshot, name='screenshot'),
    path('pages', list_pages, name='pages_list'),
    path('pages/create', create_page, name='page_create'),
    path('pages/clear', clear_pages, name='pages_clear'),
    path('pages/batch-move', pages_batch_move, name='pages_batch_move'),
    path('pages/<int:page_id>', page_detail, name='page_detail'),
    path('pages/<int:page_id>/items', page_elements, name='page_items'),
    path('pages/<int:page_id>/elements', add_element_to_page, name='page_add_element'),
    path('pages/<int:page_id>/elements/batch', batch_add_elements, name='page_batch_add_elements'),
    path('items/<int:el_id>', update_element, name='item_update'),
    path('flows', flows_handler, name='flows'),
    path('flows/<int:flow_id>', delete_flow, name='flow_delete'),
]
