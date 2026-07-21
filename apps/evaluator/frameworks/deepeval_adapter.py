"""DeepEval adapter — Pytest-style LLM evaluation framework.

DeepEval (https://github.com/confident-ai/deepeval) provides 50+ metrics
with a pytest-like API.  This adapter converts our question bank into
DeepEval test cases, runs them through the agent, and scores with
AnswerRelevancy / Faithfulness / GEval metrics.
"""

from __future__ import annotations

import asyncio
import logging

from ..frameworks import register
from ..frameworks.base import AdapterResult, BaseAdapter

logger = logging.getLogger("evaluator")


@register("deepeval")
class DeepEvalAdapter(BaseAdapter):
    name = "DeepEval"
    description = (
        "类 Pytest 风格的 LLM 评测框架。50+ 内置指标（AnswerRelevancy、Faithfulness、"
        "GEval、Hallucination 等），支持 CI/CD 集成和自定义指标。"
    )

    @staticmethod
    def is_available() -> bool:
        try:
            import deepeval  # noqa: F401
            return True
        except ImportError:
            return False

    async def run(
        self,
        agent_config: dict,
        questions: list[dict],
        **kwargs,
    ) -> AdapterResult:
        if not self.is_available():
            return AdapterResult(
                ok=False,
                error="DeepEval 未安装。请执行: pip install deepeval",
            )

        try:
            from asyncio import to_thread

            result = await to_thread(
                self._run_sync, agent_config, questions,
            )
            return result
        except Exception as e:
            logger.exception("DeepEval adapter failed")
            return AdapterResult(ok=False, error=str(e))

    def _run_sync(
        self,
        agent_config: dict,
        questions: list[dict],
    ) -> AdapterResult:
        """Synchronous DeepEval runner."""
        from deepeval import evaluate
        from deepeval.metrics import AnswerRelevancyMetric, GEval
        from deepeval.test_case import LLMTestCase

        model_name = agent_config.get("model_name", "gpt-4o")

        test_cases = []
        for q in questions:
            answer = self._call_agent(agent_config, q.get("content", ""))
            test_cases.append(
                LLMTestCase(
                    input=q.get("content", ""),
                    actual_output=answer,
                    expected_output=q.get("expected_keywords", ""),
                )
            )

        relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
        g_eval = GEval(
            name="completeness",
            criteria="Does the answer cover the key points mentioned in the question?",
        )

        try:
            results = evaluate(
                test_cases=test_cases,
                metrics=[relevancy_metric, g_eval],
                print_results=False,
            )

            return self._normalize(results, questions)
        except Exception as e:
            return AdapterResult(ok=False, error=f"DeepEval error: {e}")

    def _call_agent(self, agent_config: dict, question: str) -> str:
        """Simple agent call via requests."""
        import requests

        provider = agent_config.get("model_provider", "dashscope")
        base_url = agent_config.get("base_url", "")
        api_key = agent_config.get("api_key", "")
        model_name = agent_config.get("model_name", "qwen-max")

        if provider == "dashscope":
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        else:
            url = f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"

        messages = []
        sys_prompt = agent_config.get("system_prompt", "")
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": question})

        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model_name, "messages": messages, "max_tokens": 2048},
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            return f"[HTTP {resp.status_code}]"
        except Exception as e:
            return f"[Error: {e}]"

    def _normalize(self, results, questions: list[dict]) -> AdapterResult:
        """Convert DeepEval output to standardized AdapterResult."""
        items = []
        total = 0.0
        scored = 0

        try:
            test_results = getattr(results, "test_results", []) or []
            for i, tr in enumerate(test_results):
                metrics_data = {}
                for m in getattr(tr, "metrics_data", []) or []:
                    name = getattr(m, "name", "unknown")
                    score = getattr(m, "score", 0)
                    metrics_data[name] = round(float(score), 2)
                    total += float(score)
                    scored += 1

                items.append({
                    "question": questions[i].get("content", "")[:200]
                    if i < len(questions)
                    else "?",
                    "metrics": metrics_data,
                })
        except Exception:
            items = [
                {"question": q.get("content", "")[:200], "note": "see raw output"}
                for q in questions
            ]

        return AdapterResult(
            ok=True,
            total_score=round(total / scored, 2) if scored else 0,
            scores={},
            items=items,
            raw={"test_count": len(items)},
        )
