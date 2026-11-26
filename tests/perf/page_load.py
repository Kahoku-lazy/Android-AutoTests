from __future__ import annotations

import json
import statistics
import time

from pathlib import Path

import requests

BUDGETS_PATH = Path(__file__).resolve().parent / "budgets.json"

INIT_SCRIPT = """
(() => {
  window.__perfProbe = { lcp: [], cls: 0 };
  try {
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) window.__perfProbe.lcp.push(e.startTime);
    }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) {
        if (!e.hadRecentInput) window.__perfProbe.cls += e.value;
      }
    }).observe({ type: "layout-shift", buffered: true });
  } catch (e) {}
})();
"""

COLLECT_SCRIPT = """
() => {
  const nav = performance.getEntriesByType("navigation")[0] || {};
  const paints = {};
  for (const p of performance.getEntriesByType("paint")) paints[p.name] = p.startTime;
  const res = performance.getEntriesByType("resource");
  let transfer = 0;
  for (const r of res) transfer += r.transferSize || 0;
  const probe = window.__perfProbe || { lcp: [], cls: 0 };
  const app = document.querySelector("#app") || document.body;
  const fcp = paints["first-contentful-paint"] ?? null;
  const lcpValues = probe.lcp || [];
  return {
    ttfb: nav.responseStart,
    fcp,
    lcp: lcpValues.length ? Math.max(...lcpValues) : fcp,
    lcp_source: lcpValues.length ? "lcp" : fcp === null ? "none" : "fcp",
    dcl: nav.domContentLoadedEventEnd,
    load: nav.loadEventEnd,
    requests: res.length,
    transfer_kb: Math.round(((nav.transferSize || 0) + transfer) / 1024),
    cls: probe.cls,
    renderedChars: (app.innerText || "").length,
    href: location.href,
  };
}
"""

METRICS = ("lcp", "load", "transfer_kb", "requests")


def load_budgets(profile: str) -> dict:
    data = json.loads(BUDGETS_PATH.read_text(encoding="utf-8"))
    profiles = data["profiles"]
    if profile not in profiles:
        raise KeyError(f"unknown perf profile {profile!r}; available: {', '.join(profiles)}")
    return profiles[profile]


def login_tokens(api_url: str, username: str, password: str, email: str) -> dict | None:
    try:
        login = requests.post(
            f"{api_url}/api/auth/login/",
            json={"username": username, "password": password},
            timeout=10,
        )
        if login.status_code != 200:
            requests.post(
                f"{api_url}/api/auth/register/",
                json={
                    "username": username,
                    "password": password,
                    "password2": password,
                    "email": email,
                },
                timeout=10,
            )
            login = requests.post(
                f"{api_url}/api/auth/login/",
                json={"username": username, "password": password},
                timeout=10,
            )
        login.raise_for_status()
    except requests.RequestException:
        return None
    body = login.json()
    data = body.get("data", body)
    tokens = data.get("tokens", data)
    access = tokens.get("access") or tokens.get("access_token")
    if not access:
        return None
    return {
        "access": access,
        "refresh": tokens.get("refresh") or tokens.get("refresh_token") or "",
        "username": username,
    }


def seed_script(tokens: dict) -> str:
    payload = {
        "access_token": tokens["access"],
        "refresh_token": tokens["refresh"],
        "username": tokens["username"],
    }
    body = "".join(
        f"try {{ localStorage.setItem({json.dumps(k)}, {json.dumps(v)}); }} catch (e) {{}} "
        for k, v in payload.items()
    )
    return "(() => {" + body + "})();"


def launch_browser(pw, channel: str | None = None):
    candidates: list[dict] = []
    if channel:
        candidates.append({"channel": channel})
    for exe in sorted(
        (Path.home() / "AppData" / "Local" / "ms-playwright").glob(
            "chromium-*/chrome-win64/chrome.exe"
        ),
        reverse=True,
    ):
        candidates.append({"executable_path": str(exe)})
    candidates.append({})
    last_error: Exception | None = None
    for kwargs in candidates:
        try:
            return pw.chromium.launch(headless=True, **kwargs)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"cannot launch chromium: {last_error}")


def measure_path(
    browser, base_url: str, path: str, runs: int, settle_ms: int, tokens: dict | None
) -> list[dict]:
    rows: list[dict] = []
    url = base_url.rstrip("/") + path
    for index in range(runs):
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_init_script(INIT_SCRIPT)
        if tokens and not path.startswith("/login"):
            context.add_init_script(seed_script(tokens))
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        started = time.time()
        response = page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(settle_ms)
        row = page.evaluate(COLLECT_SCRIPT)
        row.update(
            {
                "path": path,
                "run": index + 1,
                "status": response.status if response else None,
                "wall_ms": round((time.time() - started) * 1000),
                "page_errors": errors[:3],
            }
        )
        rows.append(row)
        context.close()
    return rows


def summarize(rows: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    for metric in ("ttfb", "fcp", "lcp", "dcl", "load", "requests", "transfer_kb", "cls"):
        values = [row[metric] for row in rows if isinstance(row.get(metric), (int, float))]
        if not values:
            continue
        summary[metric] = {
            "median": round(statistics.median(values), 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
        }
    return summary


def median(rows: list[dict], metric: str) -> float | None:
    values = [row[metric] for row in rows if isinstance(row.get(metric), (int, float))]
    return statistics.median(values) if values else None
