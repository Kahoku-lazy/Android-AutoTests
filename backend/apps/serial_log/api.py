"""串口日志写库口 —— 端口登记、监听开关与关键词对照表的唯一写点。

跨模块需要读开关状态或按型号取关键词时走本文件；禁止其它 App 直接读写
`LogPort` / `LogKeyword`。
双轨制：config 行三列由配置同步（`ensure_log_ports`），custom 行三列由本文件
的增删改函数维护；配置同步不创建、不改写、不删除自定义行。
关键词表 `sl_log_keywords`：一行 = 关键词 × 功能点 × 范围；范围并集口径见
`keyword_mapping_for_sku`。
"""

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
    """按配置登记刷新**配置行**的端口 / SKU / 波特率三列，返回按端口排序的配置行。

    只刷三列，**不动** `enabled`（开关状态归用户，配置变更不得悄悄改回默认）。
    端口已被自定义行占用时跳过并记 warning（自定义行真相源在库，配置不得覆盖）。
    """
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
    """自定义端口登记 → 来源列表（按端口排序）；供 `sources` 双轨合并。"""
    rows = LogPort.objects.filter(origin=LogPort.ORIGIN_CUSTOM).order_by("port")
    return [LogSourceSpec(port=row.port, sku=row.sku, baud=row.baud) for row in rows]


def create_custom_port(port: int, sku: str, baud: int) -> LogPort:
    """新增自定义端口（默认开启监听）；同号已存在时抛 ValueError（数据侧兜底）。"""
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
    """编辑自定义端口的 SKU / 波特率；非自定义行抛 ValueError。"""
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
    """删除自定义端口登记（不动日志文件）；非自定义行返回 False。"""
    deleted, _ = LogPort.objects.filter(port=int(port), origin=LogPort.ORIGIN_CUSTOM).delete()
    return bool(deleted)


def get_log_port_enabled_map() -> dict[int, bool]:
    """端口 → 是否开启监听；无记录＝开启（与平台工具开关同一口径）。"""
    return {row.port: bool(row.enabled) for row in LogPort.objects.all()}


def is_log_port_enabled(port: int) -> bool:
    """该端口是否开启监听；无记录＝开启。"""
    row = LogPort.objects.filter(port=int(port)).first()
    return True if row is None else bool(row.enabled)


def set_log_port_enabled(port: int, enabled: bool) -> None:
    """写单个端口的监听开关（upsert；三列由 `ensure_log_ports` / 自定义增改负责）。"""
    LogPort.objects.update_or_create(port=int(port), defaults={"enabled": bool(enabled)})


# ── 关键词对照表（sl_log_keywords）──────────────────────────────────────────

# SKU 名白名单：与 ae_harness 的型号白名单同形，避免把任意字符串当范围存进库。
_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def list_keyword_rows() -> list[LogKeyword]:
    """全量关键词对照行（按 sort_order、id 排序）；供目录组装与维护核对。

    Returns:
        按登记行序排列的 `LogKeyword` 列表；表为空时返回空列表。
    """
    return list(LogKeyword.objects.order_by("sort_order", "id"))


def keyword_mapping_for_sku(sku: str) -> dict[str, list[dict]]:
    """某型号可用关键词 = 通用 ∪ 该型号专用（并集；专用不覆盖通用）。

    Args:
        sku: 型号名（如 H6601）；空串或 "*" 时只取通用条目。

    Returns:
        可注入 `KeywordIndex(mapping)` 的映射：keyword → [{id, module, feature}]，
        条目按表内登记行序（sort_order）排列。
    """
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
    """范围取值校验："*"（通用）或 SKU 名白名单；空值按通用。

    Raises:
        ValueError: 范围既不是 "*" 也不满足 SKU 名白名单。
    """
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
    """登记 / 更新单条关键词条目（按唯一键 keyword+feature_id+scope upsert）。

    Args:
        keyword: 关键词原文（去空白后不可为空）。
        module: 功能模块名。
        feature: 功能点名。
        feature_id: 功能点业务编号；缺省按全表 max+1 续编。
        scope: 范围，"*"=通用或 SKU 名；缺省通用。
        sort_order: 行序；缺省按全表 max+10 追加。

    Returns:
        写入后的 `LogKeyword` 行。

    Raises:
        ValueError: 关键词为空或范围非法。
    """
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
    """按主键删除单条关键词条目。

    Args:
        row_id: 条目主键。

    Returns:
        是否删除了条目（不存在时 False）。
    """
    deleted, _ = LogKeyword.objects.filter(pk=int(row_id)).delete()
    return bool(deleted)


def _require_text(value: str, label: str) -> str:
    """必填文本校验：去空白后非空。

    Raises:
        ValueError: 文本为空。
    """
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
    """新建单条关键词条目；唯一键已存在时拒绝（区别于 upsert 的静默更新）。

    Args:
        keyword: 关键词原文（必填）。
        module: 功能模块名（必填）。
        feature: 功能点名（必填）。
        scope: 范围，"*"=通用或 SKU 名；缺省通用。
        feature_id: 功能点业务编号；缺省按全表 max+1 续编。

    Returns:
        新建的 `LogKeyword` 行（行序追加表尾）。

    Raises:
        ValueError: 必填文本为空、范围非法或唯一键已存在。
    """
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
    """部分更新单条关键词条目；改动后的唯一键不得撞另一行。

    Args:
        row_id: 条目主键。
        keyword: 新关键词原文；None 表示不改。
        module: 新功能模块名；None 表示不改。
        feature: 新功能点名；None 表示不改。
        scope: 新范围；None 表示不改。
        feature_id: 新功能点编号；None 表示不改。
        sort_order: 新行序；None 表示不改。

    Returns:
        更新后的 `LogKeyword` 行。

    Raises:
        ValueError: 条目不存在、未给任何字段、必填文本为空、范围非法或唯一键撞车。
    """
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
