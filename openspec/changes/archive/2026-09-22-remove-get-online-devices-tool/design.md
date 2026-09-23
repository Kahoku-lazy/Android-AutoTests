## Context

- 工具注册表真相源：`apps/ai_assistant/tools.py` 的 `TOOLS`（工具名 → 函数 + 只读标记）与 `TOOL_META`（工具名 → 分类/module/action）。工具箱、调试 schema、引擎装配都从这里派生。
- 三角色系统提示词不是代码而是 **DB 数据**：`ai_agents.prompt_planner/executor/verifier`，种子来自迁移 `0038_aiagent_device_prompts`，用户可在「设备提示词」页编辑。实测 Agent 10 的 `prompt_executor` 与 `prompt_verifier` 各含一处对该工具名字面引用。
- 引擎侧角色工具子集：`engines/ai/agentscope/config.py` 的 `VISION_TOOLS`（executor 用）。`_select_tools` 按名字取子集、缺失名静默跳过，所以留着该条目不会报错，但会变成死引用，且它正是手册第 43 行说明的来源。
- 仓库内手册 `engines/ai/skills/platform-tools-manual/SKILL.md` 是**给规划/执行/验收模型读的 Skill**，逐条列出工具与数量。
- 前端 `PLATFORM_TOOL_NAMES`（`constants.ts`）**全仓无引用**（实测只有自身定义两处命中），是死常量。
- 同名不同物：`apps/device_pool/api.py::get_online_devices()` 是设备域内部辅助，被 `engine_adapter.resolve_device_serial`、`ui_pipeline`、`model_test`、`test_ai_engine_config` 调用——**不在删除范围**。
- 动机见 proposal.md - Why；条款见 specs/ai-platform-tool-debug。

## Goals / Non-Goals

**Goals:**

- 该工具从 AI 工具面彻底消失（注册表、引擎子集、手册、前端常量、DB 提示词、测试与 spec 场景）。
- 删除后全仓不再存在"指引模型调用一个不存在的工具"的文本。
- 存量提示词的同步 MUST NOT 覆盖用户的编辑内容。

**Non-Goals:**

- 不删 `apps/device_pool/api.py::get_online_devices`（引擎/命令仍用）。
- 不改设备可见性规则、不改工具箱分类定义、不改 `AIPlatformTool` 启停表结构（实测无该工具残行，无需清理）。
- 不删 `PLATFORM_TOOL_NAMES` 常量本身（只删条目）；"它是死代码"作为观察项留在 Open Questions。
- 不顺手统一两个查设备工具的序列化口径（本题是删除，不是收敛）。

## Decisions

**D1 只删 AI 工具，保留 device_pool 同名函数。** 两者调用方互不相交：工具面由 `TOOLS` 派生，设备域辅助由 `device_pool/api.py` 直接导出。合并处理会误伤 `resolve_device_serial` 的兜底取设备逻辑。

**D2 样例工具用 `list_devices` 顶替。** 它同为"无参 + 只读"（`user_id` 在 schema 里被剥掉），且信息更全（含 `status`/`is_current`），适合继续担任 spec 与测试里的"无参只读工具"样例。

**D3 提示词用短语级条件替换，而不是整值比对。** 只替换平台原文的两个短语：

- executor：`必要时调 get_online_devices 或 list_devices 查询` → `必要时调 list_devices 查询`
- verifier：`即 get_online_devices 返回的 serial 字段` → `即 list_devices 返回的 serial 字段`

命中条件 = 字段当前值仍含该原文短语。备选：整值等于 0038 种子才替换 → 否决。整值比对会漏掉"管理员改了提示词别处、但保留了这句 SOP"的情况，而那种情况下模型仍会被指引去调已删工具——正是本变更要消除的状态。短语级替换同样满足"用户已改写该短语则不动"。

**D4 同时更新 0038 种子并新增 0039 数据迁移。** 编辑已应用的 0038 只影响新装（存量库已执行过），因此必须配一个前向数据迁移；0038 与 0039 同单交付，避免新装与存量分叉。

**D5 手册顺带补齐 `ocr_page`（用户已确认）。** 手册原写「12 个 / 设备管理 9」但漏了视觉识别分类（`add-ocr-vision-tool` 之后未同步，实际 13 个）。本单已要改数量与表格，留下已知错误数字没有意义。修正后：12 个 = 设备管理 8 + 设备检查器 1 + 视觉识别 1 + 工作流 2。

**D6 引擎 `VISION_TOOLS` 删条目。** `_select_tools` 虽能容忍缺失名，但保留死引用会让"引擎可用工具集"与"注册表"再次分叉。

## 模块防火墙自检

- **跨 App import**：删除不新增任何跨模块依赖；`ai_assistant` 仍只经 `apps.device_pool.api` 只读取设备，未新增对 `device_pool` 的 models/service/manager 引用。
- **写操作收敛**：新增的数据迁移只更新 `ai_assistant` 自有表 `ai_agents`，不跨 App 写库；无新增 INSERT/UPDATE 于他 App。
- **前端 HTTP 出口**：仅删常量条目，不新增调用。
- **数据库**：无 schema 变更；一个可逆数据迁移。
- **内部网关**：不涉及。

## Risks / Trade-offs

- [数据迁移覆盖用户提示词编辑] → 短语级条件替换：不含原文短语即不动；并提供 reverse（把短语替换回原文）以便回滚。
- [提示词与工具表不一致的窗口期] → 0038 种子与 0039 数据迁移同单交付；部署即一致。
- [别处仍引用该工具名导致 404] → tasks 把"全仓 grep 该名字（排除 device_pool api、归档与历史迁移注释）"列为验证项。
- [删除后 executor 少一个工具] → `list_devices` 覆盖其用途（在线过滤 + serial/status + 更正确的可见性），能力不减。
- [手册数量再次漂移] → 手册同单修正为自洽值，并在 tasks 中要求 grep 校验分类计数。

## Migration Plan

- 顺序：先删注册表条目与引擎子集 → 改手册/常量 → 改测试与 spec 场景 → 最后跑数据迁移。
- 迁移：`0039` forward 做短语替换；reverse 反向替换。无 schema 变更。
- 回滚：代码回退 + `migrate ai_assistant 0038`（反向替换提示词）即可；无数据结构需回滚。

## Open Questions

- `frontend/src/modules/ai-assistant/constants.ts` 的 `PLATFORM_TOOL_NAMES` / `WORKSPACE_TOOL_NAMES` 实测全仓无引用（死代码）。是否另行删除该常量，本单不做。
