"""report-generator HTTP routes — endpoints under /api/reports/*."""
from datetime import datetime, timedelta
from pathlib import Path
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt

# ── Shared Q objects for test result filtering ──
# Used in Count('results', filter=...) on TestRunRecord → needs results__ prefix
PASS_Q = Q(results__result__iexact="pass") | Q(results__result__iexact="passed")
FAIL_Q = Q(results__result__iexact="fail") | Q(results__result__iexact="failed")

# Used directly on TestResult queries → no prefix needed
PASS_Q_DIRECT = Q(result__iexact="pass") | Q(result__iexact="passed")
FAIL_Q_DIRECT = Q(result__iexact="fail") | Q(result__iexact="failed")


def _safe_pct(part, total):
    """Return percentage as float, 0 if total is 0."""
    if total == 0:
        return 0.0
    return round(part / total * 100, 1)


# ── Helpers ──

def _compute_duration(started_at, finished_at):
    """Return human-readable duration string from two ISO timestamps."""
    if not started_at or not finished_at:
        return ""
    try:
        t1 = datetime.fromisoformat(started_at)
        t2 = datetime.fromisoformat(finished_at)
        secs = int((t2 - t1).total_seconds())
        if secs >= 60:
            return f"{secs // 60}m{secs % 60}s"
        return f"{secs}s"
    except Exception:
        return ""


# ── Run-level reports (DB-driven) ──

def _resolve_run_row(r, task_map):
    """Build a single run dict from TestRunRecord + optional TaskCard."""
    tc = task_map.get(r.client_task_id)
    if tc:
        total = tc.overall_pass + tc.overall_fail
        passed = tc.overall_pass
        failed = tc.overall_fail
        case_count = len(tc.case_ids) if tc.case_ids else 0
    else:
        case_count = len(r.selected_cases) if r.selected_cases else 0
        total = r.total or 0
        passed = r.passed or 0
        failed = total - passed
    rate = round(passed / total * 100) if total else 0
    return {
        "run_id": r.run_id,
        "status": r.status,
        "device_serial": r.device_serial,
        "loop_count": tc.loop_count if tc else r.loop_count,
        "case_count": case_count,
        "total": total,
        "passed": passed,
        "failed": failed,
        "rate": rate,
        "duration": _compute_duration(r.started_at, r.finished_at),
        "started_at": r.started_at,
        "finished_at": r.finished_at,
        "client_task_id": r.client_task_id or "",
        "task_name": tc.name if tc else None,
        "creator": tc.creator if tc else None,
        "outcome": tc.outcome if tc else None,
    }


PASS_RESULTS = {'pass', 'passed'}
FAIL_RESULTS = {'fail', 'failed', 'stopped'}


def _filter_run_queryset(request):
    """Apply shared report list filters to a TestRunRecord queryset."""
    from apps.test_runner.models import TestRunRecord, TaskCard

    qs = TestRunRecord.objects.all()

    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    if start_date:
        qs = qs.filter(started_at__gte=start_date)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            qs = qs.filter(started_at__lt=end_dt.isoformat())
        except ValueError:
            pass

    run_id = request.GET.get('run_id', '').strip()
    task_name = request.GET.get('task_name', '').strip()
    device_serial = request.GET.get('device_serial', '').strip()
    creator = request.GET.get('creator', '').strip()

    if run_id:
        qs = qs.filter(run_id__icontains=run_id)
    if device_serial:
        qs = qs.filter(device_serial__icontains=device_serial)
    if task_name:
        task_ids = TaskCard.objects.filter(name__icontains=task_name).values_list('task_id', flat=True)
        qs = qs.filter(client_task_id__in=task_ids)
    if creator:
        task_ids = TaskCard.objects.filter(creator__icontains=creator).values_list('task_id', flat=True)
        qs = qs.filter(client_task_id__in=task_ids)

    return qs


def _build_case_title_map(run_record):
    title_map = {}
    for sc in (run_record.selected_cases or []):
        cid = sc.get('case_id', '')
        if cid:
            title_map[str(cid)] = sc.get('title', cid)
    return title_map


def _failed_steps_for_case(failed_steps, case_title, case_id):
    matched = []
    for fs in (failed_steps or []):
        fs_title = fs.get('caseTitle') or ''
        fs_id = str(fs.get('caseId') or '')
        if fs_title == case_title or fs_id == case_id or fs_title == case_id:
            matched.append(fs)
    return matched


