from __future__ import annotations

import re

from django.db.models import Max

from engines.device.logbus import LogSourceSpec
from utils.logs import backend_log

from .models import LogKeyword, LogPort

__all__ = [
    "create_custom_port",
    "create_keyword",
    "delete_custom_port",
    "delete_keyword",
    "ensure_log_ports",
    "get_log_port_enabled_map",
    "is_log_port_enabled",
    "keyword_mapping_for_sku",
    "list_custom_port_specs",
    "list_keyword_rows",
    "set_log_port_enabled",
    "update_custom_port",
    "update_keyword",
    "upsert_keyword",
]


def ensure_log_ports(specs) -> list[LogPort]:
    stored = {row.port: row for row in LogPort.objects.all()}
    rows: list[LogPort] = []
    for spec in specs:
        port = int(spec.port)
        channel = str(spec.channel)
        baud = int(spec.baud)
        row = stored.get(port)
        if row is not None and row.origin == LogPort.ORIGIN_CUSTOM:
            backend_log.warning(
                "config port %s already registered as custom; skip config sync", port
            )
            continue
        if row is None:
            row = LogPort.objects.create(
                port=port, sku=channel, baud=baud, origin=LogPort.ORIGIN_CONFIG
            )
        elif row.sku != channel or row.baud != baud:
            row.sku = channel
            row.baud = baud
            row.save(update_fields=["sku", "baud", "updated_at"])
        rows.append(row)
    return sorted(rows, key=lambda item: item.port)


def list_custom_port_specs() -> list[LogSourceSpec]:
    rows = LogPort.objects.filter(origin=LogPort.ORIGIN_CUSTOM).order_by("port")
    return [LogSourceSpec(port=row.port, sku=row.sku, baud=row.baud) for row in rows]


def create_custom_port(port: int, sku: str, baud: int) -> LogPort:
    port = int(port)
    if LogPort.objects.filter(port=port).exists():
        raise ValueError(f"端口 {port} 已登记，不能重复新增")
    return LogPort.objects.create(
        port=port,
        sku=str(sku),
        baud=int(baud),
        origin=LogPort.ORIGIN_CUSTOM,
        enabled=True,
    )


def update_custom_port(port: int, *, sku: str | None = None, baud: int | None = None) -> LogPort:
    row = LogPort.objects.filter(port=int(port), origin=LogPort.ORIGIN_CUSTOM).first()
    if row is None:
        raise ValueError(f"端口 {int(port)} 不是自定义端口，不能编辑")
    fields: list[str] = []
    if sku is not None:
        row.sku = str(sku)
        fields.append("sku")
    if baud is not None:
        row.baud = int(baud)
        fields.append("baud")
    if fields:
        row.save(update_fields=[*fields, "updated_at"])
    return row


def delete_custom_port(port: int) -> bool:
    deleted, _ = LogPort.objects.filter(port=int(port), origin=LogPort.ORIGIN_CUSTOM).delete()
    return bool(deleted)


def get_log_port_enabled_map() -> dict[int, bool]:
    return {row.port: bool(row.enabled) for row in LogPort.objects.all()}


def is_log_port_enabled(port: int) -> bool:
    row = LogPort.objects.filter(port=int(port)).first()
    return True if row is None else bool(row.enabled)


def set_log_port_enabled(port: int, enabled: bool) -> None:
    LogPort.objects.update_or_create(port=int(port), defaults={"enabled": bool(enabled)})


_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def list_keyword_rows() -> list[LogKeyword]:
    return list(LogKeyword.objects.order_by("sort_order", "id"))


def keyword_mapping_for_sku(sku: str) -> dict[str, list[dict]]:
    name = str(sku or "").strip()
    scopes = [LogKeyword.SCOPE_GENERAL]
    if name and name != LogKeyword.SCOPE_GENERAL:
        scopes.append(name)
    mapping: dict[str, list[dict]] = {}
    for row in LogKeyword.objects.filter(scope__in=scopes).order_by("sort_order", "id"):
        mapping.setdefault(row.keyword, []).append(
            {"id": row.feature_id, "module": row.module, "feature": row.feature}
        )
    return mapping


