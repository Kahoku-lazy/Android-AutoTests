"""evaluator 写操作 — CRUD 与人工评分收敛到本文件。

写操作铁律：View 调用 api.py 函数写 DB，禁止直接 ORM INSERT/UPDATE/DELETE。
评测引擎（evaluator.py 的 run_evaluation）运行时状态更新属 service 层内部编排，不在此收敛。

__all__ 白名单，供 views.py / views_api.py / AgentScope Tool 调用。
"""

from .models import EvalResult, EvalRun, Question, QuestionBank

__all__ = [
    "create_question_bank",
    "update_question_bank",
    "delete_question_bank",
    "seed_default_bank",
    "create_eval_run",
    "delete_eval_run",
    "submit_human_score",
]


def create_question_bank(name: str, description: str, questions_data: list) -> dict:
    """创建试卷 + 嵌套题目。

    Args:
        name: 试卷名称
        description: 描述
        questions_data: 题目列表，每项含 content/expected_keywords/category/order

    Returns:
        dict: {"id": int, "question_count": int}
    """
    bank = QuestionBank.objects.create(name=name, description=description)
    for i, q in enumerate(questions_data):
        Question.objects.create(
            bank=bank,
            content=q.get("content", ""),
            expected_keywords=q.get("expected_keywords", ""),
            category=q.get("category", "general"),
            order=q.get("order", i),
        )
    return {"id": bank.id, "question_count": bank.question_count}


def update_question_bank(bank_id: int, data: dict) -> dict:
    """更新试卷（name/description）；可选整题替换（questions）。

    Args:
        bank_id: 试卷 ID
        data: {"name"?, "description"?, "questions"?}

    Returns:
        dict: {"question_count": int}
    """
    bank = QuestionBank.objects.get(id=bank_id)
    if "name" in data:
        bank.name = data["name"]
    if "description" in data:
        bank.description = data["description"]
    bank.save()

    if "questions" in data:
        bank.questions.all().delete()
        for i, q in enumerate(data["questions"]):
            Question.objects.create(
                bank=bank,
                content=q.get("content", ""),
                expected_keywords=q.get("expected_keywords", ""),
                category=q.get("category", "general"),
                order=i,
            )
    return {"question_count": bank.question_count}


def delete_question_bank(bank_id: int) -> None:
    """删除试卷（级联删除题目）。"""
    QuestionBank.objects.filter(id=bank_id).delete()


def seed_default_bank() -> dict:
    """创建默认 30 题试卷（幂等）。

    Returns:
        dict: {"id": int, "question_count": int, "existed": bool}
    """
    from .default_questions import DEFAULT_QUESTIONS

    existing = QuestionBank.objects.filter(name="默认30题试卷").first()
    if existing:
        return {"id": existing.id, "question_count": existing.question_count, "existed": True}

    bank = QuestionBank.objects.create(
        name="默认30题试卷",
        description="内置 30 道评测问题，覆盖平台功能、测试流程、设备管理、元素定位、知识库、异常处理、测试方法等 7 个类别。",
    )
    for q in DEFAULT_QUESTIONS:
        Question.objects.create(
            bank=bank,
            content=q["content"],
            expected_keywords=q.get("expected_keywords", ""),
            category=q.get("category", "general"),
            order=q.get("order", 0),
        )
    return {"id": bank.id, "question_count": bank.question_count, "existed": False}


def create_eval_run(agent, bank, framework: str, judge_provider: str, judge_model: str) -> dict:
    """创建评测运行记录。agent/bank 由调用方预取并校验存在。

    Returns:
        dict: {"id": int}
    """
    run = EvalRun.objects.create(
        agent=agent,
        bank=bank,
        framework=framework,
        status="pending",
        judge_provider=judge_provider,
        judge_model=judge_model,
    )
    return {"id": run.id}


def delete_eval_run(run_id: int) -> None:
    """删除评测运行记录。"""
    EvalRun.objects.filter(id=run_id).delete()


def submit_human_score(result_id: int, scores: dict) -> dict:
    """人工评分 + 重算所属 run 的平均分。

    Args:
        result_id: 评测结果 ID
        scores: {"human_relevance"?, "human_accuracy"?, "human_completeness"?, "human_conciseness"?, "human_note"?}

    Returns:
        dict: {"result_id": int, "scored": bool}
    """
    result = EvalResult.objects.get(id=result_id)
    for field in ["human_relevance", "human_accuracy", "human_completeness", "human_conciseness"]:
        if field in scores and scores[field] is not None:
            setattr(result, field, float(scores[field]))
    if "human_note" in scores:
        result.human_note = scores["human_note"]
    result.save()

    run = result.run
    all_results = run.results.all()
    scored = 0
    tr = ta = tc = tcon = 0.0
    for r in all_results:
        eff = r.effective_scores()
        if any(v > 0 for v in eff.values()):
            scored += 1
            tr += eff["relevance"]
            ta += eff["accuracy"]
            tc += eff["completeness"]
            tcon += eff["conciseness"]
    if scored > 0:
        run.avg_relevance = round(tr / scored, 2)
        run.avg_accuracy = round(ta / scored, 2)
        run.avg_completeness = round(tc / scored, 2)
        run.avg_conciseness = round(tcon / scored, 2)
        run.total_score = round(
            (run.avg_relevance + run.avg_accuracy + run.avg_completeness + run.avg_conciseness) / 4,
            2,
        )
        run.save()

    return {"result_id": result.id, "scored": True}