def _result_matches_type(result, result_type):
    res = (result or '').lower()
    if result_type == 'pass':
        return res in PASS_RESULTS
    if result_type == 'fail':
        return res in FAIL_RESULTS
    return False


@csrf_exempt
def list_reports(request):
    """GET /api/reports — List execution runs with optional filters + KPI summary.

    Query params:
        start_date      ISO date string (e.g. 2026-07-01)
        end_date        ISO date string (e.g. 2026-07-13)
        run_id          partial match on run_id
        task_name       partial match on linked TaskCard name
        device_serial   partial match on device serial
        creator         partial match on linked TaskCard creator
    """
    from apps.test_runner.models import TestRunRecord, TaskCard

    qs = _filter_run_queryset(request)

    # ── Annotate with pass/fail counts ──
    annotated = qs.annotate(
        total=Count('results'),
        passed=Count('results', filter=PASS_Q),
    )

    # ── All matching rows (KPI / trend / table share the same filtered set) ──
    rows = list(annotated.order_by('-id'))

    # ── Bulk-fetch TaskCard data (single query, no N+1) ──
    client_task_ids = [r.client_task_id for r in rows if r.client_task_id]
    task_map = {}
    if client_task_ids:
        tcs = TaskCard.objects.filter(task_id__in=client_task_ids).only(
            'task_id', 'name', 'creator', 'outcome',
            'overall_pass', 'overall_fail', 'case_ids', 'loop_count',
        )
        task_map = {tc.task_id: tc for tc in tcs}

    runs = [_resolve_run_row(r, task_map) for r in rows]

    # ── KPI summary: aggregate from TaskCard data when available ──
    # Recompute over displayed rows using the resolved pass/fail values
    summary_total_pass = sum(r['passed'] for r in runs)
    summary_total_fail = sum(r['failed'] for r in runs)
    summary_total_iterations = summary_total_pass + summary_total_fail

    # ── Daily trend: fill chart window (week / month / quarter) ──
    chart_range = request.GET.get('chart_range', '30').strip()
    try:
        range_days = int(chart_range)
    except ValueError:
        range_days = 30
    if range_days not in (7, 30, 90):
        range_days = 30
    trend = _build_trend_from_runs(runs, range_days)

    return JsonResponse({
        "ok": True,
        "summary": {
            "total_runs": len(runs),
            "total_iterations": summary_total_iterations,
            "total_pass": summary_total_pass,
            "total_fail": summary_total_fail,
            "pass_rate": _safe_pct(summary_total_pass, summary_total_iterations),
        },
        "bug_summary": {
            k: v for k, v in _build_bug_summary(
                _collect_case_groups(request, 'fail')[0]
            ).items() if k != 'cases'
        },
        "trend": trend,
        "runs": runs,
    })


def _build_trend_from_runs(runs, range_days=30):
    """Build daily pass/fail/rate trend with zero-filled days for chart scrolling."""
    from collections import defaultdict
    from datetime import date, timedelta

    daily = defaultdict(lambda: {"pass": 0, "fail": 0})
    for r in runs:
        if r.get("started_at"):
            day = r["started_at"][:10]
            daily[day]["pass"] += r.get("passed", 0) or 0
            daily[day]["fail"] += r.get("failed", 0) or 0

    end = date.today()
    for day_key in daily.keys():
        try:
            d = date.fromisoformat(day_key)
            if d > end:
                end = d
        except ValueError:
            pass

    start = end - timedelta(days=range_days - 1)
    dates = []
    labels = []
    pass_list = []
    fail_list = []
    rate_list = []

    d = start
    while d <= end:
        key = d.isoformat()
        dates.append(key)
        labels.append(f"{d.month:02d}-{d.day:02d}")
        p = daily[key]["pass"] if key in daily else 0
        f = daily[key]["fail"] if key in daily else 0
        pass_list.append(p)
        fail_list.append(f)
        total = p + f
        rate_list.append(round(p / total * 100, 1) if total else 0)
        d += timedelta(days=1)

    return {
        "range_days": range_days,
        "dates": dates,
        "labels": labels,
        "pass": pass_list,
        "fail": fail_list,
        "rate": rate_list,
    }


def _accumulate_case_entry(cases_map, case_title, case_id, task_id, task_name, run_id, count):
    """Add pass/fail counts into the hierarchical cases_map."""
    if count <= 0:
        return
    if case_title not in cases_map:
        cases_map[case_title] = {
            'case_title': case_title,
            'case_id': case_id,
            'count': 0,
            'tasks': {},
        }
    centry = cases_map[case_title]
    centry['count'] += count
    if case_id and not centry['case_id']:
        centry['case_id'] = case_id
    if task_id not in centry['tasks']:
        centry['tasks'][task_id] = {
            'task_id': task_id,
            'task_name': task_name,
            'run_id': run_id,
            'count': 0,
            'failed_steps': [],
        }
    centry['tasks'][task_id]['count'] += count


