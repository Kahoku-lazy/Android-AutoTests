"""XPath generation and YAML serialization utilities."""
# Re-exported from original api/xpath_utils.py — same implementation


def gen_xpath_candidates(el: dict, all_els: list[dict]) -> list[dict]:
    """Generate candidate XPath locators for an element, sorted by match count.

    Produces up to 8 locator types: resource-id, text, content-desc, class,
    index, combined (resource-id+text), wildcard resource-id, wildcard text.
    """
    cls = el["class_name"]
    rid = el["resource_id"]
    txt = el["text"]
    desc = el["content_desc"]
    idx = el.get("index", "")

    locators = []

    def count(pred) -> int:
        return sum(1 for e in all_els if pred(e))

    if rid:
        xp = f'//{cls}[@resource-id=\'{rid}\']'
        locators.append({
            "type": "resource-id", "xpath": xp,
            "count": count(lambda e: e["resource_id"] == rid and e["class_name"] == cls),
        })

    if txt:
        xp = f'//{cls}[@text=\'{txt}\']'
        locators.append({
            "type": "text", "xpath": xp,
            "count": count(lambda e: e["text"] == txt and e["class_name"] == cls),
        })

    if desc:
        xp = f'//{cls}[@content-desc=\'{desc}\']'
        locators.append({
            "type": "content-desc", "xpath": xp,
            "count": count(lambda e: e["content_desc"] == desc and e["class_name"] == cls),
        })

    xp = f'//{cls}'
    locators.append({
        "type": "class", "xpath": xp,
        "count": count(lambda e: e["class_name"] == cls),
    })

    if idx:
        try:
            pos = int(idx) + 1
            locators.append({
                "type": "index", "xpath": f"({xp})[{pos}]",
                "count": 1, "note": "fragile",
            })
        except ValueError:
            pass

    if rid and txt:
        xp = f'//{cls}[@resource-id=\'{rid}\' and @text=\'{txt}\']'
        locators.append({
            "type": "combined", "xpath": xp,
            "count": count(lambda e: e["resource_id"] == rid and e["text"] == txt and e["class_name"] == cls),
        })

    if rid:
        locators.append({
            "type": "resource-id (any)", "xpath": f'//*[@resource-id=\'{rid}\']',
            "count": count(lambda e: e["resource_id"] == rid),
        })

    if txt:
        locators.append({
            "type": "text (any)", "xpath": f'//*[@text=\'{txt}\']',
            "count": count(lambda e: e["text"] == txt),
        })

    # Deduplicate + sort
    seen = set()
    uniq = []
    for l in locators:
        if l["xpath"] not in seen:
            seen.add(l["xpath"])
            uniq.append(l)
    uniq.sort(key=lambda x: x["count"])
    return uniq


def simple_yaml_dump(obj, indent=0) -> str:
    """Serialize Python dict/list to YAML string without PyYAML dependency."""
    lines = []
    prefix = "  " * indent

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(simple_yaml_dump(v, indent + 1))
            elif isinstance(v, str):
                if "\n" in v or "'" in v or ":" in v:
                    lines.append(f'{prefix}{k}: "{v}"')
                else:
                    lines.append(f"{prefix}{k}: {v}")
            elif v is None:
                lines.append(f"{prefix}{k}:")
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                lines.append(f"{prefix}- ")
                for dk, dv in item.items():
                    if isinstance(dv, dict):
                        lines.append(f"{prefix}  {dk}:")
                        lines.append(simple_yaml_dump(dv, indent + 2))
                    elif isinstance(dv, str):
                        if "\n" in dv or "'" in dv:
                            lines.append(f'{prefix}  {dk}: "{dv}"')
                        else:
                            lines.append(f"{prefix}  {dk}: {dv}")
                    else:
                        lines.append(f"{prefix}  {dk}: {dv}")
            elif isinstance(item, str):
                lines.append(f'{prefix}- {item}')
            else:
                lines.append(f"{prefix}- {item}")

    return "\n".join(lines)
