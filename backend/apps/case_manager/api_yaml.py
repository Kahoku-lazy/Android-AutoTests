"""
python -m 调试路径: backend.apps.case_manager.api_yaml

本模块的业务功能如下：
1. parse_yaml_text: YAML 文本收敛为中性用例行，保留执行提示并把可选元数据映射成平台字段。
2. import_yaml_text: 按「项目 + 用例表」幂等写入用例库，必要时清理 YAML 中已消失的行。
3. export_yaml_text: 把选中的平台用例导出为可执行 YAML 文本，供任务执行物化配置。
4. validate_business_type: 校验调用方传入的默认业务类型（YAML 没写 business 时用它）。
"""

from __future__ import annotations

from typing import Any

import yaml

from django.db import transaction

from engines.agents.workflow.case_file import parse_cases, validate_platform_yaml

from .api_definitions import create_definition, update_definition
from .api_files import create_file, get_file
from .api_projects import ConflictError, get_project
from .models import CaseFile, TestDefinition

__all__ = [
    "BUSINESS_TYPES",
    "DEFAULT_BUSINESS_TYPE",
    "IMPORT_FILE_NAME_LIMIT",
    "export_yaml_text",
    "import_yaml_text",
    "parse_yaml_text",
    "validate_business_type",
]

IMPORT_FILE_NAME_LIMIT = 200
"""用例表名的字符上限，与 ``CaseFile.name`` 的模型上限一致。"""

BUSINESS_TYPES: tuple[str, ...] = ("appliance", "lighting", "app")
"""业务类型枚举：家电 / 照明 / APP。"""

DEFAULT_BUSINESS_TYPE = "appliance"
"""YAML 没写 ``business`` 且调用方也没指定时使用的业务类型。"""

_SYSTEMS: tuple[str, ...] = ("ANDROID", "WEB", "IOS", "API")
"""系统取值白名单；YAML 里可能是 ``WEB/ANDROID/IOS`` 这种多值串。"""

_PRIORITY_BY_NUMBER = {1: "P0", 2: "P1", 3: "P2"}
"""数值优先级到平台枚举的映射。"""

_BUSINESS_BY_TEXT = {"家电": "appliance", "照明": "lighting", "APP": "app"}
"""业务类型中文到平台枚举的映射。"""


def _text(value: object) -> str:
    """把任意值收成去首尾空白的文本。"""
    return str(value if value is not None else "").strip()


def _priority(value: object) -> str:
    """把 YAML 的优先级收成 P0 / P1 / P2，识别不了时回退 P1。"""
    if isinstance(value, bool):
        return "P1"
    if isinstance(value, (int, float)):
        return _PRIORITY_BY_NUMBER.get(int(value), "P1")
    text = _text(value).upper()
    for key in ("P0", "P1", "P2"):
        if text.startswith(key):
            return key
    if text.isdigit():
        return _PRIORITY_BY_NUMBER.get(int(text), "P1")
    return "P1"


def _system(value: object) -> str:
    """取 YAML 系统字段里的首个合法系统，缺省 ANDROID。"""
    text = _text(value).upper()
    for key in _SYSTEMS:
        if key in text:
            return key
    return "ANDROID"


def _case_type(value: object) -> str:
    """类型缺省为 AUTO（导入的 YAML 都是执行用）；给了「功能」时才是 FUNC。"""
    text = _text(value)
    if not text:
        return "AUTO"
    if "自动化" in text or text.upper() == "AUTO":
        return "AUTO"
    return "FUNC"


def _business_type(value: object, *, default: str = DEFAULT_BUSINESS_TYPE) -> str:
    """业务类型：YAML 显式给出时以 YAML 为准，否则用调用方指定的默认值。

    Args:
        value: YAML 里的 `business` 字段，可能是中文（家电 / 照明 / APP）或英文枚举。
        default: 该条用例没写业务类型时使用的值。

    Returns:
        `appliance` / `lighting` / `app` 之一。
    """
    text = _text(value)
    if not text:
        return default
    if text in _BUSINESS_BY_TEXT:
        return _BUSINESS_BY_TEXT[text]
    lowered = text.lower()
    if lowered in BUSINESS_TYPES:
        return lowered
    return _BUSINESS_BY_TEXT.get(text.upper(), default)


