"""Data migration: clear page-level OCR data（OCR 落库下线，rework-inspector-view）.

检查器「保存到元素定位」不再写入页面级 OCR，存量 el_pages.ocr_json 一并清空。
快照表 di_snapshots.ocr_json 与 inspector 缩略图文件不受影响。
不可逆：reverse 为空操作，回滚需从 el_pages 备份恢复。
"""

from django.db import migrations


def _clear_page_ocr(apps, schema_editor):
    """逐行判断后置空（不用 JSON 相等查询，避免各数据库对 JSONField 比较语义的差异）。"""
    Page = apps.get_model("element_locator", "Page")
    for page in Page.objects.only("id", "ocr_json").iterator():
        if page.ocr_json:
            page.ocr_json = {}
            page.save(update_fields=["ocr_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("element_locator", "0013_migrate_locator_trees"),
    ]

    operations = [
        migrations.RunPython(_clear_page_ocr, migrations.RunPython.noop),
    ]
