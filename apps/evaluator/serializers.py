"""evaluator DRF serializers — QuestionBank, Question, EvalRun, EvalResult."""

from rest_framework import serializers

from . import api
from .models import EvalResult, EvalRun, Question, QuestionBank


class QuestionSerializer(serializers.ModelSerializer):
    """A single test question within a bank."""

    class Meta:
        model = Question
        fields = [
            "id",
            "content",
            "expected_keywords",
            "category",
            "order",
        ]


class QuestionBankSerializer(serializers.ModelSerializer):
    """Question bank with nested questions — full CRUD via one payload."""

    questions = QuestionSerializer(many=True)

    class Meta:
        model = QuestionBank
        fields = [
            "id",
            "name",
            "description",
            "questions",
            "question_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "question_count", "created_at", "updated_at"]

    def create(self, validated_data):
        # 写库经 api.py（与 legacy 路径同一实现）；api 不返回 ORM，故按 id 只读回取
        questions_data = validated_data.pop("questions", [])
        result = api.create_question_bank(
            name=validated_data["name"],
            description=validated_data.get("description", ""),
            questions_data=questions_data,
        )
        return QuestionBank.objects.get(id=result["id"])

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        data = dict(validated_data)
        if questions_data is not None:
            data["questions"] = questions_data
        api.update_question_bank(instance.id, data)
        return QuestionBank.objects.get(id=instance.id)


class EvalRunSerializer(serializers.ModelSerializer):
    """Evaluation run — read-heavy (run details with results)."""

    agent_name = serializers.CharField(source="agent.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    results = serializers.SerializerMethodField()
    # agent_id / bank_id 必须显式声明：DRF 会把 FK 的 `*_id` attname 建成 ReadOnlyField，
    # 于是 POST /runs/ 会静默丢弃这两个字段（API-评估器.md §4.2 登记为「可写、非必填」）。
    # 用裸 IntegerField 兑现契约；存在性校验在 EvalRunViewSet.perform_create。
    agent_id = serializers.IntegerField(allow_null=True, required=False)
    bank_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = EvalRun
        fields = [
            "id",
            "agent_id",
            "agent_name",
            "bank_id",
            "bank_name",
            "framework",
            "status",
            "total_questions",
            "completed_questions",
            "total_score",
            "avg_relevance",
            "avg_accuracy",
            "avg_completeness",
            "avg_conciseness",
            "judge_provider",
            "judge_model",
            "report_json",
            "created_at",
            "finished_at",
            "results",
        ]

    def get_results(self, obj) -> list[dict]:
        if not hasattr(obj, "_prefetched_results"):
            return []
        return EvalResultSerializer(obj._prefetched_results, many=True).data


class EvalRunListSerializer(serializers.ModelSerializer):
    """Evaluation run — summary only (list view, no nested results)."""

    agent_name = serializers.CharField(source="agent.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)

    class Meta:
        model = EvalRun
        fields = [
            "id",
            "agent_id",
            "agent_name",
            "bank_id",
            "bank_name",
            "framework",
            "status",
            "total_questions",
            "completed_questions",
            "total_score",
            "avg_relevance",
            "avg_accuracy",
            "avg_completeness",
            "avg_conciseness",
            "created_at",
            "finished_at",
        ]


class EvalResultSerializer(serializers.ModelSerializer):
    """Per-question scoring result — machine + optional human scores."""

    effective_relevance = serializers.SerializerMethodField()
    effective_accuracy = serializers.SerializerMethodField()
    effective_completeness = serializers.SerializerMethodField()
    effective_conciseness = serializers.SerializerMethodField()

    class Meta:
        model = EvalResult
        fields = [
            "id",
            "question_id",
            "question_text",
            "agent_response",
            "relevance_score",
            "accuracy_score",
            "completeness_score",
            "conciseness_score",
            "human_relevance",
            "human_accuracy",
            "human_completeness",
            "human_conciseness",
            "human_note",
            "effective_relevance",
            "effective_accuracy",
            "effective_completeness",
            "effective_conciseness",
            "judge_reasoning",
        ]

    def get_effective_relevance(self, obj) -> float:
        eff = obj.effective_scores()
        return eff["relevance"]

    def get_effective_accuracy(self, obj) -> float:
        eff = obj.effective_scores()
        return eff["accuracy"]

    def get_effective_completeness(self, obj) -> float:
        eff = obj.effective_scores()
        return eff["completeness"]

    def get_effective_conciseness(self, obj) -> float:
        eff = obj.effective_scores()
        return eff["conciseness"]