def validate_business_type(value: object) -> str:
    """校验默认业务类型取值。

    Args:
        value: 调用方传入的默认业务类型。

    Returns:
        合法的 `appliance` / `lighting` / `app`。

    Raises:
        ValueError: 取值不在枚举内，或为空。
    """
    text = _text(value) or DEFAULT_BUSINESS_TYPE
    if text not in BUSINESS_TYPES:
        raise ValueError(f"业务类型无效，可选：{' / '.join(BUSINESS_TYPES)}")
    return text


def _step_payload(step) -> dict[str, Any]:
    """把引擎的一步收成可入库的字典，空提示不写空节点。"""
    payload: dict[str, Any] = {"action": step.action, "assertion": step.expected}
    if step.anchor:
        payload["anchor"] = dict(step.anchor)
    if step.log is not None:
        payload["log"] = {
            "sku": step.log.sku,
            "port": step.log.port,
            "keywords": list(step.log.keywords),
        }
    return payload


def _raw_cases(data: object) -> list[dict[str, Any]]:
    """取根节点的原始用例字典列表；结构不对时返回空列表。"""
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def parse_yaml_text(
    text: str, *, default_business_type: str = DEFAULT_BUSINESS_TYPE
) -> tuple[list[dict[str, Any]], str]:
    """
    把 YAML 文本收敛为可写入用例库的中性行。

    Args:
        text: YAML 正文（UTF-8 文本）。
        default_business_type: YAML 没写 ``business`` 时使用的业务类型。

    Returns:
        (用例行列表, 失败原因)。成功时原因为空串；每行含 title / priority /
        system / case_type / business_type / module / precondition /
        source_case_id / steps（步骤内含可选 anchor 与 log）。

    Raises:
        无：解析与结构问题一律通过返回值报出，由调用方决定如何提示。
    """
    try:
        default_business = validate_business_type(default_business_type)
    except ValueError as exc:
        return [], str(exc)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [], f"YAML 无法解析: {exc}"
    items, reason = parse_cases(data, require_agent=False)
    if reason:
        return [], reason
    raws = _raw_cases(data)
    rows: list[dict[str, Any]] = []
    for raw, item in zip(raws, items):
        rows.append(
            {
                "title": item.title,
                "priority": _priority(raw.get("priority")),
                "system": _system(raw.get("system")),
                "case_type": _case_type(raw.get("type")),
                "business_type": _business_type(raw.get("business"), default=default_business),
                "module": _text(raw.get("module")),
                "precondition": _text(raw.get("precondition")),
                "source_case_id": _text(raw.get("case_id")),
                "steps": [_step_payload(step) for step in item.steps],
            }
        )
    return rows, ""


def _resolve_file(*, project_id: int, user_id: str, name: str) -> CaseFile:
    """按项目 + 表名取用例表；不存在时新建，并发冲突时重查一次。

    Raises:
        LookupError: 项目不存在或无权访问。
        ValueError: 表名为空。
    """
    clean = _text(name)[:IMPORT_FILE_NAME_LIMIT]
    if not clean:
        raise ValueError("用例表名称不能为空")
    existing = CaseFile.objects.filter(project_id=project_id, directory=None, name=clean).first()
    if existing is not None:
        return existing
    try:
        created = create_file(project_id=project_id, name=clean, user_id=user_id)
    except ConflictError:
        existing = CaseFile.objects.filter(
            project_id=project_id, directory=None, name=clean
        ).first()
        if existing is None:
            raise
        return existing
    return CaseFile.objects.get(id=created["id"])


