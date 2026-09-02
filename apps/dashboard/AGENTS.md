# dashboard App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.2 · 最后更新：2026-09-01 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开；v1.1：新增 AI 用量聚合与 DeepSeek 计费说明（`apps/dashboard/ai_usage.py`）；v1.2：AI 用量口径由「对话」改「任务」（AITask）。

## 红线（全局索引表 dashboard 行的展开）

| 只做 | 禁止 |
|------|------|
| 聚合各 App 数据的只读统计（stats/activities） | **任何写操作**（全平台唯一只读区，前端同理） |
| 跨 App 只读 ORM 查询（防火墙 #2 读放开） | import 其他 App 的 service/内部实现 |

- 聚合口径依赖各 App Model 字段；字段改名时本 App 的统计 SQL/查询必须同改，否则静默返回错误口径。

## 本 App 契约（特例 + 真相源）

真相源：`apps/dashboard/urls.py`（4 端点挂在 `/api/` 下：`dashboard/stats/` / `dashboard/activities/` / `devices/stats/` / `cases/stats/`）+ `views.py`。

- **路由前缀特例**：本 App 是唯一挂载在 `/api/` 根下而非 `/api/{app}/` 的 App（`config/urls.py` 第 18 行），新增端点时注意路径命名不与其它 App 冲突。
- 信封走全局标准 `{status, data}`。
- 无 models（纯聚合），无 `api.py`——无写路径，也就不存在跨 App 写问题。
- 模块文件：`views.py`（4 端点 + 聚合辅助）+ `ai_usage.py`（AI 用量聚合与 DeepSeek 计费，纯只读，见下节）。

## AI 用量聚合与 DeepSeek 计费（`ai_usage.py`）

- **文件**：`apps/dashboard/ai_usage.py`（纯只读，无任何写操作），承载 `ai_usage_stats()`（今日/累计）与 `ai_daily_series()`（近 12 天逐日），读 `ai_assistant` 的 `AITask`（`input_tokens` / `output_tokens` / `cache_input_tokens` / `model_usage`）。任务 token 由工作流采集落库（`agent_scope/workflow.py` 采集 → `api.finalize_task` 落库）。
- **DeepSeek 官方价目 = 可配置常量 `DEEPSEEK_PRICING`**（`ai_usage.py` 顶部，元 / 百万 tokens）：`deepseek-v4-flash` / `deepseek-v4-flash-vision-exp`（命中 0.05 / 未命中 1.5 / 输出 4.5）、`deepseek-v4-pro`（0.15 / 4.5 / 13.5）。**官方调价只改此常量，聚合逻辑不变**（参考 https://api-docs.deepseek.com/zh-cn/quick_start/pricing）。
- **高峰/空闲时段计费**：高峰时段 = 北京时间周一至五 9:00–12:00、14:00–18:00，单价 ×2（`_is_peak_time`）。**依赖 `config/settings.py` 的 `TIME_ZONE=Asia/Shanghai` + `USE_TZ=False`**（`created_at` 即北京时间 naive datetime，直接取 `weekday/hour`）；改时区必须同步 `_is_peak_time`，否则计费错峰。
- **旧模型别名** `_DEEPSEEK_MODEL_ALIASES`：`deepseek-chat`→flash 档、`deepseek-reasoner`→pro 档（官方定价页已下线旧名仍可计费）。
- **费用口径**：`命中×命中价 + (输入−命中)×未命中价 + 输出×输出价`，再按高峰 ×2；结果保留 4 位小数。
- **契约字段**：`ai_usage` 含 `task_count` / `input_tokens` / `output_tokens` / `total_tokens` / `cache_hit_tokens` / `cache_hit_rate` / `avg_tokens_per_task` / `deepseek_cost`（均 `{today,total}`）；`charts.ai_tokens`（`{labels,total_tokens,cache_tokens}`）、`charts.deepseek_cost`（`{labels,cost}`）。字段改动须同步 PRD-01 §5.2 与前端 `dashboard` 模块。

## 本 App 协议要点

无 WS / SSE。数据经 HTTP 拉取，仪表盘不订阅实时通道。

## 关单附加项（全局清单的 delta）

```
[ ] 无任何 INSERT/UPDATE/DELETE（grep 本 App 无 .create(/.save(/.delete(）
[ ] 聚合口径与来源 App Model 字段逐一核对（字段改名时）
[ ] 只读跨 App 访问仅 Model import，无 service import
```
