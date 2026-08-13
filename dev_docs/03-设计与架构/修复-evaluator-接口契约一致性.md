# 修复：evaluator 接口契约一致性

> 状态：**P0-1 已实施并验证**；前端切 DRF 推迟（信封统一待全量迁移，见 §11）
> 日期：2026-08-13
> 相关：`检查-DRF迁移-接口契约一致性.md`、`设计-DRF迁移方案-evaluator试点.md`、`设计-登录模块-accounts-DRF.md`

## 1. 目标

修复 evaluator 前后端契约不一致（见检查报告 P0/P1），确立信封与字段规范：

1. **P0-1**：启动评测返回字段不匹配 → `pollRun(undefined)` 404，评测状态无法刷新
2. **P0-2**：信封三态（平铺 / `data` 嵌套）→ 统一为 `{ status, data }`
3. **P1-2**：评分端点 `submit_score` 挂在错误的 ViewSet 上 → 路径语义与 legacy 不兼容

evaluator 是 DRF 迁移试点，本次修复同时作为其余 App 的契约修复样板。

## 2. 已确认决策

| 项 | 选择 |
|---|---|
| 修复对象 | evaluator 先行；workflow/case_manager/element_locator 分批跟进 |
| 信封 | 统一 `{ status: true, data }` / `{ status: false, message }`（对齐 accounts） |
| 字段命名 | JSON 保持 snake_case 不变 |
| P0-1 startRun | 后端返回 `run` 对象（`{ run: { id } }`），前端零改动 |
| 前端接入 | evaluator 前端 `evaluator-api.ts` 切 DRF 端点（RESTful 路径） |
| submitScore | 从 `EvalRunViewSet` 移到 `EvalResultViewSet`，`/results/{id}/score/` |
| 写操作 | 收敛到新建 `api.py`（后续批，见 §10 Non-goals） |

## 3. 架构

```
Vue (EvaluatorTab.vue / evaluator-api.ts)
        │  HTTP JSON（snake_case）
        ▼
apps.evaluator (DRF ViewSet + Serializer)
        │  读：get_queryset → ORM
        │  写：perform_create / @action → ORM（本轮暂不收敛 api.py）
        ▼
Django ORM (QuestionBank / Question / EvalRun / EvalResult)
        +
shared.renderers.EnvelopeJSONRenderer   # 统一 { status, data }
shared.auth.drf_auth.JWTAuthentication   # 受保护接口鉴权
```

### 边界

| 模块 | 职责 |
|------|------|
| `apps.evaluator` | 试卷库 / 评测运行 / 人工评分的 HTTP 契约 |
| `shared.renderers` | 信封统一，业务层不再手拼 `status` 外壳 |
| 前端 `evaluator-api.ts` | 路径切 DRF；组件从 `data` 嵌套读字段 |

## 4. 修复项

### 4.1 P0-1：启动评测返回 `run` 对象

**现状**（前端 `EvaluatorTab.vue:131` 读 `data.run?.id`，后端返回顶层 `id`）：

```python
# apps/evaluator/views.py:381-387（legacy）与 views_api.py:144-147（DRF）均返回
return JsonResponse({"status": True, "id": run.id, "message": "..."})
```

**修复后**（后端包一层 `run` 对象，与 `get_run` 的 `run` 结构一致）：

```python
# DRF views_api.py start @action
return Response({"run": {"id": run.id}, "message": f"评测已开始，共 {bank.question_count} 题"})

# legacy views.py start_eval_run
return JsonResponse({"status": True, "run": {"id": run.id}, "message": "..."})
```

前端 `data.run?.id` 即可拿到，`pollRun(id)` 正常轮询。**前端零改动，后端改一处（两端同步）。**

### 4.2 P0-2：信封统一为 `{ status, data }`

**现状**：legacy 视图平铺 `{ status: true, banks: [...] }`；DRF 经 `EnvelopeJSONRenderer` 嵌套 `{ status: true, data: [...] }`；前端写死平铺读取。

**决策**：统一为 `{ status, data }` 嵌套，前端 `evaluator-api.ts` 切 DRF 路径后天然对齐（同 accounts 模式）。

| 端点 | 修复前（legacy） | 修复后（DRF + Envelope） |
|------|-----------------|------------------------|
| `list_banks` | `GET /banks` → `{ status, banks: [...] }` | `GET /banks/` → `{ status, data: [...] }` |
| `bank_detail` | `GET /banks/{id}` → `{ status, bank }` | `GET /banks/{id}/` → `{ status, data }` |
| `create_bank` | `POST /banks/create` → `{ status, id }` | `POST /banks/` → `{ status, data }` |
| `update_bank` | `POST /banks/{id}/update` | `PUT /banks/{id}/` |
| `delete_bank` | `POST /banks/{id}/delete` | `DELETE /banks/{id}/` |
| `list_runs` | `GET /runs` → `{ status, runs }` | `GET /runs/` → `{ status, data }` |

前端 `evaluator-api.ts` 由平铺读（`data.banks`）改为嵌套读（`data.data`）；组件同步改为读 `data.data.banks`。

### 4.3 P1-2：submitScore 移到 EvalResultViewSet

**现状**：`submit_score` 定义在 `EvalRunViewSet` 上（`views_api.py:232`，`@action(detail=False, url_path="score")`），路径 `/runs/score/`，`result_id` 作 body 参数。legacy 是 `/results/{result_id}/score`（路径参数）。语义不兼容。