def import_yaml_text(
    *,
    project_id: int,
    user_id: str,
    text: str,
    file_id: int | None = None,
    file_name: str = "",
    prune: bool = False,
    default_business_type: str = DEFAULT_BUSINESS_TYPE,
) -> dict[str, Any]:
    """
    把一份 YAML 写入用例库，按标题幂等覆盖。

    Args:
        project_id: 目标用例项目编号。
        user_id: 当前用户编号；项目必须属于该用户。
        text: YAML 正文。
        file_id: 目标用例表编号；None 时按 ``file_name`` 复用或新建。
        file_name: 目标用例表名；``file_id`` 为空时使用。
        prune: 是否删除 YAML 中已不存在的旧用例行。
        default_business_type: YAML 没写 ``business`` 时使用的业务类型。

    Returns:
        `{file_id, file_name, total, created, updated, removed, skipped}`。

    Raises:
        ValueError: YAML 结构不合法、默认业务类型非法，或表名为空。
        LookupError: 项目 / 用例表不存在，或不属于当前用户。
    """
    rows, reason = parse_yaml_text(text, default_business_type=default_business_type)
    if reason:
        raise ValueError(reason)
    if not rows:
        raise ValueError("YAML 中没有可用用例")

    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")

    if file_id is not None:
        case_file = get_file(file_id=file_id, user_id=user_id)
        if case_file is None or case_file.project_id != project.id:
            raise LookupError("用例表不存在")
    else:
        case_file = _resolve_file(project_id=project.id, user_id=user_id, name=file_name)

    existing = {
        obj.title: obj
        for obj in TestDefinition.objects.filter(file=case_file).order_by("sort_order", "id")
    }
    skipped: list[dict[str, str]] = []
    created = 0
    updated = 0
    seen: set[str] = set()
    with transaction.atomic():
        for index, row in enumerate(rows):
            title = row["title"]
            if title in seen:
                skipped.append({"title": title, "reason": "同一份 YAML 内标题重复"})
                continue
            seen.add(title)
            obj = existing.pop(title, None)
            if obj is None:
                create_definition(
                    project_id=project.id,
                    file_id=case_file.id,
                    user_id=user_id,
                    title=title,
                    priority=row["priority"],
                    system=row["system"],
                    case_type=row["case_type"],
                    business_type=row["business_type"],
                    module=row["module"],
                    precondition=row["precondition"],
                    steps=row["steps"],
                    sort_order=index,
                    source_case_id=row["source_case_id"],
                )
                created += 1
                continue
            update_definition(
                case_id=obj.id,
                user_id=user_id,
                title=title,
                priority=row["priority"],
                system=row["system"],
                case_type=row["case_type"],
                business_type=row["business_type"],
                module=row["module"],
                precondition=row["precondition"],
                steps=row["steps"],
                sort_order=index,
            )
            updated += 1
        removed = 0
        if prune and existing:
            ids = [obj.id for obj in existing.values()]
            # delete() 会连带统计级联的步骤行，先用 count 取「真正删掉的用例条数」
            removed = TestDefinition.objects.filter(id__in=ids).count()
            TestDefinition.objects.filter(id__in=ids).delete()

    return {
        "file_id": case_file.id,
        "file_name": case_file.name,
        "total": len(rows),
        "created": created,
        "updated": updated,
        "removed": removed,
        "skipped": skipped,
    }


def export_yaml_text(*, case_ids: list[str], user_id: str) -> str:
    """
    把选中的平台用例导出为可执行 YAML 文本。

    Args:
        case_ids: 用例编号列表，顺序即导出顺序。
        user_id: 当前用户编号；只能导出自己项目下的用例。

    Returns:
        YAML 文本；根节点为用例列表，步骤含 action / assert 与可选 anchor / log。

    Raises:
        ValueError: 未选择用例，或导出的文本无法通过平台 YAML 校验。
        LookupError: 有编号不存在或不属于当前用户。
    """
    ids = [str(item).strip() for item in (case_ids or []) if str(item).strip()]
    if not ids:
        raise ValueError("请选择要执行的用例")
    rows = (
        TestDefinition.objects.filter(id__in=ids, project__created_by=str(user_id))
        .prefetch_related("steps")
        .order_by("sort_order", "id")
    )
    by_id = {obj.id: obj for obj in rows}
    for case_id in ids:
        if case_id not in by_id:
            raise LookupError(f"用例不存在或无权执行：{case_id}")

    payload: list[dict[str, Any]] = []
    for case_id in ids:
        obj = by_id[case_id]
        steps: list[dict[str, Any]] = []
        for step in obj.steps.all():
            item: dict[str, Any] = {"action": step.action, "assert": step.assertion}
            if step.anchor:
                item["anchor"] = dict(step.anchor)
            if step.log:
                item["log"] = dict(step.log)
            steps.append(item)
        payload.append({"title": obj.title, "steps": steps})

    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000)
    _items, reason = validate_platform_yaml(text)
    if reason:
        raise ValueError(f"用例无法物化为平台 YAML：{reason}")
    return text
