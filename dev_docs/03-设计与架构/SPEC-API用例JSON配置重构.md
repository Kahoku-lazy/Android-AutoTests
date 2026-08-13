# SPEC: API 测试用例统一 JSON 配置重构 — 任务拆解与执行计划

> 来源：设计文档 `dev_docs/03-设计与架构/设计-API用例JSON配置重构方案.html`
> 完整方案：`C:\Users\zhiyan\.claude\plans\tests-refactored-sundae.md`
> 创建日期：2026-08-10
> 状态：执行中

---

## 概览

| 阶段 | 名称 | 预估工作量 | 依赖 | 状态 |
|:--:|------|:--:|------|:--:|
| P0 | 类型定义与基础设施 | 0.5d | — | ✅ 完成 |
| P1 | 后端 Model & Migration | 1d | P0 | ⬜ 待开始 |
| P2 | 后端 api.py & views.py | 1d | P1 | ⬜ 待开始 |
| P3 | 后端 Executor V2 | 1.5d | P0 | ⬜ 待开始 |
| P4 | AgentScope Tool | 0.5d | P2 | ⬜ 待开始 |
| P5 | 前端 Composables | 1d | P0 | ⬜ 待开始 |
| P6 | 前端组件 — CaseInfoPanel | 0.5d | P5 | ⬜ 待开始 |
| P7 | 前端组件 — StepListPanel + ApiStepCard | 1.5d | P5 | ⬜ 待开始 |
| P8 | 前端组件 — TestDataPanel | 1d | P5 | ⬜ 待开始 |
| P9 | 前端组件 — ValidationPanel | 0.5d | P5 | ⬜ 待开始 |
| P10 | 前端 ApiCaseEditor 重构 | 1d | P6-P9 | ⬜ 待开始 |
| P11 | WebSocket 推送 | 0.5d | P4 | ⬜ 待开始 |
| P12 | 测试 — 后端 | 1d | P3 | ⬜ 待开始 |
| P13 | 测试 — 前端 E2E | 0.5d | P10 | ⬜ 待开始 |
| P14 | 清理旧代码 | 0.5d | P12-P13 | ⬜ 待开始 |

> **总预估**: 10-12 个工作日。可并行：P4 ∥ P5-P9（前后端独立），P6-P9 之间独立。

---

## P0: 类型定义与基础设施 ✅

**目标**：前后端共享的类型定义先行，后续所有任务依赖此层。

### 任务 P0.1 — 后端 config_json Schema 常量 ✅

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/schema_config.py`（已创建） |
| **内容** | `CONFIG_JSON_SCHEMA`、`get_default_config()`、`validate_config_json()` |
| **验收** | 已完成 |

### 任务 P0.2 — 前端 TypeScript 类型定义 ✅

| 项 | 内容 |
|------|------|
| **文件** | `frontend/src/modules/case-manager/types/api-config.ts`（已创建） |
| **内容** | `ApiConfigJson`、`CaseInfo`、`ApiStep`、`TestDataRow`、`ValidationRule`、`ExtractRule`、`ResolvedVariable` + 工厂函数 |
| **验收** | 已完成 |

### 任务 P0.3 — 确认 jsonschema 依赖 ⚠️

| 项 | 内容 |
|------|------|
| **状态** | jsonschema 4.26.0 已安装，但 **未在 requirements.txt 中声明** |
| **操作** | 需添加 `jsonschema>=4.0.0` 到 requirements.txt |

---

## P1: 后端 Model & Migration

**目标**：ApiTestCase 表结构变更——加 `config_json`，删 12 个废弃字段。

### 任务 P1.1 — 创建 migration 0019

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/migrations/0019_*.py`（自动生成 + 手动编辑） |
| **操作** | 1. `python manage.py makemigrations case_manager --name add_config_json_to_api`<br>2. 手动编写 `operations`：`AddField("config_json")` + 12 个 `RemoveField` |
| **删除字段** | `method`, `url`, `headers`, `body`, `expected_response`, `expected_status`, `steps_json`, `rows`, `assertions`, `custom_columns`, `design_method`, `metrics` |
| **注意** | `precondition` 保留；`description` 保留 |
| **验收** | `python manage.py migrate` 成功；往返 migrate 正常 |

### 任务 P1.2 — 更新 models_api.py

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/models_api.py` |
| **操作** | 1. 添加 `config_json = models.JSONField(default=dict)`<br>2. 删除 12 个废弃字段定义<br>3. `__str__` 保持返回 `self.title` |
| **验收** | `python manage.py check --deploy` 通过 |

---

## P2: 后端 api.py & views.py

### 任务 P2.1 — 更新 api_api.py

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/api_api.py` |
| **操作** | 1. `save_api_definition` 新增 `config_json` 参数，写入前调 `validate_config_json()`<br>2. 移除旧字段参数（method/url/headers/body/steps_json/rows）<br>3. `batch_save_api_definitions` 同步调整 |
| **验收** | 合法 config_json 写入成功；非法 → ValueError |

