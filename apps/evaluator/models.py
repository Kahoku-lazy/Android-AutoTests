"""Evaluator app — agent & knowledge base evaluation.

Models:
- QuestionBank: a named collection of test questions (e.g. "30-question base set").
- Question: a single test item belonging to a bank.
- EvalRun: one evaluation session against a specific agent + question bank.
- EvalResult: per-question score (machine + optional human review) within a run.
"""

from django.conf import settings
from django.db import models


class QuestionBank(models.Model):
    """A named collection of test questions (a "test paper")."""

    name = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ev_question_banks"
        verbose_name = "问题试卷"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    @property
    def question_count(self) -> int:
        return self.questions.count()


class Question(models.Model):
    """A single test question."""

    bank = models.ForeignKey(
        QuestionBank, on_delete=models.CASCADE, related_name="questions",
    )
    content = models.TextField()  # the question text
    expected_keywords = models.TextField(
        default="", blank=True,
        help_text="Comma-separated keywords the answer should cover",
    )
    category = models.CharField(
        max_length=50, default="general", blank=True,
        help_text="e.g. 平台功能, 测试流程, 设备管理, 用例设计",
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ev_questions"
        ordering = ["bank", "order", "id"]
        verbose_name = "评测问题"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content[:80]


class EvalRun(models.Model):
    """One evaluation session: a specific agent × question bank."""

    STATUS_CHOICES = [
        ("pending", "等待中"),
        ("running", "评测中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]

    agent = models.ForeignKey(
        "ai_assistant.AIAgent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eval_runs",
    )
    bank = models.ForeignKey(
        QuestionBank, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="runs",
    )
    status = models.CharField(max_length=20, default="pending", choices=STATUS_CHOICES)
    total_questions = models.IntegerField(default=0)
    completed_questions = models.IntegerField(default=0)

    # Which evaluation framework to use
    framework = models.CharField(
        max_length=30, default="self",
        help_text="self | evalscope | deepeval | maseval",
    )
    # Judge model config — separate from the agent under test
    judge_provider = models.CharField(max_length=50, default="dashscope")
    judge_model = models.CharField(max_length=100, default="qwen-max")

    # Aggregate scores (1-5 scale)
    total_score = models.FloatField(default=0.0)
    avg_relevance = models.FloatField(default=0.0)
    avg_accuracy = models.FloatField(default=0.0)
    avg_completeness = models.FloatField(default=0.0)
    avg_conciseness = models.FloatField(default=0.0)

    # Full report stored as JSON
    report_json = models.TextField(default="{}", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ev_runs"
        ordering = ["-created_at"]
        verbose_name = "评测记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        agent_name = self.agent.name if self.agent else "?"
        return f"[{self.status}] {agent_name} × {self.bank.name if self.bank else '?'}"


class EvalResult(models.Model):
    """Per-question scoring within an evaluation run."""

    run = models.ForeignKey(
        EvalRun, on_delete=models.CASCADE, related_name="results",
    )
    question = models.ForeignKey(
        Question, on_delete=models.SET_NULL, null=True, blank=True,
    )
    question_text = models.TextField(default="", blank=True)
    agent_response = models.TextField(default="", blank=True)

    # Machine scores (Judge LLM, 1-5)
    relevance_score = models.FloatField(default=0.0)
    accuracy_score = models.FloatField(default=0.0)
    completeness_score = models.FloatField(default=0.0)
    conciseness_score = models.FloatField(default=0.0)

    # Optional human review scores (override machine scores when present)
    human_relevance = models.FloatField(null=True, blank=True)
    human_accuracy = models.FloatField(null=True, blank=True)
    human_completeness = models.FloatField(null=True, blank=True)
    human_conciseness = models.FloatField(null=True, blank=True)
    human_note = models.TextField(default="", blank=True)

    # Judge LLM reasoning for this question
    judge_reasoning = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ev_results"
        ordering = ["question__order", "id"]
        verbose_name = "评测结果"
        verbose_name_plural = verbose_name

    def effective_scores(self) -> dict:
        """Return human scores when available, otherwise machine scores."""
        return {
            "relevance": self.human_relevance
            if self.human_relevance is not None
            else self.relevance_score,
            "accuracy": self.human_accuracy
            if self.human_accuracy is not None
            else self.accuracy_score,
            "completeness": self.human_completeness
            if self.human_completeness is not None
            else self.completeness_score,
            "conciseness": self.human_conciseness
            if self.human_conciseness is not None
            else self.conciseness_score,
        }
