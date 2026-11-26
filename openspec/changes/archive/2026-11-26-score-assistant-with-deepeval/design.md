## Context

当前评测（2026-11-19 落地）是自研发布闸门，实测已把自己锁死：

| 事实 | 证据 |
| --- | --- |
| 闸门与自测的样本集口径不一致 | [api.py:404](backend/apps/ai_assistant/api.py:404) 落 `["A1"]`/`["S1","S2","S3"]`，[api.py:569](backend/apps/ai_assistant/api.py:569) 比 `["A1","S1","S2","S3"]` → 永不相等 |
| 尺子把「守卫拦住」判成违规 | S3 的步骤只有一条 `{"tool":"adb_tap","text":"未挂载"}`，仍产出 2 条失败（[live_rulers.py:16](backend/apps/ai_assistant/services/live_rulers.py:16)） |
| 实际后果 | workflow run 5 `fingerprint` 完全一致，`eval_passed` 仍为 False；任何名片/工作流都发不出去 |

同时它**不回答质量问题**：4 条规则只知道「合规/不合规」，作者改一版提示词无从判断好坏。

DeepEval 的事实在官方文档与 PyPI：4.3.5、`Requires-Python >=3.10,<4.0`（本机 3.13 可装）、50+ 指标、`GEval` 用 LLM-as-a-judge 给 0–1 分与理由、可用 `DeepEvalBaseLLM` 接任意模型、遥测用 `DEEPEVAL_TELEMETRY_OPT_OUT=1` 关闭。代价是 32 个依赖（`grpcio` / `opentelemetry-*` / `posthog` / pytest 插件四件套）；`requirements.txt:41` 的注释显示这个包历史上在过。

## Goals / Non-Goals

**Goals**

1. 评测只产分数与理由，落库可对比历史。
2. 发布回归「草稿 + 编辑权」，评分只作参考。
3. 旧自测机制（表、服务、假世界、剧本）彻底删除。
4. 评分成本可控：一次评测 = 2 次判分调用。

**Non-Goals**

1. 不做轨迹级指标（`ToolCorrectness` / `StepEfficiency`）——需要把 `aligned.json` 转成 DeepEval trace，留待下一轮。
2. 不接 Confident AI 云、不做 CI 闸门、不做自动重评。
3. 不为评分触发真机运行。

## Decisions

**D1 只做两项指标，用 `GEval` 各调一次。** `prompt_quality`（评系统提示词正文）与 `handover_quality`（评交接文本）。备选「拆成 5 个维度各调一次」被否：成本 ×5，且作者要的是趋势不是雷达图。维度写进 `criteria` 与 `evaluation_steps`，由一个总分承载。

**D2 判分模型用 DeepSeek，走 `DeepEvalBaseLLM` 子类。** 依据官方「Using Custom LLMs」：实现 `get_model_name` / `load_model` / `generate(prompt, schema)` / `a_generate`，`schema` 存在时返回对应 Pydantic 实例（否则结构化指标会 `AttributeError`）。默认 `deepseek-chat`（比 `flash` 稳），key 走 `DEEPSEEK_API_KEY`，base_url `https://api.deepseek.com`。不把 judge 配成平台角色，避免"自己评自己"。

**D3 评分表拆两张：run 与 item。** `ai_eval_scores`（一次评测一行：kind/target_id/prompt_fingerprint/source_ref/judge_model/created_at）与 `ai_eval_score_items`（每指标一行：metric_key/score/reason/threshold）。理由：历史对比要按指标聚合，塞 JSON 里查询要全表扫。

**D4 交接文本从已归档产物里选，不重跑。** 助手侧候选来自对话栏日志（`logs/agents/assistants/<assistant_id>/<thread_id>/<stamp>/*.aligned.json` 的 `summary.final_text`），工作流侧来自任务报告目录。选中项记 `source_ref`（如 `assistant:<aid>:<thread>:<stamp>` 或 `task:<id>:<run>`）。备选「评测时现场跑一次任务」被否：慢、占设备、与"只打分"冲突。

