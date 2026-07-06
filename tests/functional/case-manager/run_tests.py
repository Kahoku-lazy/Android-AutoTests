"""
Case-Manager 全功能自动化测试 — 入口 + Runner + HTML 报告 (含失败截图).

用法:
    python run_tests.py                      # 全量
    python run_tests.py --layer DB           # DB 层
    python run_tests.py --layer API          # API 层
    python run_tests.py --layer UI           # UI 层 (Playwright + 失败截图)
    python run_tests.py --layer WHITE        # 白盒层
    python run_tests.py --case CASE-DB-01    # 单条
"""
import sys, os, time, argparse
from datetime import datetime
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)

import helpers as H

# 加载各层测试
import db_tests      # noqa: F401
import api_tests     # noqa: F401
import ui_tests      # noqa: F401
import white_tests   # noqa: F401


def run_tests(page=None, case_ids=None, layer=None):
    """执行测试。UI 层失败自动截图。"""
    passed = 0; failed = 0; skipped = 0
    tests_to_run = {}
    for cid, (tl, tf, desc) in H.ALL_TESTS.items():
        if case_ids and cid not in case_ids: continue
        if layer and tl != layer: continue
        tests_to_run[cid] = (tl, tf, desc)

    for cid, (tl, tf, desc) in tests_to_run.items():
        needs_browser = tl == "UI" and "page" in tf.__code__.co_varnames[:1]
        is_db = tl == "DB"
        if needs_browser and page is None: skipped += 1; continue
        if is_db and not H._django_ready:
            H.results.append({"case":cid,"dim":"DB","description":desc,"status":"SKIP",
                "actual":"Django ORM not ready","expected":"","duration_ms":0,
                "evidence":{},"screenshot":"","fix_note":""})
            skipped += 1; continue
        print(f"  [{cid}] {desc} ... ", end="", flush=True)
        try:
            ok = tf(page) if needs_browser else tf()
            if ok is None: skipped += 1; print("⏭ SKIP")
            elif ok: passed += 1; print("✅ PASS")
            else:
                failed += 1
                # UI 测试返回 False → 截图
                if needs_browser and page:
                    ss, _ = H.capture_screenshot(page, cid)
                    # 更新最近一条 record 的 screenshot
                    if H.results and H.results[-1]["case"] == cid:
                        H.results[-1]["screenshot"] = ss
                    print(f"❌ FAIL 📸 已截图")
                else:
                    print("❌ FAIL")
        except Exception as e:
            failed += 1
            err_msg = str(e)[:300]
            ss = ""
            # UI 测试失败 → 截图
            if needs_browser and page:
                ss, _ = H.capture_screenshot(page, cid)
                print(f"💥 ERROR: {e}  📸 已截图")
            else:
                print(f"💥 ERROR: {e}")
            H.results.append({"case":cid,"dim":tl,"description":desc,"status":"FAIL",
                "actual":err_msg,"expected":"no exception","duration_ms":0,
                "evidence":{"actual":err_msg,"expected":"no exception"},
                "screenshot":ss,"fix_note":""})
    return passed, failed, skipped


