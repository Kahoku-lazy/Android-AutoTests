"""Core evaluation engine — judges agent answers using a separate Judge LLM.

Design:
- The agent under test answers each question via its configured model API.
- A separate *Judge LLM* scores the answer on 4 dimensions (1-5 scale).
- The scoring prompt asks the judge to produce structured JSON so we can
  parse it deterministically.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime

logger = logging.getLogger("evaluator")

# ── Judge prompt template ──────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """你是一个专业的 AI 评测裁判。你的任务是对另一个 AI 助手的回答进行四维评分。

评分维度（每个维度 1-5 分）：
1. **相关性 (relevance)**：回答是否切题，是否直接回应了问题
2. **准确性 (accuracy)**：回答中的事实是否准确，有没有错误信息
3. **完整性 (completeness)**：回答是否覆盖了问题的关键要点
4. **简洁性 (conciseness)**：回答是否简洁明了，有无冗余啰嗦

请严格以 JSON 格式返回评分结果，不要输出其他内容：

{
  "relevance": <1-5>,
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "conciseness": <1-5>,
  "reasoning": "<简短评分理由，不超过200字>"
}"""


def _build_judge_messages(question: str, answer: str) -> list[dict]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": f"【问题】\n{question}\n\n【AI 回答】\n{answer}"},
    ]


def _call_judge_llm(
    messages: list[dict],
    provider: str,
    model: str,
    api_key: str,
    base_url: str = "",
) -> dict | None:
    """Call the Judge LLM and return parsed score dict, or None on failure."""
    import requests

    try:
        if provider == "dashscope":
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        else:
            url = f"{base_url.rstrip('/')}/chat/completions"

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.1,  # low temp for consistent judging
                "max_tokens": 512,
            },
            timeout=60,
        )
        if resp.status_code != 200:
            logger.warning("Judge LLM HTTP %s: %s", resp.status_code, resp.text[:200])
            return None

        body = resp.json()
        raw = body["choices"][0]["message"]["content"]
        # Try to extract JSON from the response
        return _parse_judge_response(raw)
    except Exception as e:
        logger.warning("Judge LLM call failed: %s", e)
        return None


def _parse_judge_response(raw: str) -> dict | None:
    """Extract JSON from judge LLM response.  Handles markdown code fences."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try extracting from ```json ... ``` fence
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding the first { ... } block
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse judge response: %s", raw[:200])
    return None


def call_agent_for_answer(
    question: str,
    model_provider: str,
    model_name: str,
    api_key: str,
    base_url: str = "",
    system_prompt: str = "",
    temperature: float = 0.7,
) -> str:
    """Send a single question to the agent's model and return the answer text."""
    import requests

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})

    try:
        if model_provider == "dashscope":
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        else:
            url = f"{base_url.rstrip('/')}/chat/completions"

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2048,
            },
            timeout=120,
        )
        if resp.status_code != 200:
            return f"[调用失败] HTTP {resp.status_code}: {resp.text[:300]}"

        body = resp.json()
        return body["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[调用异常] {e}"


def run_evaluation(
    run_id: int,
    judge_provider: str = "dashscope",
    judge_model: str = "qwen-max",
) -> dict:
    """Execute a full evaluation run against an EvalRun record.

    This is designed to be called from a background thread.
    Returns a summary dict.
    """
    from .models import EvalRun, EvalResult

    try:
        run = EvalRun.objects.select_related("agent", "bank").get(id=run_id)
    except EvalRun.DoesNotExist:
        return {"ok": False, "error": f"Run {run_id} not found"}

    if not run.agent or not run.bank:
        run.status = "failed"
        run.save()
        return {"ok": False, "error": "Agent or question bank missing"}

    agent = run.agent
    questions = list(run.bank.questions.all().order_by("order", "id"))

    # Decrypt agent API key
    from apps.ai_assistant.api import decrypt_key

    api_key = decrypt_key(agent.api_key) if agent.api_key else ""
    if not api_key:
        run.status = "failed"
        run.report_json = json.dumps({"error": "Agent has no API key"}, ensure_ascii=False)
        run.save()
        return {"ok": False, "error": "Agent has no API key"}

    from agentscope_service.provider_registry import get_provider_config

    provider_cfg = get_provider_config(agent.model_provider, agent.base_url)

    run.status = "running"
    run.total_questions = len(questions)
    run.judge_provider = judge_provider
    run.judge_model = judge_model
    run.save()

    # ── Need a Judge LLM API key ──
    # Use same key as agent for now; can be made separately configurable.
    judge_api_key = api_key

    results: list[dict] = []
    total_relevance = 0.0
    total_accuracy = 0.0
    total_completeness = 0.0
    total_conciseness = 0.0
    scored_count = 0

    for i, q in enumerate(questions):
        # 1. Get agent answer
        t0 = time.time()
        answer = call_agent_for_answer(
            question=q.content,
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            api_key=api_key,
            base_url=provider_cfg.get("base_url", ""),
            system_prompt=agent.system_prompt or "",
            temperature=agent.temperature,
        )
        answer_latency = round(time.time() - t0, 2)

        # 2. Judge the answer
        judge_msgs = _build_judge_messages(q.content, answer)
        scores = _call_judge_llm(
            judge_msgs,
            provider=judge_provider if judge_provider != "dashscope" else agent.model_provider,
            model=judge_model,
            api_key=judge_api_key,
            base_url=provider_cfg.get("base_url", ""),
        )

        rel = scores.get("relevance", 0) if scores else 0
        acc = scores.get("accuracy", 0) if scores else 0
        com = scores.get("completeness", 0) if scores else 0
        con = scores.get("conciseness", 0) if scores else 0
        reasoning = scores.get("reasoning", "") if scores else "Judge LLM 评分失败"

        # 3. Persist
        EvalResult.objects.create(
            run=run,
            question=q,
            question_text=q.content,
            agent_response=answer,
            relevance_score=rel,
            accuracy_score=acc,
            completeness_score=com,
            conciseness_score=con,
            judge_reasoning=reasoning,
        )

        if scores:
            total_relevance += rel
            total_accuracy += acc
            total_completeness += com
            total_conciseness += con
            scored_count += 1

        results.append({
            "question_id": q.id,
            "question": q.content[:100],
            "answer_preview": answer[:200],
            "scores": {"relevance": rel, "accuracy": acc, "completeness": com, "conciseness": con},
            "latency": answer_latency,
        })

        # Update progress
        run.completed_questions = i + 1
        run.save(update_fields=["completed_questions"])

    # ── Finalize ──
    if scored_count > 0:
        run.avg_relevance = round(total_relevance / scored_count, 2)
        run.avg_accuracy = round(total_accuracy / scored_count, 2)
        run.avg_completeness = round(total_completeness / scored_count, 2)
        run.avg_conciseness = round(total_conciseness / scored_count, 2)
        run.total_score = round(
            (run.avg_relevance + run.avg_accuracy + run.avg_completeness + run.avg_conciseness) / 4, 2,
        )

    run.status = "completed"
    run.finished_at = datetime.now()
    run.report_json = json.dumps({
        "questions_total": len(questions),
        "questions_scored": scored_count,
        "averages": {
            "relevance": run.avg_relevance,
            "accuracy": run.avg_accuracy,
            "completeness": run.avg_completeness,
            "conciseness": run.avg_conciseness,
        },
        "total_score": run.total_score,
        "details": results,
    }, ensure_ascii=False, indent=2)
    run.save()

    return {"ok": True, "total_score": run.total_score, "details": results}