### 任务 P2.2 — 更新 views_api.py

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/views_api.py` |
| **操作** | 1. `_serialize_api`：返回 `config_json`，移除旧字段序列化<br>2. `_normalize_api_batch`：适配新格式<br>3. POST handler：从 request body 取 `config_json`，校验后调用 `save_api_definition` |
| **验收** | GET 返回含 config_json 的数据；POST 新用例成功 |

### 任务 P2.3 — 更新 urls.py

| 项 | 内容 |
|------|------|
| **操作** | 检查路由，大概率不变 |
| **验收** | 3 条 API 路由正常 |

---

## P3: 后端 Executor V2

### 任务 P3.1 — 创建 executor_v2.py

| 项 | 内容 |
|------|------|
| **文件** | `apps/test_runner/executors/api/executor_v2.py`（新建） |
| **内容** | `ApiExecutorV2` 类：`execute_case` → `_execute_row` → 7 步 pipeline |
| **复用** | `_eval_json_path`、`_resolve`、adapter 调用逻辑从现有 executor.py 提取 |
| **验收** | 单步 HTTP → pass；schema 不匹配 → fail（含 diff） |

### 任务 P3.2 — 扩展 TestStep dataclass

| 项 | 内容 |
|------|------|
| **文件** | `models/step_types.py` |
| **操作** | 新增 `request_schema: dict` 和 `response_schema: dict` 字段，更新 `to_dict()`/`from_dict()` |
| **验收** | `TestStep().to_dict()` 包含新字段 |

### 任务 P3.3 — 重写 load_definitions()

| 项 | 内容 |
|------|------|
| **文件** | `apps/test_runner/views/execution.py` |
| **操作** | 从 `r.config_json` 直接读取；移除 `_build_api_step_from_flat()`；透传 `test_data` + `validation`；选择 `ApiExecutorV2` |
| **验收** | `POST /api/runner/run` → 返回 pass/fail |

---

## P4: AgentScope Tool

### 任务 P4.1 — 注册 Tool Schema + Handler

| 项 | 内容 |
|------|------|
| **文件** | `apps/ai_assistant/agent_scope/tool_registry.py` |
| **操作** | 新增 `save_api_test_case` tool：module=`"cases"`, action=`"save_api_config"`, params=`[{case_id, config_json}]` |
| **验收** | AgentScope 工具列表出现新 tool |

### 任务 P4.2 — WebSocket 推送

| 项 | 内容 |
|------|------|
| **文件** | `apps/case_manager/consumers.py`（新建）、`gateway/routing.py` |
| **操作** | 创建 `CaseEditingConsumer`；`save_api_definition` 后推送 `case_updated`；路由注册 `ws/case-editing/{case_id}` |
| **降级** | 如 WS 过于复杂，可降级为 30s 轮询 |
| **验收** | WS 面板收到 `case_updated` 消息 |

---

## P5: 前端 Composables

### 任务 P5.1 — 实现 useApiConfigJson

| 项 | 内容 |
|------|------|
| **文件** | `frontend/src/modules/case-manager/composables/useApiConfigJson.ts`（新建） |
| **内容** | `config`（reactive）、`load(id)`、`save()`、`upstreamVariables(stepIndex)`、`dataColumns`（computed）、`resolveVariables(steps, stepIndex)` |
| **验收** | 在 setup 中可用 |

### 任务 P5.2 — 实现 JSON Schema 编辑器 composable

| 项 | 内容 |
|------|------|
| **文件** | `frontend/src/modules/case-manager/composables/useJsonSchemaEditor.ts`（新建） |
| **内容** | 可视化模式 ↔ 代码模式切换；`schemaToFields()` 和 `fieldsToSchema()` 转换 |
| **验收** | 双向转换不丢失数据 |

---

## P6-P9: 前端面板组件

### P6 — CaseInfoPanel.vue

- **Props**: `modelValue: CaseInfo`
- **UI**: ID（只读）、标题（必填红色星号）、描述（textarea）、前置条件（textarea）

### P7 — StepListPanel.vue + ApiStepCard.vue

- **StepListPanel**: 步骤卡片列表、拖拽排序、添加步骤
- **ApiStepCard**: 折叠卡片（name/domain/url/method/headers/body/request_schema/response_schema/extract/assert），变量下拉提示

### P8 — TestDataPanel.vue

- **Props**: `modelValue: TestDataRow[]`、`dataColumns: string[]`
- **UI**: el-table，列头自动生成，output_schema 弹出编辑器

### P9 — ValidationPanel.vue

- **Props**: `modelValue: ValidationRule[]`、`stepCount: number`
- **UI**: step_index 下拉 + enabled 开关 + JSON Schema 编辑器

---

## P10: 前端 ApiCaseEditor 重构

### 任务 P10.1 — 重建 ApiCaseEditor.vue

| 项 | 内容 |
|------|------|
| **操作** | 使用 `useApiConfigJson()` composable；组合 4 个面板；保存前校验 title 非空 + steps.length > 0 |
| **注意** | 462 行 → 预计 150-200 行。备份旧文件为 `.bak` |

### 任务 P10.2 — 更新 ApiCaseList.vue

| 项 | 内容 |
|------|------|
| **操作** | 移除 method/url/expected_status 列；从 `config_json.case_info.title` 取标题 |

---

## P11: WebSocket 推送（前端）

- **文件**: `useCaseEditingSocket.ts`（新建）
- **内容**: 连接 `ws/case-editing/{case_id}`，收到 `case_updated` → 自动刷新

---

## P12-P13: 测试

### P12 — 后端测试（≥23 条）

| 文件 | 用例数 | 覆盖 |
|------|:--:|------|
| `test_api_crud.py` | ≥10 | 创建/读取/更新/删除/校验拒绝 |
| `test_executor_v2.py` | ≥8 | 7步 pipeline + 数据驱动 |
| `test_substitute_vars.py` | ≥6 | 5字段替换 + 优先级 |

### P13 — 前端 E2E（≥5 条）

Playwright 测试：编辑器渲染 → 填写保存 → 编辑回显 → 测试数据持久化 → AI 刷新

---

## P14: 清理旧代码

- **后端**: 移除 `_build_api_step_from_flat()`、`_to_row_dicts()`、旧字段引用
- **前端**: 移除 `buildStepsJson()`、`syncFieldsToStep()`、旧状态引用

---

## 执行依赖图

```
P0 (类型定义) ✅
 │
 ├── P1 (Model Migration) ── P2 (api.py/views.py) ── P4 (AgentScope Tool) ── P11 (WS 推送)
 │                                                         │
 ├── P3 (Executor V2) ─────────────────────────────────────┤
 │                                                         │
 └── P5 (Composables) ──┬── P6 (CaseInfoPanel) ──────────┐ │
                        ├── P7 (StepListPanel) ──────────┤ │
                        ├── P8 (TestDataPanel) ──────────┤ │
                        └── P9 (ValidationPanel) ────────┤ │
                                                         P10 (ApiCaseEditor 重构)
                                                              │
                                          P12 (后端测试) ────┤
                                          P13 (E2E) ────────┤
                                                              │
                                                         P14 (清理旧代码)
