from __future__ import annotations

from typing import Any

__all__ = [
    "CASE_SUITE",
    "HANDOVER_QUALITY",
    "METHOD_KEYS",
    "METHODS",
    "PROMPT_QUALITY",
    "build_metric",
    "list_methods",
]

PROMPT_QUALITY = "prompt_quality"
HANDOVER_QUALITY = "handover_quality"
CASE_SUITE = "case_suite"
DEFAULT_THRESHOLD = 0.5

METHODS: dict[str, dict] = {
    PROMPT_QUALITY: {
        "name": "提示词质量",
        "target": "prompt",
        "engine": "geval",
        "description": "评估系统提示词本身是否把活说清楚。",
        "steps": [
            "只看提示词本身，不评模型能力。角色与目标是否明确：能看出这个智能体负责什么、边界在哪。",
            "流程是否可执行：是否有固定工作顺序（先看屏幕、再决定动作、动作后确认）。",
            "工具与约束是否说清：工具怎么用、坐标怎么算、何时必须重新截图或禁止重复点击。",
            "异常与收尾是否交代：失败怎么处理、什么时候交接、交接要写什么。四条都具体可照做给高分；含糊、只有口号、缺少可执行细节给低分。",
        ],
    },
    HANDOVER_QUALITY: {
        "name": "交接文本质量",
        "target": "handover",
        "engine": "geval",
        "description": "评估一次运行产出的交接文本能否让接手人继续干活。",
        "steps": [
            "做了什么：是否说清完成到哪一步、哪些子目标已完成。",
            "停在哪：是否交代当前页面与关键界面元素。",
            "下一步从哪开始：是否给出可继续的起点，或明确说明任务已结束。",
            "有无臆造：是否声称做了没做的事，或把没验证的结果说成已验证。前三项具体且没有臆造给高分；空泛复述、把未验证说成成功、或缺少下一步给低分。",
        ],
    },
    CASE_SUITE: {
        "name": "真题集执行",
        "target": "case",
        "engine": "geval",
        "description": "对每条评测题的真实执行结果（步骤达成 + 交接文本）打分。",
        "steps": [
            "是否按题目动作把该做的做完，断言是否被验证。",
            "失败时是否说明卡在哪一步、原因是什么、是否给出可继续的建议。",
            "交接文本是否交代最终停在哪个页面、关键界面元素。",
            "有无臆造：是否把没验证的结果说成已验证。做完且交代清楚给高分；中途失败但如实说明可给中等分；含糊、复述或臆造给低分。",
        ],
    },
}

METHOD_KEYS = tuple(METHODS)


def list_methods() -> list[dict]:
    return [
        {
            "key": key,
            "name": item["name"],
            "target": item["target"],
            "engine": item["engine"],
            "description": item["description"],
            "criteria": "\n".join(item["steps"]),
            "steps": list(item["steps"]),
            "threshold": DEFAULT_THRESHOLD,
        }
        for key, item in METHODS.items()
    ]


def build_metric(method_key: str, judge: Any, *, threshold: float = DEFAULT_THRESHOLD) -> Any:
    from deepeval.metrics import GEval
    from deepeval.test_case import SingleTurnParams

    item = METHODS.get(method_key)
    if item is None:
        raise ValueError(f"未知评测方法：{method_key}")
    return GEval(
        name=item["name"],
        evaluation_steps=[*item["steps"], "理由必须用简体中文写，不要用英文。"],
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=judge,
        threshold=threshold,
    )
