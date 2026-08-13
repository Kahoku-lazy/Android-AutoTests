# DRF 迁移方案 — evaluator 试点

## 目标

将项目从纯 Django 函数视图向 Django REST Framework 迁移，试点选 **evaluator** App。

目标：**规范化架构 + API 自动文档 + 减少重复代码**。

---

## 为什么是 evaluator（而非其他 App）

| App | 标准 CRUD | 非标准 | 文件数 | 适合试点？ |
|-----|:--:|:--:|:--:|-----|
| **evaluator** | 8 (57%) | 6 | 1 | ✅ **最佳** — 2 个 Model，比例均衡，单文件 |
| workflow | 5 (50%) | 5 | 1 | 偏小，有 REST 反模式需先修 |
| case_manager | 10 (38%) | 16 | 9 | 太大，适合第二波 |
| device_pool | **0 (0%)** | 13 | 5 | ❌ 全非标准（ADB/u2/锁状态机），DRF 无收益 |

---

## Before → After

### 1. 序列化：手写校验 → Serializer 声明式

**Before** — 每个 View 手动 `json.loads` + 逐个字段校验 + 手拼 dict 响应：

```python
def create_bank(request):
    data = json.loads(request.body)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse(
            {"status": False, "message": "试卷名称不能为空"}, status=400
        )
    bank = QuestionBank.objects.create(
        name=name, description=data.get("description", "")
    )
    for i, q in enumerate(data.get("questions") or []):
        Question.objects.create(
            bank=bank,
            content=q.get("content", ""),
            expected_keywords=q.get("expected_keywords", ""),
            category=q.get("category", "general"),
            order=i,
        )
    return JsonResponse(
        {"status": True, "id": bank.id, "question_count": bank.question_count}
    )
```

**After** — `serializer.is_valid(raise_exception=True)` 替代 20 行校验，嵌套创建自动处理：

```python
# serializers.py
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "content", "expected_keywords", "category", "order"]

class QuestionBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = QuestionBank
        fields = ["id", "name", "description", "questions", "question_count", "created_at"]
        read_only_fields = ["id", "question_count", "created_at"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        bank = QuestionBank.objects.create(**validated_data)
        for i, q in enumerate(questions_data):
            Question.objects.create(bank=bank, order=q.get("order", i), **q)
        return bank

# views_api.py — 一行替代整个 create 函数
class QuestionBankViewSet(ModelViewSet):
    serializer_class = QuestionBankSerializer
    # create / list / retrieve / update / destroy 全部自动生成
```

### 2. 权限：命令式 if → 声明式配置

**Before** — 每个 View 手动重复鉴权检查：

```python
def update_bank(request, bank_id):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return JsonResponse(
            {"status": False, "message": "Unauthorized"}, status=401
        )
    # ...
```

**After** — 全局声明，所有 ViewSet 自动鉴权：

```python
# config/settings.py
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
# 所有 ViewSet 自动执行鉴权，无需每个函数手写
```

### 3. 路由：14 条 path() → 2 行 register()

**Before** — 44 行手动路由注册：

```python
urlpatterns = [
    path("banks", list_banks, name="banks_list"),
    path("banks/create", create_bank, name="bank_create"),
    path("banks/seed", seed_default_bank, name="bank_seed"),
    path("banks/<int:bank_id>", bank_detail, name="bank_detail"),
    path("banks/<int:bank_id>/update", update_bank, name="bank_update"),
    path("banks/<int:bank_id>/delete", delete_bank, name="bank_delete"),
    path("runs", list_runs, name="runs_list"),
    path("runs/start", start_eval_run, name="run_start"),
    path("runs/<int:run_id>", run_detail, name="run_detail"),
    path("runs/<int:run_id>/delete", delete_run, name="run_delete"),
    path("results/<int:result_id>/score", submit_human_score, name="result_score"),
    path("frameworks", list_frameworks, name="frameworks_list"),
    path("kb-search", kb_search, name="kb_search"),
    path("kb-self-test", kb_self_test, name="kb_self_test"),
]
```

**After** — 12 行。Router 自动生成标准 REST 路由，`@action` 处理非标准操作，KB 端点保留原样：