def _failure_signature(step):
    """Normalize a failed step into a deduplication key."""
    return (
        (step.get('stepType') or '').strip(),
        (step.get('description') or '').strip(),
        (step.get('result') or '').strip(),
    )


def _build_bug_summary(groups):
    """Aggregate failures by case; identical issues are merged with occurrence count."""
    cases_out = []
    unique_issues = 0
    total_occurrences = 0

    for group in groups:
        issue_map = {}

        for task in group.get('tasks', []):
            steps = task.get('failed_steps') or []
            remainder = max(0, (task.get('count') or 0) - len(steps))

            for step in steps:
                sig = _failure_signature(step)
                if sig not in issue_map:
                    issue_map[sig] = {
                        'step_type': sig[0],
                        'description': sig[1],
                        'result': sig[2],
                        'count': 0,
                        'task_ids': set(),
                    }
                issue_map[sig]['count'] += 1
                issue_map[sig]['task_ids'].add(task.get('task_id', ''))

            if remainder > 0:
                sig = ('iteration', '执行失败（无步骤明细）', 'fail')
                if sig not in issue_map:
                    issue_map[sig] = {
                        'step_type': sig[0],
                        'description': sig[1],
                        'result': sig[2],
                        'count': 0,
                        'task_ids': set(),
                    }
                issue_map[sig]['count'] += remainder
                issue_map[sig]['task_ids'].add(task.get('task_id', ''))

        if not issue_map:
            continue

        issues = []
        for issue in sorted(issue_map.values(), key=lambda x: (-x['count'], x['description'])):
            issues.append({
                'step_type': issue['step_type'],
                'description': issue['description'],
                'result': issue['result'],
                'count': issue['count'],
                'task_count': len(issue['task_ids']),
                'task_ids': sorted(t for t in issue['task_ids'] if t),
            })

        case_occurrences = sum(i['count'] for i in issues)
        cases_out.append({
            'case_title': group['case_title'],
            'case_id': group.get('case_id', ''),
            'issue_count': len(issues),
            'total_occurrences': case_occurrences,
            'issues': issues,
        })
        unique_issues += len(issues)
        total_occurrences += case_occurrences

    return {
        'unique_issues': unique_issues,
        'total_occurrences': total_occurrences,
        'affected_cases': len(cases_out),
        'cases': cases_out,
    }