```

---

## 风险清单

| # | 风险 | 影响 | 缓解措施 |
|:--:|------|:--:|------|
| 1 | DB migration 失败（开发环境有旧数据） | P1 阻塞 | 开发 DB 是 SQLite，可直接删除重建 |
| 2 | `TestStep` dataclass 扩展影响 UI automation | P3 阻塞 | 新字段 `default_factory=dict`，对其他执行器透明 |
| 3 | `load_definitions()` 修改影响 Web/Storage | P3 风险 | 只改 `task_type == "api_testing"` 分支 |
| 4 | WebSocket 推送复杂度超预期 | P11 风险 | 降级为 30s 轮询 |
| 5 | `ApiCaseEditor.vue` 462 行重写遗漏功能 | P10 风险 | 保留旧文件为 `.bak` |
| 6 | `jsonschema` pip 包未在 requirements.txt | P0 风险 | P0.3 先检查 |
| 7 | 12 个字段删除导致其他 App 引用报错 | P1 风险 | 全局 grep 确认后再删 |

---

## 验收总清单

- [ ] `POST /api/cases/api-testing/definitions` 接收 `config_json` → 校验 → 写入
- [ ] `GET /api/cases/api-testing/definitions` 返回含 `config_json` 的数据
- [ ] `POST /api/runner/run` → ExecutorV2 正确执行 7 步 pipeline
- [ ] 步骤间 `{{var}}` 变量传递正确
- [ ] `test_data` N 行 × M 步 = N×M 次请求
- [ ] `request_schema` 校验失败 → 不发请求，标记 fail
- [ ] `response_schema` 断言失败 → 标记 fail，含 diff
- [ ] `response_schema` 中 `{{var}}` 被正确替换（漏洞修复）
- [ ] 行级 `output_schema` 覆盖步骤级断言
- [ ] 前端 4 面板直接绑定 `configJson`，所见即所得
- [ ] 前端保存 → 刷新 → 数据一致
- [ ] AI 通过 AgentScope Tool 写入 → 前端自动刷新
- [ ] 后端测试 ≥ 23 条全部通过
- [ ] 旧字段引用全部清理
- [ ] `python manage.py check --deploy` 无警告