```python
from rest_framework.routers import DefaultRouter
from .views_api import QuestionBankViewSet, EvalRunViewSet
from .views import kb_search, kb_self_test

router = DefaultRouter()
router.register(r"banks", QuestionBankViewSet)
router.register(r"runs", EvalRunViewSet)

urlpatterns = router.urls + [
    path("kb-search", kb_search),
    path("kb-self-test", kb_self_test),
]

# 自动生成的端点：
# GET    /banks/              → list
# POST   /banks/              → create
# GET    /banks/{id}/         → retrieve
# PUT    /banks/{id}/         → update
# DELETE /banks/{id}/         → destroy
# POST   /banks/seed/         → @action
# GET    /runs/               → list
# POST   /runs/start/         → @action
# GET    /runs/{id}/          → retrieve
# DELETE /runs/{id}/          → destroy
# POST   /runs/{id}/score/    → @action
# GET    /frameworks/         → @action
```

### 4. API 文档：零 → drf-spectacular + Swagger UI

DRF 自带的 Browsable API（服务端渲染 HTML）适合开发调试。生产级方案推荐 **drf-spectacular + Swagger UI**（自动 OpenAPI 3.0）：

```python
# config/settings.py
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Android-AutoTests API",
    "VERSION": "1.0.0",
}

# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
```

效果：浏览器访问 `http://localhost:8766/api/docs/` → 可交互 Swagger UI，自动列出所有端点、请求/响应 schema、"Try it out" 按钮。

| 方案 | 适合场景 | 推荐 |
|------|---------|:--:|
| DRF **Browsable API** | 开发调试，浏览器直接看 | 保留（零成本） |
| **drf-spectacular** + Swagger UI | 团队协作、前端对接、OpenAPI 导出 | ✅ 推荐 |
| drf-yasg | 老方案，仅 OpenAPI 2.0 | ❌ 过时 |

---

## 实施步骤

### Step 1: 安装依赖

```bash
pip install djangorestframework drf-spectacular
```

更新 `requirements.txt`：
```
djangorestframework>=3.15
drf-spectacular>=0.28
```

### Step 2: 全局配置

`config/settings.py`：

```python
INSTALLED_APPS += [
    "rest_framework",
    "drf_spectacular",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "shared.auth.drf_auth.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Android-AutoTests API",
    "VERSION": "1.0.0",
}
```

`config/urls.py`：
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
```

### Step 3: JWT → DRF 认证桥接

`shared/auth/drf_auth.py`（新建）— 复用现有 `verify_token()`，零破坏：

```python
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .jwt_auth import verify_token


class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Bearer "):
            return None
        try:
            payload = verify_token(auth[7:])
            user = type("User", (), {
                "id": int(payload["sub"]),
                "is_authenticated": True,
            })()
            return (user, auth[7:])
        except Exception:
            raise AuthenticationFailed("Invalid token")
```

### Step 4: 新建 Serializers

`apps/evaluator/serializers.py`（新建）：

```python
from rest_framework import serializers
from .models import QuestionBank, Question, EvalRun, EvalResult


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "content", "expected_keywords", "category", "order"]


class QuestionBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = QuestionBank
        fields = ["id", "name", "description", "questions", "question_count", "created_at"]
        read_only_fields = ["id", "question_count", "created_at"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        bank = QuestionBank.objects.create(**validated_data)
        for i, q in enumerate(questions_data):
            Question.objects.create(bank=bank, order=q.get("order", i), **q)
        return bank

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        instance = super().update(instance, validated_data)
        if questions_data is not None:
            instance.questions.all().delete()
            for i, q in enumerate(questions_data):
                Question.objects.create(bank=instance, order=q.get("order", i), **q)
        return instance


class EvalRunSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)

    class Meta:
        model = EvalRun
        fields = [
            "id", "agent_id", "agent_name", "bank_id", "bank_name",
            "framework", "status", "total_questions", "completed_questions",
            "total_score", "avg_relevance", "avg_accuracy",
            "avg_completeness", "avg_conciseness",
            "created_at", "finished_at",
        ]


class EvalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvalResult
        fields = "__all__"
