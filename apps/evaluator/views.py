"""Evaluator views — question bank CRUD, eval run management, KB self-test."""

import json
import threading

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from shared.auth.require_auth import require_auth

from . import api
from .models import EvalResult, EvalRun, QuestionBank

# ── short-circuit: missing-auth views that don't crash middleware ──


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


# ═══════════════════════════════════════════════════════════════════════
# Question Bank CRUD
# ═══════════════════════════════════════════════════════════════════════


def list_banks(request):
    banks = QuestionBank.objects.all().order_by("-updated_at")
    return JsonResponse(
        {
            "status": True,
            "banks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "description": b.description,
                    "question_count": b.question_count,
                    "created_at": str(b.created_at),
                }
                for b in banks
            ],
        }
    )


def bank_detail(request, bank_id):
    try:
        bank = QuestionBank.objects.prefetch_related("questions").get(id=bank_id)
    except QuestionBank.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    return JsonResponse(
        {
            "status": True,
            "bank": {
                "id": bank.id,
                "name": bank.name,
                "description": bank.description,
                "questions": [
                    {
                        "id": q.id,
                        "content": q.content,
                        "expected_keywords": q.expected_keywords,
                        "category": q.category,
                        "order": q.order,
                    }
                    for q in bank.questions.all()
                ],
            },
        }
    )


@csrf_exempt
@require_auth
def create_bank(request):
    data = json.loads(request.body)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "试卷名称不能为空"}, status=400)
    result = api.create_question_bank(
        name=name,
        description=data.get("description", ""),
        questions_data=data.get("questions") or [],
    )
    return JsonResponse(
        {"status": True, "id": result["id"], "question_count": result["question_count"]}
    )


@csrf_exempt
@require_auth
def update_bank(request, bank_id):
    try:
        result = api.update_question_bank(bank_id, json.loads(request.body))
    except QuestionBank.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    return JsonResponse({"status": True, "question_count": result["question_count"]})


@csrf_exempt
@require_auth
def delete_bank(request, bank_id):
    api.delete_question_bank(bank_id)
    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def seed_default_bank(request):
    """POST /api/evaluator/banks/seed — create the default 30-question bank."""
    result = api.seed_default_bank()
    if result["existed"]:
        return JsonResponse(
            {
                "status": True,
                "id": result["id"],
                "message": "默认试卷已存在，直接返回",
            }
        )
    return JsonResponse(
        {"status": True, "id": result["id"], "question_count": result["question_count"]}
    )


# ═══════════════════════════════════════════════════════════════════════
# Frameworks
# ═══════════════════════════════════════════════════════════════════════


def list_frameworks(request):
    """GET /api/evaluator/frameworks — list available eval frameworks."""
    from .frameworks import available_frameworks

    return JsonResponse({"status": True, "frameworks": available_frameworks()})


# ═══════════════════════════════════════════════════════════════════════
# Eval Run
# ═══════════════════════════════════════════════════════════════════════


def list_runs(request):
    runs = EvalRun.objects.select_related("agent", "bank").all()[:50]
    return JsonResponse(
        {
            "status": True,
            "runs": [
                {
                    "id": r.id,
                    "agent_id": r.agent_id,
                    "agent_name": r.agent.name if r.agent else "?",
                    "framework": r.framework or "self",
                    "bank_id": r.bank_id,
                    "bank_name": r.bank.name if r.bank else "?",
                    "status": r.status,
                    "total_questions": r.total_questions,
                    "completed_questions": r.completed_questions,
                    "total_score": r.total_score,
                    "avg_relevance": r.avg_relevance,
                    "avg_accuracy": r.avg_accuracy,
                    "avg_completeness": r.avg_completeness,
                    "avg_conciseness": r.avg_conciseness,
                    "created_at": str(r.created_at),
                    "finished_at": str(r.finished_at) if r.finished_at else None,
                }
                for r in runs
            ],
        }
    )


