# knowledge_search · 检索 / 评测 / 设置

> 归属模块：`backend/apps/knowledge_search` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/knowledge_search/urls.py`、`api.py`、`retrieval.py`、`eval_runner.py`、`models.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

知识模块的**检索面与评测面**，四张表：

| 表 | 模型 | 说明 |
| --- | --- | --- |
| `KnowledgeModule` | 知识模块 | 名称、描述、数据目录、启用开关 |
| `RetrievalSettings` | 检索设置 | 单例行；embedding 模型引用 `AIModelConfig`（跨 App 只读） |
| `KsEvalRun` | 评测批次 | 状态、进度、阶段、指标 |
| `KsEvalQuery` | 评测查询 | 单条查询的命中与指标明细 |

模块清单**落库**（`KnowledgeModule`），旧的 `registry.py` 已删除。

## 接口（`/api/knowledge-search/`，全部带尾斜杠）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET / PATCH | `settings/` | 读 / 写检索设置 |
| GET | `modules/` | 模块列表 |
| GET / PATCH / DELETE | `modules/<int:pk>/` | 模块详情 / 更新 / 删除 |
| POST | `modules/<int:pk>/index/` | 为模块建索引 |
| POST | `query/` | 检索查询 |
| GET | `evaluations/` | 评测批次列表（`?module=` 过滤） |
| GET | `evaluations/<int:pk>/` | 评测批次详情 |

## 写库与生命周期

- 写操作一律经 `api.py`：`create_module` / `update_module` / `delete_module` /
  `save_retrieval_settings` / `create_eval_run` / `mark_eval_running` / `set_eval_progress` /
  `set_eval_phase` / `add_eval_query` / `finish_eval_run`。
- **评测批次状态机在 `api.py`**，执行体在 `eval_runner.py`；同一模块同时只允许一个运行中的批次
  （`api.running_eval_run()` 判重，冲突返回 409 `EvalRunningConflict`）。
- 检索实现（分块、嵌入、召回）在 `retrieval.py`。

## 待偿债权（如实登记，勿当成已合规）

**View 编排未下沉（审计 R-4）**：`views.py` 直接编排 `api` / `retrieval` / `eval_runner`，
并两处直接读跨 App Model——`AIModelConfig.objects.filter(...)`（`views.py:46`、`:230`）。
跨 App **读** Model 按 `backend/AGENTS.md` §1.1 是允许的，所以这不是违规；
但「编排逻辑留在 View」属于技术债，收敛方向是把编排挪进 `api.py`。改动该模块时**不要**继续加厚 View。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/knowledge_search -q
[ ] python manage.py spectacular --validate
```

全局关单清单见 `backend/AGENTS.md` §3；命令全集见
[../self_test_and_checks.md](../self_test_and_checks.md)。