def _collect_case_groups(request, result_type):
    """Build hierarchical case groups for pass/fail breakdown."""
    from collections import defaultdict
    from apps.test_runner.models import TaskCard, TestResult

    rows = list(_filter_run_queryset(request).order_by('-id'))
    run_db_ids = [r.id for r in rows]

    client_task_ids = list({r.client_task_id for r in rows if r.client_task_id})
    task_map = {}
    if client_task_ids:
        for tc in TaskCard.objects.filter(task_id__in=client_task_ids).only(
            'task_id', 'name', 'case_items', 'failed_steps',
        ):
            task_map[tc.task_id] = tc

    results_by_run = defaultdict(list)
    if run_db_ids:
        for tr in TestResult.objects.filter(run_id__in=run_db_ids):
            results_by_run[tr.run_id].append(tr)

    cases_map = {}
    total_count = 0
    steps_attached = set()

    for r in rows:
        tc = task_map.get(r.client_task_id)
        task_id = r.client_task_id or r.run_id
        task_name = (tc.name if tc else None) or task_id

        if tc and tc.case_items:
            for ci in tc.case_items:
                case_id = str(ci.get('id', ''))
                case_title = ci.get('title', case_id) or case_id
                passed = ci.get('pass', 0) or 0
                failed = ci.get('fail', 0) or 0
                cnt = passed if result_type == 'pass' else failed
                if cnt <= 0:
                    continue

                total_count += cnt
                _accumulate_case_entry(
                    cases_map, case_title, case_id, task_id, task_name, r.run_id, cnt,
                )

                if result_type == 'fail':
                    step_key = (task_id, case_title)
                    if step_key not in steps_attached and tc.failed_steps:
                        steps = _failed_steps_for_case(tc.failed_steps, case_title, case_id)
                        if steps:
                            tentry = cases_map[case_title]['tasks'][task_id]
                            existing = {
                                (s.get('iteration'), s.get('stepIndex'))
                                for s in tentry['failed_steps']
                            }
                            for step in sorted(
                                steps,
                                key=lambda s: (s.get('iteration', 0), s.get('stepIndex', 0)),
                            ):
                                key = (step.get('iteration'), step.get('stepIndex'))
                                if key not in existing:
                                    tentry['failed_steps'].append(step)
                                    existing.add(key)
                            steps_attached.add(step_key)
            continue

        title_map = _build_case_title_map(r)
        for tr in results_by_run.get(r.id, []):
            if not _result_matches_type(tr.result, result_type):
                continue

            cid = str(tr.case_id) if tr.case_id else 'unknown'
            case_title = title_map.get(cid, cid)
            total_count += 1
            _accumulate_case_entry(
                cases_map, case_title, cid, task_id, task_name, r.run_id, 1,
            )

            if result_type == 'fail':
                tentry = cases_map[case_title]['tasks'][task_id]
                tentry['failed_steps'].append({
                    'caseTitle': case_title,
                    'caseId': cid,
                    'iteration': tr.iteration,
                    'stepIndex': -1,
                    'stepType': 'iteration',
                    'description': tr.detail or f"第 {tr.iteration} 轮执行失败",
                    'result': tr.result,
                })

    groups = []
    for centry in sorted(cases_map.values(), key=lambda c: c['case_title']):
        tasks = sorted(centry['tasks'].values(), key=lambda t: t['task_id'])
        if result_type == 'pass':
            for t in tasks:
                t.pop('failed_steps', None)
        else:
            for t in tasks:
                t['failed_steps'].sort(
                    key=lambda s: (s.get('iteration', 0), s.get('stepIndex', 0)),
                )
        groups.append({
            'case_title': centry['case_title'],
            'case_id': centry['case_id'],
            'count': centry['count'],
            'tasks': tasks,
        })

    return groups, total_count


@csrf_exempt
def case_breakdown(request):
    """GET /api/reports/cases — Hierarchical pass/fail case list under current filters.

    Uses TaskCard.case_items (same source as KPI summary), with TestResult fallback.

    Query params:
        result          required: pass | fail
        (+ same filters as list_reports)
    """
    result_type = request.GET.get('result', '').strip().lower()
    if result_type not in ('pass', 'fail'):
        return JsonResponse({"ok": False, "error": "result 必须为 pass 或 fail"}, status=400)

    groups, total_count = _collect_case_groups(request, result_type)

    payload = {
        "ok": True,
        "result_type": result_type,
        "total": total_count,
        "case_count": len(groups),
        "groups": groups,
    }
    if result_type == 'fail':
        bug_summary = _build_bug_summary(groups)
        payload["bug_summary"] = bug_summary

    return JsonResponse(payload)


