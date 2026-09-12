"""Data migration: seed system projects and map old trees → LocatorDirectory."""

from django.db import migrations


def _seed_and_migrate(apps, schema_editor):
    LocatorProject = apps.get_model("element_locator", "LocatorProject")
    LocatorDirectory = apps.get_model("element_locator", "LocatorDirectory")
    Page = apps.get_model("element_locator", "Page")
    WebGroup = apps.get_model("element_locator", "WebGroup")
    WebElement = apps.get_model("element_locator", "WebElement")
    ApiGroup = apps.get_model("element_locator", "ApiGroup")
    ApiEndpoint = apps.get_model("element_locator", "ApiEndpoint")

    projects = {}
    for code, name in (("android", "Android"), ("web", "Web"), ("api", "API")):
        obj, _ = LocatorProject.objects.get_or_create(
            code=code, defaults={"name": name, "description": ""}
        )
        projects[code] = obj

    # ── Android: folders → directories; pages hang under nearest folder ancestor ──
    folder_map: dict[int, int] = {}  # old Page folder id → LocatorDirectory id

    def ensure_folder_chain(page_folder):
        if page_folder.id in folder_map:
            return folder_map[page_folder.id]
        parent_dir_id = None
        if page_folder.parent_id:
            parent_page = Page.objects.filter(id=page_folder.parent_id).first()
            if parent_page and parent_page.is_folder:
                parent_dir_id = ensure_folder_chain(parent_page)
            elif parent_page and not parent_page.is_folder:
                # parent is a page file — create sibling-named dir under that page's directory
                parent_dir_id = None
        name = (page_folder.label or f"目录-{page_folder.id}").strip() or f"目录-{page_folder.id}"
        # unique under parent
        existing = LocatorDirectory.objects.filter(
            project=projects["android"], parent_id=parent_dir_id, name=name
        ).first()
        if existing:
            folder_map[page_folder.id] = existing.id
            return existing.id
        d = LocatorDirectory.objects.create(
            project=projects["android"],
            parent_id=parent_dir_id,
            name=name,
            sort_order=0,
        )
        folder_map[page_folder.id] = d.id
        return d.id

    for folder in Page.objects.filter(is_folder=True).order_by("id"):
        ensure_folder_chain(folder)

    for page in Page.objects.filter(is_folder=False).order_by("id"):
        dir_id = None
        if page.parent_id:
            parent = Page.objects.filter(id=page.parent_id).first()
            if parent and parent.is_folder:
                dir_id = folder_map.get(parent.id) or ensure_folder_chain(parent)
            elif parent and not parent.is_folder:
                # page nested under another page: create same-name directory for parent page
                wrap_name = (parent.label or f"页面-{parent.id}").strip() or f"页面-{parent.id}"
                wrap_parent = None
                if parent.parent_id and parent.parent_id in folder_map:
                    wrap_parent = folder_map[parent.parent_id]
                wrap = LocatorDirectory.objects.filter(
                    project=projects["android"], parent_id=wrap_parent, name=wrap_name
                ).first()
                if wrap is None:
                    wrap = LocatorDirectory.objects.create(
                        project=projects["android"],
                        parent_id=wrap_parent,
                        name=wrap_name,
                    )
                if parent.directory_id is None:
                    parent.directory_id = wrap.id
                    parent.save(update_fields=["directory_id"])
                dir_id = wrap.id
        page.directory_id = dir_id
        page.save(update_fields=["directory_id"])

    # ── Web groups → directories ──
    web_group_map: dict[int, int] = {}

    def ensure_web_group(group):
        if group.id in web_group_map:
            return web_group_map[group.id]
        parent_dir_id = None
        if group.parent_id:
            parent = WebGroup.objects.filter(id=group.parent_id).first()
            if parent:
                parent_dir_id = ensure_web_group(parent)
        name = (group.name or f"分组-{group.id}").strip() or f"分组-{group.id}"
        existing = LocatorDirectory.objects.filter(
            project=projects["web"], parent_id=parent_dir_id, name=name
        ).first()
        if existing:
            web_group_map[group.id] = existing.id
            return existing.id
        d = LocatorDirectory.objects.create(
            project=projects["web"],
            parent_id=parent_dir_id,
            name=name,
            sort_order=getattr(group, "sort_order", 0) or 0,
        )
        web_group_map[group.id] = d.id
        return d.id

    for g in WebGroup.objects.all().order_by("id"):
        ensure_web_group(g)
    for el in WebElement.objects.all():
        if el.group_id and el.group_id in web_group_map:
            el.directory_id = web_group_map[el.group_id]
            el.save(update_fields=["directory_id"])

    # ── API groups → directories ──
    api_group_map: dict[int, int] = {}

    def ensure_api_group(group):
        if group.id in api_group_map:
            return api_group_map[group.id]
        parent_dir_id = None
        if group.parent_id:
            parent = ApiGroup.objects.filter(id=group.parent_id).first()
            if parent:
                parent_dir_id = ensure_api_group(parent)
        name = (group.name or f"分组-{group.id}").strip() or f"分组-{group.id}"
        existing = LocatorDirectory.objects.filter(
            project=projects["api"], parent_id=parent_dir_id, name=name
        ).first()
        if existing:
            api_group_map[group.id] = existing.id
            return existing.id
        d = LocatorDirectory.objects.create(
            project=projects["api"],
            parent_id=parent_dir_id,
            name=name,
            sort_order=getattr(group, "sort_order", 0) or 0,
        )
        api_group_map[group.id] = d.id
        return d.id

    for g in ApiGroup.objects.all().order_by("id"):
        ensure_api_group(g)
    for ep in ApiEndpoint.objects.all():
        if ep.group_id and ep.group_id in api_group_map:
            ep.directory_id = api_group_map[ep.group_id]
            ep.save(update_fields=["directory_id"])


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("element_locator", "0012_locator_projects_directories"),
    ]

    operations = [
        migrations.RunPython(_seed_and_migrate, _noop_reverse),
    ]
