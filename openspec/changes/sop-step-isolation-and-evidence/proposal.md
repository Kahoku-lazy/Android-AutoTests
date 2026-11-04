## Why

2026-11-03 的 TASK-178（定时任务测试-02，5 步）实测：**580s、¥1.2542、135 次模型调用**，5 步全部首判通过——任务本身是健康的，但拆开看有三处可复用的浪费：

1. 验收提示词白纸黑字写着「系统提示词末尾附有日志关键词表（关键词 → 功能点）」，但**引擎侧根本没有这张表**。step2 的验收模型连续盲猜 13 次 `check_device_log`（`schedule` / `timer` / `timer_set` / … / `ble_response`）才命中 `timer_configs_set_success`，step3、step4 继续猜，19 次日志调用里约 17 次是猜。
2. 执行模型拿不到入口锚点，只能靠视觉试错：step2 为找「添加定时」**上滑找底部 → 下滑回顶 → 4 次盲试 xpath → 最终放弃新增、改为改已有任务**，花掉约 10 次调用、约 50s；时间滚轮算出行高后放弃分钟列，只改了小时。
3. **一个用例 5 步共用同一个执行者**，对话历史只增不减：单次调用输入从 step1 的 8.7K 涨到 step5 的 28.7K，5 步共 239 万输入 token（¥0.98 全是输入）。后几步在为前几步的截图与工具返回付费。

## What Changes

- **新增按型号的日志关键词目录**：`engines/agents/config/data/log_keywords/<SKU>.md`（先落 `H6810.md`），按「功能点 → 关键词」维护，随该步注入验收角色；验收提示词改为「优先用步骤给出的关键词，其次查表，禁止连续盲猜」。
- **用例步骤升级为结构化字段**：`steps[]` 新增可选 `anchor`（页面 / 入口 / 目标元素）与 `log`（`sku` / `port` / `keyword`）；装载时校验，注入时**只给当前步**——`anchor` 只进执行者提示，`log` 与关键词表只进验收者提示，保持「执行者看不到验收标准、验收者看不到动作」的既有边界。旧用例（只有 `action` / `assert`）行为不变。
- **每个 SOP 步骤新建角色实例**：装配入口改为接收「角色工厂」，每步现建执行者与验收者，上下文归零。**BREAKING**（内部装配 API 与运行行为）：装配不再复用同一实例，随之删除「最近 3 步保留截图」的上下文裁剪要求。
- **不改**：任务与用例的对外语义、SOP 状态机、事件流与判决、计费口径、提示词的其余纪律条款。

## 关联文档

无 PRD 需求编号。来源是线上执行过程复盘：`dev_docs/DEV_TEST/分析-定时任务178执行过程与优化空间-20261103.md`（TASK-178 的时间/费用分布、13 次盲猜与 4 处绕路的原文证据）。约束来源：`openspec/specs/agent-sop-workflow`、`agent-sop-runner`、`role-prompt-guardrails`。

## Capabilities

### New Capabilities

（无：不新增能力，只调整 SOP 步骤的输入粒度与角色生命周期。）

### Modified Capabilities

- `agent-sop-workflow`: 「Assembly uses the supplied roles」改为「接收角色工厂、每步新建实例」；删除「Recent steps keep screenshots」（新实例无历史，裁剪不再有意义）；新增「每步只注入本步锚点与日志证据」「验收步骤自带按型号的关键词目录」两条需求。
- `agent-sop-runner`: 「用已就绪的角色装配 SOP」由「复用智能体实例」改为「复用角色配置、每步新建实例」。
- `role-prompt-guardrails`: 「验收提示词声明证据纪律」补充「关键词来自步骤证据或关键词表，禁止连续盲猜」。

## Impact

- 代码：`engines/agents/workflow/case_file.py`（结构字段解析）、`engines/agents/workflow/ui_auto_workflow.py`（工厂化 + 步骤简报注入）、`engines/agents/workflow/platform_run.py`（每步新建 + 传递步骤对象）、新增 `engines/agents/workflow/step_brief.py`、新增 `engines/agents/config/log_keywords.py`、`engines/agents/config/data/log_keywords/H6810.md`、两个提示词 md。
- 测试：新增 `test_step_brief.py`、`test_log_keywords.py`、`test_sop_step_isolation.py`、`test_log_keyword_catalog.py`（md 与 `backend/config/device_log_keywords.json` 的一致性）；更新 `test_case_run_continuity.py`（步骤元组 → 步骤对象）与 `test_agent_middleware_assembly.py` 之外的相关用例。
- 行为：同一用例的执行时间与费用预期下降（TASK-178 基线 580s / ¥1.25，目标 ~380–430s / ¥0.6–0.7），每步多 1 次截图确认；用例与判决结果不变。
- 不影响：前端、数据库结构、计费规则、事件折叠、任务清单展示。