@csrf_exempt
def run_report(request, run_id):
    """GET /api/reports/run/{run_id} — Full aggregated report for a single run."""
    from apps.test_runner.models import TestRunRecord, TestResult, TaskCard

    try:
        run_record = TestRunRecord.objects.get(run_id=run_id)
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)

    # ── Fetch linked TaskCard metadata ──
    task_card = None
    if run_record.client_task_id:
        try:
            task_card = TaskCard.objects.get(task_id=run_record.client_task_id)
        except TaskCard.DoesNotExist:
            task_card = None

    # ── Build case breakdown ──
    # TaskCard.case_items is source of truth for aggregate pass/fail counts.
    # TestResult rows provide per-iteration detail (result, duration, error info).
    cases = []
    total_pass = 0
    total_fail = 0

    # Always fetch TestResult for iteration-level details
    results_qs = TestResult.objects.filter(run=run_record).order_by('case_id', 'iteration')

    # Build title lookup from selected_cases snapshot
    title_map = {}
    for sc in (run_record.selected_cases or []):
        cid = sc.get("case_id", "")
        if cid:
            title_map[cid] = sc.get("title", cid)

    # Build iteration map from TestResult: case_id → [iteration_details]
    iter_map = {}
    for r in results_qs:
        cid = r.case_id or "unknown"
        if cid not in iter_map:
            iter_map[cid] = {"iterations": [], "title": title_map.get(cid, cid)}
        iter_map[cid]["iterations"].append({
            "iteration": r.iteration,
            "result": r.result,
            "duration_ms": round(r.duration_ms, 1) if r.duration_ms else 0,
            "detail": r.detail or "",
        })

    if task_card and task_card.case_items:
        # Use TaskCard aggregates + TestResult iteration details
        for ci in task_card.case_items:
            cid = str(ci.get('id', ''))
            p = ci.get('pass', 0) or 0
            f = ci.get('fail', 0) or 0
            it_info = iter_map.get(cid, {})
            cases.append({
                "case_id": cid,
                "case_title": ci.get('title', it_info.get('title', cid)),
                "planned": task_card.loop_count,
                "actual": p + f,
                "pass": p,
                "fail": f,
                "rate": round(p / (p + f) * 100) if (p + f) else 0,
                "iterations": it_info.get("iterations", []),
            })
            total_pass += p
            total_fail += f
    else:
        # Fallback: aggregate everything from TestResult rows
        for cid, it_info in iter_map.items():
            p = sum(1 for it in it_info["iterations"] if it["result"] == "pass")
            f = len(it_info["iterations"]) - p
            planned = run_record.loop_count
            actual = p + f
            cases.append({
                "case_id": cid,
                "case_title": it_info["title"],
                "planned": planned,
                "actual": actual,
                "pass": p,
                "fail": f,
                "rate": round(p / actual * 100) if actual else 0,
                "iterations": it_info["iterations"],
            })
            total_pass += p
            total_fail += f

    # Sort cases: failed first, then by case_id
    cases.sort(key=lambda c: (-c["fail"], c["case_id"]))

    total_iterations = total_pass + total_fail
    pass_rate = round(total_pass / total_iterations * 100, 1) if total_iterations else 0

    # Recent runs for trend chart — use TaskCard data when available
    recent_qs = (
        TestRunRecord.objects
        .annotate(
            total=Count('results'),
            passed=Count('results', filter=PASS_Q),
        )
        .order_by('-id')[:10]
    )
    # Bulk-fetch TaskCards for recent runs too
    recent_task_ids = [r.client_task_id for r in recent_qs if r.client_task_id]
    recent_task_map = {}
    if recent_task_ids:
        recent_tcs = TaskCard.objects.filter(task_id__in=recent_task_ids).only(
            'task_id', 'overall_pass', 'overall_fail',
        )
        recent_task_map = {tc.task_id: tc for tc in recent_tcs}

    recent_runs = []
    for r in reversed(list(recent_qs)):
        rtc = recent_task_map.get(r.client_task_id)
        if rtc and (rtc.overall_pass or rtc.overall_fail):
            t = rtc.overall_pass + rtc.overall_fail
            p = rtc.overall_pass
        else:
            t = r.total or 0
            p = r.passed or 0
        recent_runs.append({
            "run_id": r.run_id,
            "started_at": r.started_at,
            "total": t,
            "passed": p,
            "failed": t - p,
            "rate": round(p / t * 100) if t else 0,
        })

    return JsonResponse({
        "ok": True,
        "run": {
            "run_id": run_record.run_id,
            "status": run_record.status,
            "device_serial": run_record.device_serial,
            "loop_count": run_record.loop_count,
            "selected_cases": run_record.selected_cases,
            "started_at": run_record.started_at,
            "finished_at": run_record.finished_at,
            "duration": _compute_duration(run_record.started_at, run_record.finished_at),
            "total_iterations": total_iterations,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "pass_rate": pass_rate,
            "case_count": len(cases),
            "cases": cases,
            "recent_runs": recent_runs,
            # ── TaskCard metadata (nullable) ──
            "client_task_id": run_record.client_task_id or "",
            "task_name": task_card.name if task_card else None,
            "task_creator": task_card.creator if task_card else None,
            "task_outcome": task_card.outcome if task_card else None,
            "task_conclusion": task_card.conclusion if task_card else None,
            "task_bug_ticket": task_card.bug_ticket if task_card else None,
            "task_failed_steps": task_card.failed_steps if task_card else None,
            "task_round": task_card.round if task_card else None,
        },
    })


# ── Task-level report (TaskCard perspective) ──

@csrf_exempt
def _load_step_details_for_report(tc) -> list:
    """Load per-step screenshots from linked TestResult rows for report."""
    try:
        from apps.test_runner.models import TestResult
        if not tc.run_id:
            return []
        results = TestResult.objects.filter(run_id=tc.run_id).order_by("iteration")
        all_steps = []
        for tr in results:
            for d in (tr.step_details or []):
                d.setdefault("caseId", tr.case_id)
                d.setdefault("caseTitle", _resolve_case_title(tc, tr.case_id))
                d.setdefault("_date", str(tr.created_at)[:19] if tr.created_at else "")
            all_steps.extend(tr.step_details or [])
        return all_steps
    except Exception:
        return []


