# eval · deepeval 封装
> 归属模块：`engines/eval` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/eval/judge.py`、`engines/eval/methods.py`、`engines/eval/runner.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../../../engines/AGENTS.md) → **本文件**。本文件只写评测原语增量；**冲突时本文件的领域规则优先**。

## 职责

把 deepeval 收成可复用的评测原语。上层只传「样本 + 方法 + 裁判」，这里返回分数、理由和一份官方看板。不认平台角色、不读业务表、不写数据库。

| 路径 | 职责 |
| --- | --- |
| `judge.py` | `build_judge`：`deepseek` 用官方 `DeepSeekModel`，`dashscope` / `openai` 用官方 `OpenAIModel(base_url=...)`；密钥在本包内读 |
| `methods.py` | 方法目录 3 项（`prompt_quality` / `handover_quality` / `case_suite`），判定点是固定 `evaluation_steps` |
| `runner.py` | `run_evaluation`：调官方 `evaluate()`，落 `test_run_*.json` 与 HTML 看板 |

## 红线（禁止）

1. **全仓只有本包 import deepeval**，且必须放在函数内。`list_methods()` 不得触发 deepeval 导入。
2. **不依赖 `ae_harness`**。二者同级，各封装一个外部框架；密钥不复用 `load_secret`。
3. **不手写 `DeepEvalBaseLLM`**。官方已有 `DeepSeekModel` / `OpenAIModel`，用量从官方 metric 的 `input_tokens` / `output_tokens` 取。
4. **不传 `criteria`**。判定点只写 `evaluation_steps`；只传 `criteria` 时官方每次重新生成步骤，分数会漂。
5. **不自研单次图表**。看板用 `DisplayConfig(file_type="html")`。官方只在 `print_results=True` 时导出 HTML，所以这里必须开着。
6. **零 Django**：禁止 `import apps.*` / `django.*` / `backend.apps.*`。

## 已知行为

- DeepSeek 不返回 logprobs。G-Eval 先走 logprobs，失败后官方自己退回 JSON 打分，不需要我们兜底。
- 一次 `evaluate()` 的指标整批共用。提示词与交接要各跑一次，第二次用 `results_subfolder` 落到同一结果目录。
- 官方收尾会往控制台打 `⚠`。Windows GBK 控制台会 `UnicodeEncodeError`，所以进入本包时把 `PYTHONIOENCODING` 设为 `utf-8`。
- 遥测用 `DEEPEVAL_TELEMETRY_OPT_OUT=1` 关闭，不接 Confident AI。

## AI 阅读与检查流程（必读）

1. 先读 [`engines/AGENTS.md`](../../../../engines/AGENTS.md)。
2. 改裁判、方法目录或看板导出时再读**本文件**。
3. 写代码前读 style rules；自检：`--path engines/eval`。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层入口 | [`engines/AGENTS.md`](../../../../engines/AGENTS.md) |
| 业务合成 | `engines/backend_bridge/eval/` |
| 官方看板说明 | https://deepeval.com/docs/evaluation-flags-and-configs |
| 官方裁判 | https://deepeval.com/integrations/models/deepseek |
