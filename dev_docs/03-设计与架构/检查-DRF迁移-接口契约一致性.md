# 检查-DRF迁移-接口契约一致性

> 日期：2026-08-13
> 范围：DRF 迁移的 5 个 App（accounts / evaluator / workflow / case_manager / element_locator）
> 方法：静态契约核对（前端 `api/*.ts` + 组件字段消费 ↔ 后端 `urls.py` + `views*.py` + `serializers.py`），未运行服务。

---

## 一、检查项清单（Checklist）

| # | 检查项 | 判定标准 | 本次结果 |
|---|--------|---------|---------|
| 1 | **路径一致性** | 前端每个请求路径 ↔ 后端 `urls.py` 有唯一匹配路由 | ⚠️ 路径全匹配，但 legacy 与 DRF 双轨并存（尾斜杠分叉） |
| 2 | **请求体字段命名** | 前端发送字段 ↔ 后端解析字段，snake_case 一致 | ✅ 全 snake_case（`agent_id`/`parent_id`/`permitted_users`…） |
| 3 | **响应字段名** | 前端读取字段 ↔ 后端返回字段名一致 | 🔴 发现 1 处不匹配（startRun） |
| 4 | **响应字段集合** | 前端期望字段 ⊆ 后端返回字段，无缺失 | 🟠 DRF serializer 与 legacy 字段集不一致 |
| 5 | **字段类型** | 前端 TS 类型 ↔ 后端字段类型一致 | 🟠 `run` 对象缺失导致 `data.run?.id` 为 undefined |
| 6 | **信封结构** | 统一 `{status, data|message}`，层级一致 | 🔴 三态并存（平铺 / `data` 嵌套） |
| 7 | **写操作路径** | 写库是否走 api.py（写操作铁律） | 🔴 5 个 App 仅 workflow 合规 |
| 8 | **鉴权一致性** | 中间件 / DRF 双轨不冲突 | 🟡 双验证 + `user_id`(str)/`user.id`(int) 双身份 |
| 9 | **迁移期并行一致性** | DRF 端点 ↔ legacy 端点字段/语义等价 | 🔴 4 个 App 前端零接入 DRF，差异未被发现 |

---

## 二、逐 App 核对结论

| App | 前端接入层 | 路径 | 字段 | 信封 | 写操作 |
|-----|-----------|:--:|:--:|:--:|:--:|
| **accounts** | DRF APIView（已切换） | ✅ | ✅ | ✅ | ❌ 直接 `create_user` |
| **evaluator** | legacy | ✅ | 🔴 startRun bug | 🟠 | ❌ 直接 ORM |
| **workflow** | legacy | ✅ | 🟡 config/config_json | 🟠 | ✅ 走 `wf_api` |
| **case_manager** | legacy | ✅ | 🟠 steps 四重命名 | 🟠 | ❌ 直接 ORM |
| **element_locator** | legacy | ✅ | ✅ | 🟠 | ❌ 直接 ORM |

---

## 三、问题清单（按严重度）

### 🔴 P0-1 evaluator「启动评测」字段不匹配（真实 bug，可复现 404）

- 前端 `frontend/src/modules/ai-assistant/EvaluatorTab.vue:131`：`pollRun(data.run?.id)`
- 后端 legacy `apps/evaluator/views.py:381-387` 与 DRF `apps/evaluator/views_api.py:144-147` 都返回 `{"status": true, "id": ..., "message": ...}`（顶层 `id`，无 `run` 对象）
- 前端 `frontend/src/modules/ai-assistant/evaluator-api.ts:55` 类型写的是 `{ run?: object }`
- **后果**：`data.run` 为 undefined → `pollRun(undefined)` → `getRun(undefined)` 请求 `/runs/undefined` → `<int:run_id>` 不匹配 → 404，评测状态无法自动轮询刷新
- **修复**：后端包一层 `{"run": {"id": ...}, "message": ...}`，或前端改读 `data.id`

### 🔴 P0-2 信封三态不一致

| 层 | 形状 |
|----|------|
| 前端期望 / legacy 视图 | `{status: true, banks: [...]}` 平铺 |
| DRF + `EnvelopeJSONRenderer` | `{status: true, data: [...]}` 嵌套 |

