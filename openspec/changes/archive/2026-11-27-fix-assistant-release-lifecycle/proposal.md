## Why

复查「新建助手 → 发布 → 跑」整条链路后，发现三类问题同时存在：

1. **规格已写、代码没跟上**：`assistant-release` 要求「其他用户直接访问草稿 MUST 得到 404」，但头像、对话栏、日志三个接口没有任何可见性校验；`ai-assistant-test-chat` 要求「草稿助手 MUST NOT 允许其他用户打开新的对话」，实际任何登录用户拿到编号即可建栏、读消息、发消息、删栏。
2. **规格内部矛盾**：`assistant-release` 要求「新提交的工作流任务 MUST 记下版本、开跑与重跑 MUST 读取该版本」，但 `task_runner` 只有 SOP 分支读版本，goal / team 读实时配置；任务却照样记下 `release_version`，数据在说谎。
3. **状态机漏一条边**：`update_sop_workflow` 从不退回草稿，已发布工作流改绑定后任务仍跑旧快照、发布按钮消失、后端拒绝重发，编辑静默无效；名片侧同一问题只对显示名成立（规格明确要求改名不退回）。此外 `revision` 乐观锁后端已实现、前端从不回传，两名作者同时编辑会互相覆盖。

同时，运营可以删掉仍被名片引用的 Agent 配置，让助手在下一次对话时 409、工作流在下一次发布时炸，故障点离操作很远。

## What Changes

- **草稿不可经旁路外泄**：头像、对话栏列表/新建、对话栏详情/改名/发送/取消/删除、对话栏日志列表，对非作者且名片未发布时统一返回 404（与名片详情同口径，MUST NOT 403）；已发布名片对所有登录用户保持可对话。
- **任务版本口径收敛**：只有 `orchestration = sop` 的提交记录 `release_version`；`goal` / `team` 记录编排与种类但不记版本，开跑读该工作流的**最新发布版本**（从未发布时回落实时配置）。理由：这两类的输入是自然语言目标，按旧版本复现没有意义；记一个不会被读取的版本号会误导排查，而"读实时配置"会让未发布的草稿改动泄漏进运行，所以取最新发布版本。
- **发布前校验引用**：名片发布要求所引用 Agent 配置存在；工作流发布要求两侧（team 为队长与全部成员）名片已发布；缺少引用时 400 并给出可读原因，MUST NOT 冻结一份空提示词/空模型的版本。
- **发布状态机补齐**：工作流在名称、执行/验收/队长绑定或成员变化时退回草稿并 `revision + 1`；名片维持规格——只改显示名、头像、笔色保持已发布。
- **运行名不再冻结在版本里**：版本仍记录发布当时显示名作留痕，但解析任务绑定与对话快照时使用名片当前显示名，避免改名后报告永久停在旧名。
- **乐观锁启用**：前端 `PATCH` 回传 `revision`，后端已有的比对生效；不一致返回 409「内容已变化，请先刷新」。
- **删除保护**：删除被名片引用的 Agent 配置返回 400 并列出占用名片名。
- **顺手**：助手列表查询排除头像大字段；启动扫描改经 `api.py`；`queue_turn` 的测试判据改用 `settings.TESTING`。

**不新增**：自定义异常类、数据库迁移、对外端点、依赖方向变化、计费口径变化。

## 决策记录（三件拍板 + 一处偏离）

| # | 拍板 | 落地方式 |
|---|---|---|
| 1 | 改名是否算「影响快照」 | 用户授权「算 → 回草稿」。**执行时改判**：与 `assistant-release`「只修改显示名 MUST 保持已发布」及其场景、既有用例 `test_runtime_edit_returns_to_draft_display_name_does_not`、以及「名片本身即发布体，回草稿等于从他人列表下线」三条事实冲突。改为等效目标——报告不出现旧名：版本保留发布时名作留痕，解析时按当前显示名刷新 |
| 2 | goal / team 是否也按版本复现 | 不。只声明「仅 SOP 可复现」，并把不会生效的 `release_version` 落成空值；这两类开跑读最新发布版本，不读实时草稿 |
| 3 | 非作者能否读草稿的对话/头像 | 不能，与列表同口径 404；已发布助手继续对所有人开放 |

## Capabilities

### Modified Capabilities

- `assistant-release`：版本冻结口径（运行名留痕 + 解析刷新）、版本使用方收敛到 SOP、发布前引用校验、工作流回草稿、乐观锁客户端义务
- `ai-assistant-card`：草稿不可经头像/对话接口外泄
- `ops-agent-config`：删除被引用配置必须拒绝

### New Capabilities

（无 —— 全部是既有能力的收紧与补齐）

## Impact

- **代码**：`backend/apps/ai_assistant/{api.py,views_drf.py,apps.py}`、`services/{assistant_cards.py,agent_configs.py}`、`backend/apps/task_list/views.py`、`frontend/src/modules/ai-assistant/{types.ts,api/assistants.ts,components/AssistantEditor.vue}`
- **测试**：`tests/ai_assistant/api/`（名片、对话栏、发布、工作流）与 `tests/task/api/`（提交版本口径）
- **文档**：`.agents/docs/apps/ai_assistant/ai_assistant_agent_config_and_cards.md`、`dev_docs/ARCH_PRD/ARCH-助手数据链路.html`（卡片文案）
- **对外契约**：若干接口在草稿场景的返回码由「200」变「404」；`/tasks/submit/` 对 goal/team 不再写 `release_version`（响应形状不变）
