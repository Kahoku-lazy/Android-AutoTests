_MILESTONE = "milestone"
_UNTITLED = "未命名用例"


def case_identity_label(identity: object) -> str:
    if not isinstance(identity, dict) or not identity:
        return ""
    if identity.get("source") == _MILESTONE:
        return "里程碑"
    rows = _rows(identity)
    if not rows:
        return ""
    first = _title(rows[0])
    if len(rows) == 1:
        return first
    return f"{first} · 共 {len(rows)} 条"


def case_identity_rows(identity: object) -> list[dict]:
    if not isinstance(identity, dict) or identity.get("source") == _MILESTONE:
        return []
    return _rows(identity)


def _rows(identity: dict) -> list[dict]:
    raw = identity.get("rows")
    if not isinstance(raw, list):
        return []
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "project": " ".join(str(item.get("project") or "").split()),
                "id": str(item.get("id") or ""),
                "title": _title(item),
            }
        )
    return rows


def _title(row: dict) -> str:
    text = " ".join(str(row.get("title") or "").split())
    return text or _UNTITLED