def _validate_scope(scope: str) -> str:
    value = str(scope or "").strip() or LogKeyword.SCOPE_GENERAL
    if value != LogKeyword.SCOPE_GENERAL and not _SCOPE_PATTERN.match(value):
        raise ValueError(f"范围 {scope!r} 非法：须为 '*'（通用）或 SKU 名（字母/数字/_/-）")
    return value


def upsert_keyword(
    keyword: str,
    *,
    module: str,
    feature: str,
    feature_id: int | None = None,
    scope: str = LogKeyword.SCOPE_GENERAL,
    sort_order: int | None = None,
) -> LogKeyword:
    text = str(keyword or "").strip()
    if not text:
        raise ValueError("关键词不能为空")
    scope_value = _validate_scope(scope)
    if feature_id is None:
        highest = LogKeyword.objects.aggregate(value=Max("feature_id"))["value"]
        feature_id = (highest if highest is not None else -1) + 1
    if sort_order is None:
        highest_order = LogKeyword.objects.aggregate(value=Max("sort_order"))["value"]
        sort_order = (highest_order or 0) + 10
    row, _ = LogKeyword.objects.update_or_create(
        keyword=text,
        feature_id=int(feature_id),
        scope=scope_value,
        defaults={"module": str(module), "feature": str(feature), "sort_order": int(sort_order)},
    )
    return row


def delete_keyword(row_id: int) -> bool:
    deleted, _ = LogKeyword.objects.filter(pk=int(row_id)).delete()
    return bool(deleted)


def _require_text(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label}不能为空")
    return text


def create_keyword(
    keyword: str,
    *,
    module: str,
    feature: str,
    scope: str = LogKeyword.SCOPE_GENERAL,
    feature_id: int | None = None,
) -> LogKeyword:
    text = _require_text(keyword, "关键词")
    module_text = _require_text(module, "功能模块")
    feature_text = _require_text(feature, "功能点")
    scope_value = _validate_scope(scope)
    if feature_id is None:
        highest = LogKeyword.objects.aggregate(value=Max("feature_id"))["value"]
        feature_id = (highest if highest is not None else -1) + 1
    feature_id = int(feature_id)
    if LogKeyword.objects.filter(keyword=text, feature_id=feature_id, scope=scope_value).exists():
        raise ValueError(
            f"关键词 {text}（功能点 #{feature_id}，范围 {scope_value}）已登记，不能重复新建"
        )
    highest_order = LogKeyword.objects.aggregate(value=Max("sort_order"))["value"]
    return LogKeyword.objects.create(
        keyword=text,
        feature_id=feature_id,
        module=module_text,
        feature=feature_text,
        scope=scope_value,
        sort_order=(highest_order or 0) + 10,
    )


def update_keyword(
    row_id: int,
    *,
    keyword: str | None = None,
    module: str | None = None,
    feature: str | None = None,
    scope: str | None = None,
    feature_id: int | None = None,
    sort_order: int | None = None,
) -> LogKeyword:
    row = LogKeyword.objects.filter(pk=int(row_id)).first()
    if row is None:
        raise ValueError(f"关键词条目 {int(row_id)} 不存在")
    updates: dict = {}
    if keyword is not None:
        updates["keyword"] = _require_text(keyword, "关键词")
    if module is not None:
        updates["module"] = _require_text(module, "功能模块")
    if feature is not None:
        updates["feature"] = _require_text(feature, "功能点")
    if scope is not None:
        updates["scope"] = _validate_scope(scope)
    if feature_id is not None:
        updates["feature_id"] = int(feature_id)
    if sort_order is not None:
        updates["sort_order"] = int(sort_order)
    if not updates:
        raise ValueError("未提供任何更新字段")
    new_keyword = updates.get("keyword", row.keyword)
    new_feature_id = updates.get("feature_id", row.feature_id)
    new_scope = updates.get("scope", row.scope)
    collision = (
        LogKeyword.objects.filter(keyword=new_keyword, feature_id=new_feature_id, scope=new_scope)
        .exclude(pk=row.pk)
        .exists()
    )
    if collision:
        raise ValueError(
            f"关键词 {new_keyword}（功能点 #{new_feature_id}，范围 {new_scope}）已被其它条目登记，不能改成该组合"
        )
    for field, value in updates.items():
        setattr(row, field, value)
    row.save(update_fields=[*updates.keys(), "updated_at"])
    return row
