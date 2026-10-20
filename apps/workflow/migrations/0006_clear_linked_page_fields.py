"""清空页面流文档里对元素定位页面的关联字段。

变更 retire-inspector-and-element-locator。元素定位退役后，节点上四个关联键没有数据源，
迁移只删这四个键，文档结构与其余属性原样保留。
"""

import json

from django.db import migrations

_LINK_KEYS = (
    "linked_elements",
    "linked_page_domain",
    "linked_page_id",
    "linked_page_name",
)


def _strip_linked(value: object) -> tuple[object, bool]:
    """递归删除节点 properties 里的关联键；返回 (新值, 是否有改动)。"""
    if isinstance(value, list):
        changed = False
        items = []
        for item in value:
            new_item, item_changed = _strip_linked(item)
            items.append(new_item)
            changed = changed or item_changed
        return items, changed
    if not isinstance(value, dict):
        return value, False

    changed = False
    for key, inner in list(value.items()):
        if key == "properties" and isinstance(inner, dict):
            for link_key in _LINK_KEYS:
                if link_key in inner:
                    inner.pop(link_key, None)
                    changed = True
            continue
        new_inner, inner_changed = _strip_linked(inner)
        if inner_changed:
            value[key] = new_inner
            changed = True
    return value, changed


def clear_linked_props(apps, schema_editor) -> None:
    """遍历全部页面流文档，删掉四个关联键。"""
    document = apps.get_model("workflow", "WorkflowDocument")
    for doc in document.objects.all().iterator():
        try:
            data = json.loads(doc.config_json or "{}")
        except (TypeError, ValueError):
            continue
        updated, changed = _strip_linked(data)
        if changed:
            document.objects.filter(pk=doc.pk).update(
                config_json=json.dumps(updated, ensure_ascii=False)
            )


class Migration(migrations.Migration):
    """只删关联键，不改文档结构；反向迁移不恢复已删字段。"""

    dependencies = [
        ("workflow", "0005_alter_workflowdocument_doc_type"),
    ]

    operations = [
        migrations.RunPython(clear_linked_props, migrations.RunPython.noop),
    ]