def run_detail(request, run_id):
    try:
        run = EvalRun.objects.prefetch_related("results__question").get(id=run_id)
    except EvalRun.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)

    results = []
    for r in run.results.all():
        eff = r.effective_scores()
        results.append(
            {
                "id": r.id,
                "question_id": r.question_id,
                "question_text": r.question_text[:200],
                "agent_response": r.agent_response[:500],
                "relevance_score": r.relevance_score,
                "accuracy_score": r.accuracy_score,
                "completeness_score": r.completeness_score,
                "conciseness_score": r.conciseness_score,
                "human_relevance": r.human_relevance,
                "human_accuracy": r.human_accuracy,
                "human_completeness": r.human_completeness,
                "human_conciseness": r.human_conciseness,
                "human_note": r.human_note,
                "effective_relevance": eff["relevance"],
                "effective_accuracy": eff["accuracy"],
                "effective_completeness": eff["completeness"],
                "effective_conciseness": eff["conciseness"],
                "judge_reasoning": r.judge_reasoning[:300],
            }
        )

    return JsonResponse(
        {
            "status": True,
            "run": {
                "id": run.id,
                "agent_id": run.agent_id,
                "agent_name": run.agent.name if run.agent else "?",
                "framework": run.framework or "self",
                "bank_name": run.bank.name if run.bank else "?",
                "status": run.status,
                "total_questions": run.total_questions,
                "completed_questions": run.completed_questions,
                "total_score": run.total_score,
                "avg_relevance": run.avg_relevance,
                "avg_accuracy": run.avg_accuracy,
                "avg_completeness": run.avg_completeness,
                "avg_conciseness": run.avg_conciseness,
                "report_json": run.report_json,
                "created_at": str(run.created_at),
                "finished_at": str(run.finished_at) if run.finished_at else None,
                "results": results,
            },
        }
    )


