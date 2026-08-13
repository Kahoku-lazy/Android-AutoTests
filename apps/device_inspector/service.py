"""XPath generation utility — moved from element_locator.service."""


def gen_xpath_candidates(el: dict, all_els: list[dict]) -> list[dict]:
    """Generate candidate XPath locators for an element, sorted by match count.

    Produces up to 8 locator types: resource-id, text, content-desc, class,
    index, combined (resource-id+text), wildcard resource-id, wildcard text.

    Pre-indexes all_els into dicts keyed by class_name, resource_id, text,
    and compound keys for O(1) count lookups instead of O(n) scans.
    """
    cls = el["class_name"]
    rid = el["resource_id"]
    txt = el["text"]
    desc = el["content_desc"]
    idx = el.get("index", "")

    # ── Build indexes once per call (shared across all locate types) ──
    by_class: dict[str, int] = {}
    by_rid: dict[str, int] = {}
    by_text: dict[str, int] = {}
    by_class_rid: dict[tuple[str, str], int] = {}
    by_text_and_class: dict[tuple[str, str], int] = {}  # (class_name, text) → count
    by_desc_and_class: dict[tuple[str, str], int] = {}  # (class_name, content_desc) → count
    by_rid_text_class: dict[tuple[str, str, str], int] = {}  # (class, rid, text) → count
    for e in all_els:
        c = e["class_name"]
        by_class[c] = by_class.get(c, 0) + 1
        r = e["resource_id"]
        if r:
            by_rid[r] = by_rid.get(r, 0) + 1
            k = (c, r)
            by_class_rid[k] = by_class_rid.get(k, 0) + 1
        t = e["text"]
        if t:
            by_text[t] = by_text.get(t, 0) + 1
            by_text_and_class[(c, t)] = by_text_and_class.get((c, t), 0) + 1
            if r:
                by_rid_text_class[(c, r, t)] = by_rid_text_class.get((c, r, t), 0) + 1
        d = e["content_desc"]
        if d:
            by_desc_and_class[(c, d)] = by_desc_and_class.get((c, d), 0) + 1

    locators = []

    if rid:
        xp = f"//{cls}[@resource-id='{rid}']"
        locators.append(
            {
                "type": "resource-id",
                "xpath": xp,
                "count": by_class_rid.get((cls, rid), 0),
            }
        )

    if txt:
        xp = f"//{cls}[@text='{txt}']"
        locators.append(
            {
                "type": "text",
                "xpath": xp,
                "count": by_text_and_class.get((cls, txt), 0),
            }
        )

    if desc:
        xp = f"//{cls}[@content-desc='{desc}']"
        locators.append(
            {
                "type": "content-desc",
                "xpath": xp,
                "count": by_desc_and_class.get((cls, desc), 0),
            }
        )

    xp = f"//{cls}"
    locators.append(
        {
            "type": "class",
            "xpath": xp,
            "count": by_class.get(cls, 0),
        }
    )

    if idx:
        try:
            pos = int(idx) + 1
            locators.append(
                {
                    "type": "index",
                    "xpath": f"({xp})[{pos}]",
                    "count": 1,
                    "note": "fragile",
                }
            )
        except ValueError:
            pass

    if rid and txt:
        xp = f"//{cls}[@resource-id='{rid}' and @text='{txt}']"
        locators.append(
            {
                "type": "combined",
                "xpath": xp,
                "count": by_rid_text_class.get((cls, rid, txt), 0),
            }
        )

    if rid:
        locators.append(
            {
                "type": "resource-id (any)",
                "xpath": f"//*[@resource-id='{rid}']",
                "count": by_rid.get(rid, 0),
            }
        )

    if txt:
        locators.append(
            {
                "type": "text (any)",
                "xpath": f"//*[@text='{txt}']",
                "count": by_text.get(txt, 0),
            }
        )

    # Deduplicate + sort
    seen = set()
    uniq = []
    for l in locators:
        if l["xpath"] not in seen:
            seen.add(l["xpath"])
            uniq.append(l)
    uniq.sort(key=lambda x: int(str(x.get("count", 0))))
    return uniq