```

### Step 5: 新建 ViewSets

`apps/evaluator/views_api.py`（新建，与旧 `views.py` 共存）：

```python
import json
import threading

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import QuestionBank, EvalRun, EvalResult
from .serializers import (
    QuestionBankSerializer,
    EvalRunSerializer,
    EvalResultSerializer,
)


class QuestionBankViewSet(viewsets.ModelViewSet):
    """试卷库 CRUD — list / create / retrieve / update / destroy 由 ModelViewSet 自动生成"""
    serializer_class = QuestionBankSerializer

    def get_queryset(self):
        return QuestionBank.objects.prefetch_related("questions").order_by("-updated_at")

    @action(detail=False, methods=["post"])
    def seed(self, request):
        """POST /banks/seed/ — 创建默认 30 题试卷"""
        from .default_questions import DEFAULT_QUESTIONS

        existing = QuestionBank.objects.filter(name="默认30题试卷").first()
        if existing:
            return Response({"status": True, "id": existing.id, "message": "默认试卷已存在"})

        bank = QuestionBank.objects.create(
            name="默认30题试卷",
            description="内置 30 道评测问题，覆盖平台功能、测试流程等 7 个类别。",
        )
        for q in DEFAULT_QUESTIONS:
            Question.objects.create(
                bank=bank,
                content=q["content"],
                expected_keywords=q.get("expected_keywords", ""),
                category=q.get("category", "general"),
                order=q.get("order", 0),
            )
        return Response({"status": True, "id": bank.id, "question_count": bank.question_count})


class EvalRunViewSet(viewsets.ModelViewSet):
    """评测运行管理 — 仅暴露 list / retrieve / destroy，创建走 @action"""
    serializer_class = EvalRunSerializer
    http_method_names = ["get", "post", "delete"]  # 禁用 PUT/PATCH

    def get_queryset(self):
        return EvalRun.objects.select_related("agent", "bank").all()[:50]

    @action(detail=False, methods=["post"])
    def start(self, request):
        """POST /runs/start/ — 启动评测（后台线程）"""
        agent_id = request.data.get("agent_id")
        bank_id = request.data.get("bank_id")
        framework = request.data.get("framework", "self")

        if not agent_id or not bank_id:
            return Response(
                {"status": False, "message": "agent_id and bank_id are required"},
                status=400,
            )

        from apps.ai_assistant.models import AIAgent

        try:
            agent = AIAgent.objects.get(id=agent_id)
            bank = QuestionBank.objects.get(id=bank_id)
        except (AIAgent.DoesNotExist, QuestionBank.DoesNotExist) as e:
            return Response({"status": False, "message": str(e)}, status=404)

        run = EvalRun.objects.create(
            agent=agent, bank=bank, framework=framework,
            status="pending",
            judge_provider=request.data.get("judge_provider", "dashscope"),
            judge_model=request.data.get("judge_model", "qwen-max"),
        )

        # 后台线程执行评测（与旧逻辑一致）
        if framework and framework != "self":
            from .frameworks import get_adapter

            def _bg():
                try:
                    adapter = get_adapter(framework)
                    if adapter is None:
                        run.status = "failed"
                        run.save()
                        return
                    from apps.ai_assistant.api import decrypt_key, get_provider_config
                    import asyncio

                    api_key = decrypt_key(agent.api_key) if agent.api_key else ""
                    provider_cfg = get_provider_config(agent.model_provider, agent.base_url)
                    agent_config = {
                        "model_provider": agent.model_provider,
                        "model_name": agent.model_name,
                        "api_key": api_key,
                        "base_url": provider_cfg.get("base_url", ""),
                        "system_prompt": agent.system_prompt or "",
                        "temperature": agent.temperature,
                    }
                    questions_list = [
                        {"content": q.content, "expected_keywords": q.expected_keywords, "category": q.category}
                        for q in bank.questions.all().order_by("order", "id")
                    ]
                    result = asyncio.run(adapter.run(agent_config, questions_list))
                    run.status = "completed" if result.ok else "failed"
                    from datetime import datetime
                    run.finished_at = datetime.now()
                    run.save()
                except Exception as e:
                    run.status = "failed"
                    run.save()
        else:
            from .evaluator import run_evaluation

            def _bg():
                try:
                    run_evaluation(run.id, run.judge_provider, run.judge_model)
                except Exception:
                    run.status = "failed"
                    run.save()

        t = threading.Thread(target=_bg, daemon=True)
        t.start()

        return Response({
            "status": True, "id": run.id,
            "message": f"评测已开始，共 {bank.question_count} 题",
        })

    @action(detail=True, methods=["post"], url_path="score")
    def submit_score(self, request, pk=None):
        """POST /runs/{id}/score/ — 人工评分"""
        # 委托给旧 views.py 的同名逻辑（避免重复实现）
        from .views import submit_human_score
        # 需要 result_id 而非 run_id，这里略作适配
        ...