def _resolve_case_title(tc, case_id: str) -> str:
    for ci in (tc.case_items or []):
        if str(ci.get("id", "")) == str(case_id):
            return ci.get("title", case_id)
    return case_id


def task_report(request, task_id):
    """GET /api/reports/task/{task_id} — Comprehensive report from TaskCard perspective.

    Returns TaskCard metadata, case_items with steps, conclusion, bug analysis,
    and linked TestRunRecord summaries.
    """
    from apps.test_runner.models import TaskCard, TestRunRecord, TestResult

    try:
        tc = TaskCard.objects.get(task_id=task_id)
    except TaskCard.DoesNotExist:
        return JsonResponse({"ok": False, "error": "task not found"}, status=404)

    # ── Linked run summaries (last 10) ──
    run_records = TestRunRecord.objects.filter(
        client_task_id=task_id
    ).order_by('-id')[:10]

    linked_runs = []
    for rr in run_records:
        agg = TestResult.objects.filter(run=rr).aggregate(
            total=Count('id'),
            passed=Count('id', filter=PASS_Q_DIRECT),
        )
        t = agg['total'] or 0
        p = agg['passed'] or 0
        linked_runs.append({
            "run_id": rr.run_id,
            "status": rr.status,
            "device_serial": rr.device_serial,
            "loop_count": rr.loop_count,
            "total": t,
            "passed": p,
            "failed": t - p,
            "rate": round(p / t * 100) if t else 0,
            "started_at": rr.started_at,
            "finished_at": rr.finished_at,
            "duration": _compute_duration(rr.started_at, rr.finished_at),
        })

    case_items = tc.case_items or []
    overall_pass = tc.overall_pass or 0
    overall_fail = tc.overall_fail or 0

    return JsonResponse({
        "ok": True,
        "task": {
            "task_id": tc.task_id,
            "name": tc.name,
            "creator": tc.creator,
            "mode": tc.mode,
            "device_serial": tc.device_serial,
            "loop_count": tc.loop_count,
            "interval_seconds": tc.interval_seconds,
            "status": tc.status,
            "outcome": tc.outcome,
            "round": tc.round,
            "conclusion": tc.conclusion,
            "bug_ticket": tc.bug_ticket,
            "failed_steps": tc.failed_steps,
            "case_ids": tc.case_ids,
            "case_items": case_items,
            "overall_pass": overall_pass,
            "overall_fail": overall_fail,
            "pass_rate": _safe_pct(overall_pass, overall_pass + overall_fail),
            "created_at": str(tc.created_at),
            "updated_at": str(tc.updated_at),
            "linked_runs": linked_runs,
            "step_details": _load_step_details_for_report(tc),
        },
    })


# ── File-based report endpoints (download / inline view) ──

@csrf_exempt
def download_report(request, filename):
    """GET /api/reports/{filename} — Download report file."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if fp.exists():
        suffix = fp.suffix.lower()
        mt = "text/csv" if suffix == ".csv" else "text/markdown" if suffix == ".md" else "text/plain"
        response = FileResponse(open(str(fp), 'rb'), content_type=mt)
        response['Content-Disposition'] = f'attachment; filename="{safe_name}"'
        return response
    return JsonResponse({"ok": False, "error": "not found"}, status=404)


@csrf_exempt
def view_report(request, filename):
    """GET /api/reports/{filename}/content — Return file content for inline viewing."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if not fp.exists():
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    try:
        content = fp.read_text(encoding="utf-8-sig")
    except Exception:
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            content = fp.read_text(encoding="latin-1")

    suffix = fp.suffix.lower()
    ftype = "csv" if suffix == ".csv" else "md" if suffix == ".md" else "log"

    rows = []
    if suffix == ".csv":
        lines = content.strip().split("\n")
        if lines:
            headers = [h.strip() for h in lines[0].split(",")]
            for line in lines[1:]:
                cols = [c.strip() for c in line.split(",")]
                if len(cols) == len(headers):
                    rows.append(dict(zip(headers, cols)))

    return JsonResponse({
        "ok": True,
        "name": safe_name,
        "type": ftype,
        "size": fp.stat().st_size,
        "content": content,
        "rows": rows,
        "headers": [h.strip() for h in content.split("\n")[0].split(",")] if suffix == ".csv" and content else [],
    })
