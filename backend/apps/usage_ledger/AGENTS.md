# usage_ledger 模块 AGENTS.md

> 二级约束：根 `AGENTS.md`、`backend/apps/AGENTS.md` 优先。

## 职责

全局模型用量明细账本：

| 文件 | 职责 |
| --- | --- |
| `models.py` | `ModelUsage` → `ai_usage_records`；UUID 主键、event_id 唯一 |
| `pricing.py` / `pricing.json` | 可配置官方价目表与费用计算 |
| `api.py` | 幂等写入、语音事件入账、分类/厂商汇总、最近明细 |

## 红线

1. **UUID 是关联键**：`usage_id` 必须同时存在于账本与事件流；`event_id` 唯一用于幂等。
2. **厂商只有两类**：DeepSeek Key → `deepseek`；DashScope Key → `dashscope`。
3. **分类固定**：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`；新增类型才加条目。
4. **不伪造金额**：价目表未收录或 `unpriced` 时 token 照记，费用为 0。
5. **写入不阻断主流程**：任务/语音入账失败只记日志，不影响任务或语音会话。
6. **不写业务表**：本 App 只写 `ai_usage_records`，不修改任务/语音数据。

## 快速验证

```powershell
python manage.py check
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_usage_ledger.py -q
ruff check backend/apps/usage_ledger
```