```

### Step 6: 更新路由

`apps/evaluator/urls.py`：

```python
from rest_framework.routers import DefaultRouter
from .views_api import QuestionBankViewSet, EvalRunViewSet
from .views import kb_search, kb_self_test  # 非 CRUD 保留原样

router = DefaultRouter()
router.register(r"banks", QuestionBankViewSet)
router.register(r"runs", EvalRunViewSet)

app_name = "evaluator"

urlpatterns = router.urls + [
    path("kb-search", kb_search, name="kb_search"),
    path("kb-self-test", kb_self_test, name="kb_self_test"),
]
```

### Step 7: 验证

```bash
# 1. 系统检查
python manage.py check                # 无错误

# 2. Swagger 文档
# 浏览器 → http://localhost:8766/api/docs/

# 3. 接口验证
curl http://localhost:8766/api/evaluator/banks/           # GET list
curl -X POST http://localhost:8766/api/evaluator/banks/seed/  # @action
```

---

## 行数对比

| 文件 | Before | After | 变化 |
|------|:--:|:--:|:--:|
| `views.py` | 545 行 | ~100 行（仅保留 kb_search/kb_self_test/frameworks） |
| `urls.py` | 44 行 | ~14 行 |
| `serializers.py` | 不存在 | ~60 行（新增） |
| `views_api.py` | 不存在 | ~140 行（新增） |
| **合计** | **589 行** | **~314 行（-47%）** |

---

## 关键文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `requirements.txt` | +`djangorestframework` +`drf-spectacular` | DRF 核心 + OpenAPI |
| `config/settings.py` | +`REST_FRAMEWORK` + `SPECTACULAR_SETTINGS` | 全局配置 |
| `config/urls.py` | + schema + swagger 路由 | API 文档入口 |
| `shared/auth/drf_auth.py` | **新建** | JWT → DRF Authentication |
| `apps/evaluator/serializers.py` | **新建** | 4 个 ModelSerializer |
| `apps/evaluator/views_api.py` | **新建** | 2 个 ViewSet + `@action` |
| `apps/evaluator/urls.py` | **修改** | Router 替代手动 path |
| `apps/evaluator/views.py` | 删减 | 仅保留 kb_search / kb_self_test |

---

## 风险 & 缓解

| 风险 | 缓解 |
|------|------|
| 新旧 URL 路径变化导致前端 404 | 新旧端点**并行运行**一个迭代周期 |
| 响应格式 `{status, data}` 与 DRF 默认格式不同 | DRF `Response` 可自定义；或前端适配层统一处理 |
| 旧 views.py 直接 ORM 写 | ViewSet 中继续 ORM（`perform_create`），符合现有写操作铁律 |
| 后台线程不受 DRF 管理 | `@action` 内 `threading.Thread` 逻辑保持不变 |
| 当前 JWT 中间件与 DRF 认证冲突 | 新建 `drf_auth.py` 复用同一 `verify_token()`，不冲突 |
| KB 端点不是 CRUD | 保留为独立路径，与 Router 共存——展示 DRF 与非 DRF 可以混合 |

---

## 后续推广路径

试点成功后的顺序：

```
evaluator（当前试点）
    ↓
workflow（简单，10 端点，确认流程）
    ↓
case_manager（复杂，26 端点，4 个 case-type 用 ViewSet 多态）
    ↓
其他 App 按需渐进
```

**不迁移的**：device_pool（0% CRUD）、ai_assistant（SSE/WebSocket/async）、test_runner（异步执行器）