`shared/renderers.py` 只统一了外壳，未统一业务字段层级。前端 `evaluator-api.ts:6` 写死 `{ status, banks }`，切 DRF 后 `data.banks` 为 undefined。

### 🟠 P1-1 DRF 端点前端零接入（4 App）

前端契约层全部走 legacy（无尾斜杠 + `/create` `/update` `/delete` 后缀），DRF router 标准 REST 端点无任何前端引用：

- evaluator：`/evaluator/banks/create`（legacy）≠ DRF `POST /banks/`
- workflow：`/workflow/documents/create`（legacy）≠ DRF `POST /documents/`
- case_manager：`/cases/definitions`（legacy）≠ DRF `GET /definitions/`
- element_locator：`/elements/web/create`（legacy）≠ DRF `POST /web/`

**含义**：迁移文档「新旧端点并行运行一个迭代周期」实际未发生——没有前端在跑 DRF 端点，DRF 的字段错误不会被发现。

### 🟠 P1-2 evaluator 评分端点语义不兼容

- 前端：`POST /evaluator/results/{resultId}/score`（路径参数）
- legacy：`path("results/<int:result_id>/score", submit_human_score)` ✅
- DRF：`@action(detail=False, url_path="score")` → `/runs/score/`，`result_id` 变成 body 参数

前端切 DRF 时，此调用路径与参数位置均需改。

### 🟠 P1-3 case_manager「steps」字段四重命名

`apps/case_manager/serializers.py:82-83`：

| 概念 | 字段名 | 说明 |
|------|--------|------|
| DB 列 | `steps_json` | TextField 存 JSON 字符串 |
| 读 | `steps_data` | `get_steps_data()` 解析 |
| 写 | `steps_data_write` | `source="steps_json"` write_only |
| 另一个 | `steps` | fields 里并列，语义未明 |

同一「步骤」在契约里出现 4 个名字，是历史遗留，DRF serializer 又复制了一份。

### 🟡 P2-1 截断不一致

legacy `run_detail` 对字段截断（`apps/evaluator/views.py:218-233`）：`question_text[:200]`、`agent_response[:500]`、`judge_reasoning[:300]`。DRF `EvalResultSerializer` 不截断。字段长度在 legacy/DRF 下不同。

### 🟡 P2-2 写操作铁律违反（5 App 仅 workflow 合规）

| App | 写路径 | 符合铁律 |
|-----|--------|:---:|
| workflow | ViewSet → `wf_api.*`（api.py） | ✅ |
| evaluator | `EvalRun.objects.create()` / `run.save()` | ❌ |
| case_manager | `model.objects.create()` / `.delete()` / `update_or_create()` | ❌ |
| element_locator | `WebElement.objects.create()` / `.update()` / `.delete()` | ❌ |
| accounts | `User.objects.create_user()` | ❌ |

> 注：legacy 视图同样大量直接 ORM 写（`element_locator/views.py` 20+ 处），故非 DRF 新引入，而是 DRF **复制**了 legacy 违规模式。

### 🟡 P2-3 鉴权双轨

- token 双验证：中间件 `gateway/middleware.py` + DRF `shared/auth/drf_auth.py` 各验一次
- 双身份：`request.user_id`（str，中间件注入）vs `request.user.id`（int，DRF 注入），`case_manager/views_drf.py:35` 的 `_user_id()` 兜底兼容

---

## 四、可复用检查方法

```
① 找前端契约：glob frontend/src/modules/{app}/api*.ts + types/*.ts
② 找后端契约：Read apps/{app}/urls.py + views*.py + serializers.py
③ 逐端点比对：路径 → 请求字段 → 响应字段 → 字段类型 → 信封
④ 交叉验证：前端组件消费字段（grep 组件里的 .字段名）
⑤ 数据流：写操作是否走 api.py
```

---

## 五、建议优先级

1. **先修 P0-1 startRun 字段 bug**（真实 404，影响评测功能）——两端契约对齐
2. **决策信封统一**：DRF `@action` 返回平铺，或前端统一适配 `data` 嵌套——不能三态并存
3. **给 DRF 端点一个「前端接入清单」**：否则迁移的字段差异（submitScore、steps 命名、截断）永远不被发现
4. **写操作收敛**：参照 workflow，把其余 4 个 ViewSet 改成 api.py 委托
