"""evaluator DRF serializers — QuestionBank, Question, EvalRun, EvalResult."""

from rest_framework import serializers

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
        questions_data = validated_data.pop("questions", [])
        bank = QuestionBank.objects.create(**validated_data)
        for i, q in enumerate(questions_data):
            Question.objects.create(
                bank=bank,
                order=q.get("order", i),
                **{k: v for k, v in q.items() if k != "order"},
            )
        return bank

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        instance = super().update(instance, validated_data)
        if questions_data is not None:
            instance.questions.all().delete()
            for i, q in enumerate(questions_data):
                Question.objects.create(
                    bank=instance,
                    order=q.get("order", i),
                    **{k: v for k, v in q.items() if k != "order"},
                )
        return instance


class EvalRunSerializer(serializers.ModelSerializer):
    """Evaluation run — read-heavy (run details with results)."""

    agent_name = serializers.CharField(source="agent.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    results = serializers.SerializerMethodField()

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

    def get_results(self, obj):
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

    def get_effective_relevance(self, obj):
        eff = obj.effective_scores()
        return eff["relevance"]

    def get_effective_accuracy(self, obj):
        eff = obj.effective_scores()
        return eff["accuracy"]

    def get_effective_completeness(self, obj):
        eff = obj.effective_scores()
        return eff["completeness"]

    def get_effective_conciseness(self, obj):
        eff = obj.effective_scores()
        return eff["conciseness"]