**修复**：移到 `EvalResultViewSet`，`@action(detail=True, url_path="score")`，路径 `/results/{pk}/score/`，与 legacy 语义对齐。

```python
class EvalResultViewSet(viewsets.ReadOnlyModelViewSet):
    @action(detail=True, methods=["post"], url_path="score")
    def submit_score(self, request, pk=None):
        result = self.get_object()          # pk = result_id
        ...
```

## 5. 端点契约（修复后）

| 方法 | 路径 | 权限 | 作用 |
|------|------|------|------|
| GET | `/api/evaluator/banks/` | IsAuthenticated | 试卷列表 |
| POST | `/api/evaluator/banks/` | IsAuthenticated | 创建试卷（嵌套题目） |
| GET/PUT/DELETE | `/api/evaluator/banks/{id}/` | IsAuthenticated | 详情/更新/删除 |
| POST | `/api/evaluator/banks/seed/` | IsAuthenticated | 默认 30 题试卷 |
| GET | `/api/evaluator/runs/` | IsAuthenticated | 评测运行列表 |
| POST | `/api/evaluator/runs/start/` | IsAuthenticated | 启动评测 → `{ run: { id } }` |
| GET/DELETE | `/api/evaluator/runs/{id}/` | IsAuthenticated | 详情/删除 |
| GET | `/api/evaluator/results/{id}/` | IsAuthenticated | 单条结果 |
| POST | `/api/evaluator/results/{id}/score/` | IsAuthenticated | 人工评分 |
| GET | `/api/evaluator/frameworks` | IsAuthenticated | 框架列表（legacy 保留） |
| POST | `/api/evaluator/kb-search` | IsAuthenticated | KB 检索（legacy 保留） |

### 成功响应（经 EnvelopeJSONRenderer）

```json
// GET /banks/
{ "status": true, "data": [ { "id": 1, "name": "默认30题试卷", "question_count": 30, ... } ] }

// POST /runs/start/
{ "status": true, "data": { "run": { "id": 5 }, "message": "评测已开始，共 30 题" } }
```

### 失败响应

```json
{ "status": false, "message": "agent_id and bank_id are required" }
```

## 6. 后端文件改动面

| 文件 | 变更 |
|------|------|
| `apps/evaluator/views_api.py` | `start` 返回 `run` 对象；`submit_score` 移到 `EvalResultViewSet` |
| `apps/evaluator/views.py` | `start_eval_run` 返回 `run` 对象（legacy 过渡期保持契约一致） |
| `apps/evaluator/urls.py` | 移除被 DRF 覆盖的 legacy 路径（banks/runs/results 的 CRUD，保留 frameworks/kb） |

### 删除 / 清理

- `apps/evaluator/views.py` 中 banks/runs/results 的 legacy CRUD 函数（`list_banks`/`create_bank`/`update_bank`/`delete_bank`/`list_runs`/`run_detail`/`delete_run`/`submit_human_score`），待前端切完后移除
- 保留 `list_frameworks` / `kb_search` / `kb_self_test`（无 DRF 等价物）

## 7. 前端改动面

| 文件 | 变更 |
|------|------|
| `frontend/src/modules/ai-assistant/evaluator-api.ts` | 路径切 DRF（`/banks/` `/runs/start/` 等）；返回类型改嵌套 `{ status, data }` |
| `frontend/src/modules/ai-assistant/EvaluatorTab.vue` | 读字段 `data.banks` → `data.data`；`startRun` 后读 `data.data.run.id` |

## 8. 测试改动面

| 范围 | 变更 |
|------|------|
| 接口测试 | 端点从 legacy 路径切 DRF 路径；断言 `body["data"]` 嵌套 |
| 回归 | 验证启动评测后轮询能拿到 run id（覆盖 P0-1） |

## 9. 错误处理

| 场景 | HTTP | 响应 |
|------|------|------|
| 缺 agent_id/bank_id | 400 | `{ status: false, message }` |
| agent 不存在 | 404 | `{ status: false, message }` |
| 试卷不存在 | 404 | `{ status: false, message }` |
| 评分 result 不存在 | 404 | `{ status: false, message }` |

禁止向用户暴露堆栈、ORM 原文；技术细节只写日志。

## 10. Non-goals（本轮不做）

- 写操作收敛到 `api.py`（新建 `apps/evaluator/api.py`，独立后续批）
- workflow / case_manager / element_locator 的信封与字段修复（分批跟进）
- case_manager `steps` 四重命名清理
- 鉴权双轨合并（中间件 / DRF 去重）
- evaluator 前端 UI 改版

## 11. 实施顺序

**已完成（P0-1）**：

1. ✅ 后端 `views_api.py`：`start` 返回 `run` 对象 + `submit_score` 移到 `EvalResultViewSet`(detail=True)
2. ✅ 后端 `views.py`：`start_eval_run` 返回 `run` 对象
3. ✅ 验证：`py_compile` + `manage.py check` 通过（静态验证；服务未启动，未做运行时端到端）

**推迟（前端切 DRF，信封统一）**：

> 决策：停在 P0-1。前端继续走 legacy，P0-1 已通过后端修复解决（legacy 路径也能拿到 `run.id`）。
> 原因：切 DRF 会制造「混合信封」——banks/runs/results 变 `data` 嵌套，frameworks/kb/agents 仍平铺，组件内两种读法并存，比当前「全平铺」更易错。
> 待全量切 DRF 时一揽子做信封统一 + 移除 legacy CRUD（原步骤 3–6）。
