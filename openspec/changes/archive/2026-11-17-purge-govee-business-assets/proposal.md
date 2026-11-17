## Why

Govee 专项业务资产（App 资料、专项 SOP、提示词样例）混在通用平台主干里，随提交进入公开仓库，把客户业务细节暴露在本应与厂商无关的平台代码中。当前有 5 个未推送提交即将推送，而仓库缺少一道常驻门禁，再不动手就会继续外溢。

## What Changes

- 移除 `engines/agents/config/data/app_info/govee_home.md`，并从 `engines/agents/config/data/agent_config.yaml` 两处 `app_info:` 摘除引用（该行由同文件注释认定为可选，摘除即不加注入）。
- 移除 `engines/ae_harness/workflow/sop/steps/govee_widget.yaml`，并从 `engines/backend_bridge/workflow/sop_ui.py` 的 `SPEC_KEYS` 摘除 `govee_widget` 键，同步 `backend/apps/ai_assistant/management/commands/run_ui_sop.py` 的 choices 与帮助文案。
- **BREAKING**：平台不再提供 `govee_widget` 流程，`run_ui_sop --spec govee_widget` 变为非法取值；`ui_task` 通用流程不受影响。
- `0038_aiagent_device_prompts.py` **不删不改**（`0039` 以 `dependencies` 显式依赖它，删改会断裂迁移图并影响已执行库的迁移状态）。改为**新增**一条数据迁移，把已播种提示词快照中的厂商样例替换为中性示例，使既有库与新建库都收敛到无厂商内容。
- 新增常驻门禁 `govee-business-asset`：受管业务资产目录内不得出现厂商标识，已禁用路径不得复活；接入 `python run.py check`，并复用 CI 现有 `static-checks` job 调用（不新增第 7 个 job，保持「6 个 job 全绿」口径不变）。

## 关联文档

无关联需求编号。本次为安全合规清理（移除客户业务资产 + 补常驻门禁），不新增平台功能需求，故无对应 PRD。

## Capabilities

### New Capabilities

- `business-asset-guard`: 质量门禁中的业务资产封禁规则，覆盖受管目录范围、禁用路径清单、判别口径（大小写不敏感的内容匹配）、以及门禁失败时的退出码与输出要求。

### Modified Capabilities

（无。现有能力规格均未对 `app_info` 注入内容或 `ui_task`/`govee_widget` 流程键名建立需求，本次不改变任何已规格化的行为。）

## Impact

- `engines/agents/config/data/app_info/`、`engines/agents/config/data/agent_config.yaml`
- `engines/ae_harness/workflow/sop/steps/`、`engines/backend_bridge/workflow/sop_ui.py`
- `backend/apps/ai_assistant/management/commands/run_ui_sop.py`
- `backend/apps/ai_assistant/migrations/`（新增一条数据迁移）
- `utils/check_gates.py`、`.github/workflows/ci-phase1.yml`
- 测试范围：`tests/engines/backend_bridge/`（SOP 键集合）、`tests/engines/agents/`（app_info 装配）、门禁自身的用例
- 不涉及依赖方向变化，`engines/` 仍不反向依赖 `apps.*`。
