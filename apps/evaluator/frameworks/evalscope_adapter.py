"""EvalScope adapter — Alibaba ModelScope evaluation framework.

EvalScope (https://github.com/modelscope/evalscope) is a comprehensive
LLM/VLM evaluation framework with built-in benchmarks and custom dataset
support.  This adapter converts our question bank into EvalScope's
NativeBenchmark format, runs the evaluation, and normalizes the results.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from ..frameworks import register
from ..frameworks.base import AdapterResult, BaseAdapter

logger = logging.getLogger("evaluator")


@register("evalscope")
class EvalScopeAdapter(BaseAdapter):
    name = "EvalScope"
    description = (
        "阿里 ModelScope 出品的一站式评测框架。支持 MMLU、C-Eval、SWE-bench "
        "等标准基准 + 自定义数据集。内置 LLM-as-Judge、Arena 对战模式、Agent Trace 可视化。"
    )

    @staticmethod
    def is_available() -> bool:
        try:
            import evalscope  # noqa: F401
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
                error="EvalScope 未安装。请执行: pip install evalscope",
            )

        api_key = agent_config.get("api_key", "")
        model_name = agent_config.get("model_name", "qwen-max")
        base_url = agent_config.get("base_url", "")
        provider = agent_config.get("model_provider", "dashscope")

        if not base_url and provider == "dashscope":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        try:
            import runpy
            import sys
            from asyncio import to_thread

            # Build a temporary Python script that runs EvalScope on our dataset
            result = await to_thread(
                self._run_sync,
                questions,
                model_name,
                api_key,
                base_url,
            )
            return result
        except Exception as e:
            logger.exception("EvalScope adapter failed")
            return AdapterResult(ok=False, error=str(e))

    def _run_sync(
        self,
        questions: list[dict],
        model_name: str,
        api_key: str,
        base_url: str,
    ) -> AdapterResult:
        """Synchronous EvalScope runner — runs in a thread."""
        from evalscope import TaskConfig, run_task
        from evalscope.api.dataset import SampleDataset
        from evalscope.constants import EvalType

        # Build a custom dataset from our questions
        dataset = []
        for i, q in enumerate(questions):
            dataset.append({
                "id": i,
                "query": q.get("content", ""),
                "reference": q.get("expected_keywords", ""),
            })

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "custom_dataset.jsonl"
            with open(dataset_path, "w", encoding="utf-8") as f:
                for row in dataset:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

            task_cfg = TaskConfig(
                eval_type=EvalType.CUSTOM,
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                dataset_args={
                    "dataset_id": str(dataset_path),
                },
                eval_config={
                    "limit": len(questions),
                },
            )

            try:
                eval_result = run_task(task_cfg)
                return self._normalize(eval_result, questions)
            except Exception as e:
                return AdapterResult(ok=False, error=f"EvalScope error: {e}")

    def _normalize(self, result, questions: list[dict]) -> AdapterResult:
        """Convert EvalScope output to our standardized AdapterResult."""
        items = []
        scores = {}
        total = 0.0

        try:
            # EvalScope returns different structures depending on benchmark type
            # Try to extract what we can
            raw = {}
            if hasattr(result, "to_dict"):
                raw = result.to_dict()
            elif hasattr(result, "__dict__"):
                raw = result.__dict__

            # Build per-question items
            for i, q in enumerate(questions):
                items.append({
                    "question": q.get("content", "")[:200],
                    "score": None,
                    "note": "see raw output",
                })
        except Exception:
            items = [
                {"question": q.get("content", "")[:200], "score": None}
                for q in questions
            ]

        return AdapterResult(
            ok=True,
            total_score=round(total, 2),
            scores=scores,
            items=items,
            raw=raw,
        )