**D5 `deepeval` 延迟导入，遥测关闭。** 只在评分服务里 `import deepeval`，不让 Django 启动就加载它那套 pytest 插件；进程启动时设置 `DEEPEVAL_TELEMETRY_OPT_OUT=1`。依赖进 `requirements.txt` 主清单（不改 CI 结构）。

**D6 判分用量单独入账。** 复用 `usage_ledger.record_usage`，`source="assistant_eval_judge"`、`category="LLM"`，`event_id` 用 `assistant_eval_judge:<score_run_id>:<metric_key>` 保证幂等；入账异常只记日志。

**D7 删除一步到位，但只删本轮明确点名的东西。** 三张表 + 五个服务文件 + engines 里的 `eval_probe` / `fake_world` / `scripted`。`usage_ledger` 里历史 `assistant_eval` 记录保留（账不能删）。

## 数据模型

```text
ai_eval_scores
  id, target_kind(assistant|workflow), target_id, prompt_fingerprint,
  source_ref, judge_model, created_by, created_at
ai_eval_score_items
  id, score_id(FK), metric_key(prompt_quality|handover_quality),
  score(Decimal 0-1), reason(Text), threshold(Decimal), created_at
```

`prompt_fingerprint` 沿用现有 `_fingerprint(_release_payload_for_assistant(card))` 的口径，用来回答「这个分数评的是哪一版提示词」。

## 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/ai/eval-scores/` | 发起一次评分 `{kind, target_id, source_ref?}`，同步返回两项指标（单次 2 个判分调用，超时 120 s） |
| GET | `/api/ai/eval-scores/?kind=&target_id=&limit=` | 历史评分（含 items 嵌套） |
| GET | `/api/ai/eval-candidates/?kind=&target_id=` | 可选的历史运行产物列表（助手：对话栏日志；工作流：任务报告） |

旧的 `/api/ai/evals/run/`、`/api/ai/evals/runs/{id}/` 下架。

## Risks / Trade-offs

1. **判分不确定**：同一文本两次分数可能差 0.05–0.1。缓解：分数只作参考、历史对比看趋势；记录 `judge_model` 与时间，跨模型分数不混比。
2. **依赖体积**：`deepeval` 带 `grpcio` / `otel` / pytest 四插件。缓解：只在评分服务内延迟 import；确认 `run.py check` 的 pytest 收集未被插件影响（真跑一次门禁验证）。
3. **中文判分质量**：G-Eval 用 `deepseek-chat`，中文没问题，但 `criteria` 必须写具体。缓解：`criteria` 里列 4 条可判定点，避免"整体感觉好不好"这种无法收敛的表述。
4. **删除不可逆**：三张表的历史自测记录会消失。缓解：迁移里只 drop 表，先在本机 `showmigrations` 验证；发布后用一条 `downgrade` 不可行，需从备份恢复（已在设计里列为已知代价）。
5. **评分接口同步耗时**：2 次判分约 5–20 s。缓解：前端加 loading；超过 120 s 返回超时错误但不写半条记录（先算完再落库）。

## Migration Plan

1. 先装依赖并跑通一个一次性脚本：对现有 `Android-UI-执行` 提示词打分，确认 `deepeval` + DeepSeek judge 可用、遥测已关。
2. 加两张表与评分服务、接口；前端改造。
3. 解绑发布闸门（`eval_passed` 调用删除），确认「草稿 + 编辑权」即可发布。
4. 删旧代码与三张表（独立 migration），跑门禁与灰盒用例。
5. 更新 `openspec/specs/assistant-eval/spec.md` 的 Purpose（原文写的是"五把纯函数尺子"，已不成立）。

## Open Questions

无。评分维度文案按 D1 落地；若后续要维度级分数，再单开变更接 `DAGMetric` 或多次 `GEval`。
