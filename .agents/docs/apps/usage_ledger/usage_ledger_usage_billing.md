# usage_ledger · 模型用量账本与计费

> 归属模块：`backend/apps/usage_ledger` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/usage_ledger/models.py`、`rates.py`、`pricing.py`、`api.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

全局模型用量明细账本。

| 文件 | 职责 |
| --- | --- |
| `models.py` | `ModelUsage` → `ai_usage_records`；UUID 主键、`event_id` 唯一 |
| `rates.py` | 按模型名索引的**计价基数**：单价、缓存价、倍率、长上下文门槛、汇率、模型映射。换单价只改本表，不改公式 |
| `pricing.py` | 计费**公式**：`lookup_rate` 取基数后算价、分类与厂商归一（`category_of` / `normalize_provider` / `price_usage`） |
| `pricing.json` | 价目兜底（`rates.py` 未收录时使用） |
| `api.py` | 幂等写入、语音事件入账、读库重算费用、分类/厂商汇总、最近明细 |
| `management/commands/recalc_usage_costs.py` | 按当前价目重算历史账本费用（支持 `--dry-run` 与按厂商/来源过滤） |

计价路径：`rates.py` 基数为准，`engines/backend_bridge/model_billing` 只借用高峰规则。

## 红线

1. **UUID 是关联键**：`usage_id` 必须同时存在于账本与事件流；`event_id` 唯一用于幂等。
2. **厂商归三类**：DeepSeek Key → `deepseek`；DashScope Key → `dashscope`；
   其余 OpenAI 兼容 Key → `openai`（grok 系列同一兼容口径，模型名以 `grok` 开头时由 `pricing.py` 单独映射）。
3. **分类固定**：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`；新增类型才加条目。
4. **不伪造金额**：价目表未收录或 `unpriced` 时 token 照记，费用为 0。
5. **写入不阻断主流程**：任务/语音入账失败只记日志，不影响任务或语音会话。
6. **不写业务表**：本 App 只写 `ai_usage_records`，不修改任务/语音数据。

## 快速验证

```powershell
python manage.py check
python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q
ruff check backend/apps/usage_ledger
```

命令全集见 [../self_test_and_checks.md](../self_test_and_checks.md)。