def generate_html_report(total_ms):
    """生成 HTML 报告，含截图 + 修复日志。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(H.results)
    p = sum(1 for r in H.results if r["status"]=="PASS")
    f = sum(1 for r in H.results if r["status"]=="FAIL")
    s = sum(1 for r in H.results if r["status"]=="SKIP")
    rate = (p/total*100) if total>0 else 0

    # 维度汇总
    dims = {}
    for r in H.results:
        d = r["dim"]
        if d not in dims: dims[d] = {"t":0,"p":0}
        dims[d]["t"]+=1
        if r["status"]=="PASS": dims[d]["p"]+=1

    dr = ""
    for dn in ["DB","API","UI","WHITE","DATA"]:
        if dn in dims:
            d = dims[dn]; rt = d["p"]/d["t"]*100 if d["t"]>0 else 0
            bar = "█"*max(1,int(rt/10))+"░"*(10-max(1,int(rt/10)))
            dr += f"<tr><td>{dn}</td><td>{d['t']}</td><td>{d['p']}</td><td>{d['t']-d['p']}</td><td>{rt:.0f}%</td><td class='heat'>{bar}</td></tr>"

    # 用例详情（含截图）
    cr = ""
    for r in H.results:
        icon = {"PASS":"✅","SKIP":"⏭","FAIL":"❌"}.get(r["status"],"❓")
        rc = {"PASS":"pass-row","SKIP":"skip-row","FAIL":"fail-row"}.get(r["status"],"")
        ss_html = ""
        if r.get("screenshot"):
            ss_id = f"ss-{r['case']}"
            ss_html = (
                f"<br><a href='#' class='ss-link' onclick='toggleSS(\"{ss_id}\");return false'>📸 查看失败截图</a>"
                f"<div id='{ss_id}' class='ss-wrap' style='display:none'>"
                f"<img src='{r['screenshot']}' class='ss-img' loading='lazy' title='点击收起' onclick='toggleSS(\"{ss_id}\")'>"
                f"</div>"
            )
        fix_html = ""
        # 解决方案: 仅失败用例显示
        if r.get("fix_note") and r["status"] == "FAIL":
            fix_html = f"<br><div class='fix-note'>🔧 解决方案: {r['fix_note']}</div>"
        # 问题原因: 所有用例均可有（PASS=验证了什么修复, FAIL=为什么失败）
        cause_html = ""
        if r.get("root_cause"):
            cause_label = "🔍 验证内容" if r["status"] == "PASS" else "🔍 问题原因"
            cause_html = f"<br><div class='cause-note'>{cause_label}: {r['root_cause']}</div>"
        # 复现步骤: 仅失败用例显示
        repro_html = ""
        if r.get("repro_steps") and r["status"] == "FAIL":
            repro_html = f"<br><div class='repro-note'>🔄 复现步骤: {r['repro_steps']}</div>"
        # 解决建议: 仅失败用例显示
        suggest_html = ""
        if r.get("fix_suggestion") and r["status"] == "FAIL":
            suggest_html = f"<br><div class='suggest-note'>💡 解决建议: {r['fix_suggestion']}</div>"
        cr += f"<tr class='{rc}'><td>{icon}</td><td>{r['case']}</td><td>{r['dim']}</td><td>{r['description']}</td><td class='actual'>{r['actual']}{cause_html}{repro_html}{suggest_html}{ss_html}{fix_html}</td><td class='expected'>{r['expected']}</td><td>{r['duration_ms']}ms</td></tr>"

    # 修复日志
    fl = ""
    if H.fix_log:
        fl = "<div class='card'><h2>🔧 修复日志</h2><table><tr><th>时间</th><th>用例</th><th>问题</th><th>解决方案</th><th>自动修复</th></tr>"
        for fix in H.fix_log:
            auto = "✅ 是" if fix["auto_fixed"] else "📝 否"
            fl += f"<tr><td>{fix['time']}</td><td>{fix['case']}</td><td>{fix['problem']}</td><td>{fix['solution']}</td><td>{auto}</td></tr>"
        fl += "</table></div>"

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>Case-Manager 全功能测试报告</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--primary:#19c8b9;--text:#794f27;--text-secondary:#9f927d;--bg:#f8f8f0;--bg-content:rgb(247,243,223);--border:#c4b89e;--success:#6fba2c;--error:#e05a5a;--warn:#e8a020;--r-lg:24px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Nunito,'Noto Sans SC',sans-serif;font-weight:500;background:var(--bg);color:var(--text);line-height:1.6}}
.page{{max-width:1200px;margin:0 auto;padding:40px 32px 60px}}
h1{{font-weight:900;font-size:32px}}h1 span{{color:var(--primary)}}
h2{{font-weight:700;font-size:18px;margin-bottom:12px}}
.subtitle{{color:var(--text-secondary);font-size:14px;margin-top:4px}}
.card{{background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-lg);padding:24px;margin-bottom:20px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px}}
.kpi{{background:var(--bg-content);border:2px solid var(--border);border-radius:18px;padding:20px;text-align:center}}
.kpi-value{{font-size:36px;font-weight:900;color:var(--primary)}}
.kpi-label{{font-size:13px;color:var(--text-secondary);margin-top:4px}}
.kpi--fail .kpi-value{{color:var(--error)}}.kpi--pass .kpi-value{{color:var(--success)}}
.kpi--warn .kpi-value{{color:var(--warn)}}
table{{width:100%;border-collapse:collapse}}
th{{font-weight:700;font-size:12px;color:var(--text-secondary);padding:12px 14px;border-bottom:2px solid rgba(139,115,85,0.15);text-transform:uppercase;text-align:left}}
td{{padding:10px 14px;font-size:13px;border-bottom:1px solid rgba(139,115,85,0.06);vertical-align:top}}
.pass-row{{background:rgba(111,186,44,0.04)}}.fail-row{{background:rgba(224,90,90,0.05)}}.skip-row{{background:rgba(159,146,125,0.03);color:#9f927d}}
.heat{{font-family:monospace;letter-spacing:2px;color:var(--primary)}}
.actual,.expected{{font-size:11px;color:var(--text-secondary);max-width:300px;word-break:break-all}}
.ss-wrap{{margin-top:8px;border:1px dashed var(--border);border-radius:10px;padding:8px;background:#faf9f4}}
.ss-img{{max-width:280px;max-height:160px;cursor:pointer;border-radius:8px;display:block;margin-top:6px}}
.ss-img.expanded{{max-width:900px;max-height:700px;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:9999;box-shadow:0 8px 40px rgba(0,0,0,0.3);border:3px solid var(--primary)}}
.ss-link{{font-size:12px;color:var(--primary);text-decoration:underline;cursor:pointer;white-space:nowrap}}.ss-link:hover{{color:var(--error)}}
.fix-note{{margin-top:6px;padding:6px 10px;background:rgba(232,160,32,0.08);border-left:3px solid var(--warn);border-radius:0 8px 8px 0;font-size:12px;color:#8b6914}}.cause-note{{margin-top:6px;padding:6px 10px;background:rgba(224,90,90,0.06);border-left:3px solid var(--error);border-radius:0 8px 8px 0;font-size:12px;color:#a04030}}.repro-note{{margin-top:4px;padding:4px 10px;background:rgba(25,200,185,0.05);border-left:3px solid var(--primary);border-radius:0 8px 8px 0;font-size:11px;color:#5a7060}}.suggest-note{{margin-top:4px;padding:4px 10px;background:rgba(111,186,44,0.05);border-left:3px solid var(--success);border-radius:0 8px 8px 0;font-size:11px;color:#5a7a30}}
.conclusion{{font-size:16px;font-weight:700;padding:16px 20px;border-radius:16px;margin-top:24px}}
.conclusion--pass{{background:rgba(111,186,44,0.1);color:#5a9e1e}}
.conclusion--fail{{background:rgba(224,90,90,0.1);color:#c0392b}}
.fix-log-table td{{font-size:12px}}
</style></head><body><div class="page">
<h1>🧪 Case-Manager <span>全功能测试报告</span></h1>
<p class="subtitle">模块: case-manager | 时间: {now} | 总耗时: {total_ms}ms | 环境: Django + Playwright + Vite</p>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-value">{total}</div><div class="kpi-label">总用例数</div></div>
  <div class="kpi kpi--pass"><div class="kpi-value">{p}</div><div class="kpi-label">通过</div></div>
  <div class="kpi kpi--fail"><div class="kpi-value">{f}</div><div class="kpi-label">失败</div></div>
  <div class="kpi kpi--warn"><div class="kpi-value">{s}</div><div class="kpi-label">跳过</div></div>
  <div class="kpi"><div class="kpi-value">{rate:.0f}%</div><div class="kpi-label">通过率</div></div>
</div>
<div class="card"><h2>📊 层次覆盖</h2><table><tr><th>层</th><th>用例</th><th>通过</th><th>失败</th><th>通过率</th><th>热力</th></tr>{dr}</table></div>
{fl}
<div class="card"><h2>📋 用例详情</h2><table><tr><th></th><th>编号</th><th>层</th><th>描述</th><th>实际值 / 截图</th><th>预期值</th><th>耗时</th></tr>{cr}</table></div>
<div class="conclusion {'conclusion--pass' if f==0 else 'conclusion--fail'}">
{'✅ 全部通过 — case-manager 全功能正常' if f==0 else f'⚠️ {f}/{total} 条失败，需排查。下方修复日志记录了处理过程。'}</div>
</div><script>function toggleSS(id){{var el=document.getElementById(id);el.style.display=el.style.display==='none'?'block':'none';}}</script></body></html>"""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = H.REPORTS_DIR / f"report_{ts}.html"
    path.write_text(html, encoding="utf-8")
    latest = H.REPORTS_DIR / "report_latest.html"
    if latest.exists() or latest.is_symlink(): latest.unlink()
    latest.symlink_to(path.name)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Case-Manager Full Functional Tests")
    parser.add_argument("--case", action="append", help="只运行指定用例 (可多次使用)")
    parser.add_argument("--layer", choices=["DB","API","UI","WHITE","DATA"], help="按层次筛选")
    args = parser.parse_args()

    print("=" * 58)
    print("  Case-Manager 全功能自动化测试")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  层次: {args.layer or 'ALL'}  |  Django ORM: {'✅' if H._django_ready else '❌'}")
    print(f"  Playwright: {'✅' if H._playwright_ready else '❌'}  |  用例: {len(H.ALL_TESTS)}")
    print("=" * 58)

    try:
        r = H.requests.get(f"{H.API_BASE}/", timeout=3)
        print(f"  Django API: {'✅ ONLINE' if r.ok else '❌ OFFLINE'}")
    except Exception:
        print("  Django API: ❌ OFFLINE\n  请先启动: python run.py start")
        sys.exit(1)

    needs_browser = (not args.layer) or args.layer in ("UI","DATA")
    has_ui = any(l=="UI" for l,_,_ in H.ALL_TESTS.values())

    t0 = time.time()
    if needs_browser and has_ui and H._playwright_ready:
        with H.sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width":1440,"height":900}, locale="zh-CN")
            page = ctx.new_page()
            print("\n🔐 登录中...")
            H.playwright_login(page)
            print(f"\n🧪 执行测试...\n")
            passed, failed, skipped = run_tests(page=page, case_ids=args.case if args.case else None,
                                                 layer=args.layer)
            browser.close()
    elif needs_browser and not H._playwright_ready:
        print("\n⚠️  Playwright 未安装，跳过 UI 层")
        passed, failed, skipped = run_tests(page=None, case_ids=args.case if args.case else None,
                                             layer=args.layer)
    else:
        print()
        passed, failed, skipped = run_tests(page=None, case_ids=args.case if args.case else None,
                                             layer=args.layer)
    total_ms = int((time.time()-t0)*1000)

    print(f"\n🧹 清理测试数据...")
    H.cleanup_all()

    total = passed+failed+skipped
    print(f"\n{'='*58}")
    print(f"  结果: {passed} 通过 / {failed} 失败 / {skipped} 跳过 (共 {total})")
    print(f"  截图: {H.SCREENSHOTS_DIR}")
    print(f"  总耗时: {total_ms}ms")
    print(f"{'='*58}")

    report_path = generate_html_report(total_ms)
    print(f"\n📊 HTML 报告: {report_path}")
    open(report_path)  # 自动在浏览器打开
    sys.exit(0 if failed==0 else 1)