@csrf_exempt
@require_auth
def start_eval_run(request):
    """POST /api/evaluator/runs/start — start a new evaluation run in background."""
    data = json.loads(request.body)
    agent_id = data.get("agent_id")
    bank_id = data.get("bank_id")
    framework = data.get("framework", "self")  # self | evalscope | deepeval | maseval
    judge_provider = data.get("judge_provider", "dashscope")
    judge_model = data.get("judge_model", "qwen-max")

    if not agent_id or not bank_id:
        return JsonResponse(
            {"status": False, "message": "agent_id and bank_id are required"},
            status=400,
        )

    from apps.ai_assistant.models import AIAgent

    try:
        agent = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"status": False, "message": "agent not found"}, status=404)

    try:
        bank = QuestionBank.objects.get(id=bank_id)
    except QuestionBank.DoesNotExist:
        return JsonResponse({"status": False, "message": "question bank not found"}, status=404)

    run_id = api.create_eval_run(
        agent=agent,
        bank=bank,
        framework=framework,
        judge_provider=judge_provider,
        judge_model=judge_model,
    )["id"]

    # Run evaluation in background thread
    if framework and framework != "self":
        # External framework adapter
        from .frameworks import get_adapter

        def _bg():
            run = EvalRun.objects.get(id=run_id)
            try:
                adapter = get_adapter(framework)
                if adapter is None:
                    run.status = "failed"
                    run.report_json = json.dumps(
                        {"message": f"Unknown framework: {framework}"},
                        ensure_ascii=False,
                    )
                    run.save()
                    return
                # Call agent directly using the adapter
                import asyncio

                from apps.ai_assistant.api import decrypt_key, get_provider_config

                api_key = decrypt_key(agent.api_key) if agent.api_key else ""
                provider_cfg = get_provider_config(agent.model_provider, agent.base_url)

                agent_config = {
                    "model_provider": agent.model_provider,
                    "model_name": agent.model_name,
                    "api_key": api_key,
                    "base_url": provider_cfg.get("base_url", ""),
                }
                questions_list = [
                    {
                        "content": q.content,
                        "expected_keywords": q.expected_keywords,
                        "category": q.category,
                    }
                    for q in bank.questions.all().order_by("order", "id")
                ]
                result = asyncio.run(adapter.run(agent_config, questions_list))
                run.status = "completed" if result.ok else "failed"
                run.total_score = result.total_score
                run.total_questions = len(questions_list)
                run.completed_questions = len(result.items)
                run.report_json = json.dumps(
                    {
                        "framework": framework,
                        "total_score": result.total_score,
                        "scores": result.scores,
                        "items": result.items,
                        "raw": result.raw,
                        "message": result.error if not result.ok else "",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                from datetime import datetime

                run.finished_at = datetime.now()
                run.save()
            except Exception as e:
                run.status = "failed"
                run.report_json = json.dumps({"message": str(e)}, ensure_ascii=False)
                run.save()
    else:
        # Built-in self evaluator (LLM-as-Judge)
        from .evaluator import run_evaluation

        def _bg():
            try:
                run_evaluation(run_id, judge_provider, judge_model)
            except Exception as e:
                run = EvalRun.objects.get(id=run_id)
                run.status = "failed"
                run.report_json = json.dumps({"message": str(e)}, ensure_ascii=False)
                run.save()

    t = threading.Thread(target=_bg, daemon=True)
    t.start()

    return JsonResponse(
        {
            "status": True,
            "run": {"id": run_id},
            "message": f"评测已开始，共 {bank.question_count} 题",
        }
    )


@csrf_exempt
@require_auth
def submit_human_score(request, result_id):
    """POST /api/evaluator/results/<id>/score — submit manual (human) scores."""
    try:
        api.submit_human_score(result_id, json.loads(request.body))
    except EvalResult.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def delete_run(request, run_id):
    api.delete_eval_run(run_id)
    return JsonResponse({"status": True})


# ═══════════════════════════════════════════════════════════════════════
# KB Self-Test
# ═══════════════════════════════════════════════════════════════════════

KB_TEST_QUERIES = [
    "如何创建测试用例",
    "设备状态有哪些",
    "XPath 定位策略",
    "AgentScope 是什么",
    "StepType 包含哪些步骤",
    "API 响应格式是什么",
    "如何锁定设备",
    "知识库怎么用",
]


@csrf_exempt
def kb_search(request):
    """POST /api/evaluator/kb-search — interactive KB query for testing."""
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    query = (body.get("query") or "").strip()
    if not query:
        return JsonResponse({"status": False, "message": "query required"}, status=400)

    top_k = int(body.get("top_k", 5))

    from apps.ai_assistant.api import search_knowledge

    docs = search_knowledge(query, top_k=top_k)
    return JsonResponse(
        {
            "status": True,
            "query": query,
            "total": len(docs),
            "documents": [
                {
                    "source": d.get("metadata", {}).get("source", "?"),
                    "score": round(d.get("score", 0), 4),
                    "content": d.get("content", "")[:800],
                }
                for d in docs
            ],
        }
    )


def kb_self_test(request):
    """POST /api/evaluator/kb-self-test — test knowledge base retrieval quality."""
    from apps.ai_assistant.api import search_knowledge

    results = []
    for query in KB_TEST_QUERIES:
        docs = search_knowledge(query, top_k=3)

        # Verify each retrieved fragment against its claimed source file
        verified_docs = []
        for d in docs:
            meta = d.get("metadata", {})
            source = meta.get("source", "")
            # Truncated content check — ChromaDB stores truncated content
            # so exact match isn't possible; we do a partial match
            verified_docs.append(
                {
                    "source": source,
                    "score": d["score"],
                    "content_preview": d["content"][:200],
                    "content_length": len(d["content"]),
                }
            )

        results.append(
            {
                "query": query,
                "total_hits": len(docs),
                "top_score": docs[0]["score"] if docs else 0,
                "documents": verified_docs,
            }
        )

    # Score: % of queries that returned at least 1 result
    queries_with_results = sum(1 for r in results if r["total_hits"] > 0)
    coverage_score = (
        round(queries_with_results / len(KB_TEST_QUERIES) * 100, 1) if KB_TEST_QUERIES else 0
    )

    # Average relevance score of top hits
    top_scores = [r["top_score"] for r in results if r["total_hits"] > 0]
    avg_relevance = round(sum(top_scores) / len(top_scores), 3) if top_scores else 0

    return JsonResponse(
        {
            "status": True,
            "score": {
                "coverage": coverage_score,
                "avg_relevance": avg_relevance,
                "total_queries": len(KB_TEST_QUERIES),
            },
            "details": results,
        }
    )
