# evaluator App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 evaluator 行的展开）

| 只做 | 禁止 |
|------|------|
| 题库（QuestionBank/Question）、评估运行（EvalRun/EvalResult）、人工评分 | 被评估业务写库（评估只调 Agent + 判卷 LLM） |
| 框架适配经 `frameworks/` registry（BaseAdapter + register） | 散落 import 具体 adapter、绕过 registry 新增框架 |

- **评估接口契约与 Serializer 一致**：评分维度 relevance/accuracy/completeness/conciseness（含 effective_* 口径）被前端 ai-assistant 模块消费，改字段必须含 migration + 前端同步，否则评分结果对不上。
- 新评估框架走 `frameworks/base.py` BaseAdapter 实现 + `frameworks/__init__.py` register 注册，`available_frameworks()` 自动暴露。

## 本 App 契约（特例 + 真相源）

真相源：`apps/evaluator/urls.py`（14 端点：`banks` / `banks/create` / `banks/seed` / `banks/{id}` / `banks/{id}/update` / `banks/{id}/delete` / `runs` / `runs/start` / `runs/{id}` / `runs/{id}/delete` / `results/{id}/score` / `frameworks` / `kb-search` / `kb-self-test`）+ `views.py` / `views_api.py` + `serializers.py`。

- **信封双口径（2026-08-21 校验登记）**：DRF 路径（`views_api.py` ViewSet）走全局标准 `{status, data}`；**legacy 路径（`views.py` JsonResponse：`banks/create`/`banks/{id}/delete`/`runs/{id}/delete`/`frameworks`/`kb-search` 等）为平铺** `{status, banks|...}`。前端 `evaluator-api.ts` 按端点实际结构读取。
- **预留端点**：`banks/{id}/delete` 前端暂未消费（2026-08-21 校验确认），保留路由；前端新增消费时同步本文。
- 评估运行是后台任务（`_bg()` 线程 + `evaluator.py` 判卷 LLM）：状态字段是前端轮询依据，改状态字面量双边同步。
- 前端寄宿于 ai-assistant 模块（无独立前端模块），评估页在 AI 模块内。

## 本 App 协议要点

无 WS / SSE（评估进度经 HTTP 轮询）。

## 关单附加项（全局清单的 delta）

```
[ ] Serializer 与 Model/前端契约一致（评分维度、状态字段）
[ ] 新 framework 经 BaseAdapter + register，无散落 import
[ ] 评估后台任务失败有 message/日志，无静默吞错
[ ] 改字段含 migration + 前端 ai-assistant 同步
```
