## Context

动机见 `proposal.md - Why`。方案只依赖当前仓库已确认的事实：

- `engines/agents/config/data/app_info/` 下**只有** `govee_home.md` 一个文件；`agent_config.yaml:11` 与 `:38` 各有一行 `app_info: govee_home`，同文件注释写明「删掉本行即不加注入」，说明该字段本身是可选的。
- `engines/backend_bridge/workflow/sop_ui.py:44` 的 `SPEC_KEYS` 是 `{ui_task, govee_widget}` 两键映射；`run_ui_sop.py` 的 `choices=sorted(SPEC_KEYS)` 由该映射派生，仅帮助文案硬编码了键名。
- `0038_aiagent_device_prompts.py` 依赖 `0037`，而 `0039_sync_device_prompts_tool_name.py:49` 以 `dependencies` 显式依赖 `0038`。该迁移做三件事：加三个 `prompt_*` 字段、用 `_SNAPSHOT_*` 常量播种、提供 `unseed_prompts` 反向操作。
- 统一质量入口是 `python run.py check` → `utils/check_gates.py`，其 `build_gates()` 返回 `Gate(name, desc, blocking, run)` 列表，支持 `--only <逗号分隔门禁名>`；CI 在 `static-checks` job 里已用 `--only silent-except` 调用，全流水线共 6 个 job，AGENTS.md 的验收口径写的是「6 个 job 全绿」。
- 平台对 `app_info` 注入内容与 SOP 键名均无规格约束：`openspec/specs/**` 中检索不到 `app_info`、`ui_task`、`govee_widget`。

## Goals / Non-Goals

**Goals:**
- 移除三处 Govee 专项业务资产，且平台其余能力不受影响（`ui_task` 流程、角色装配、迁移链均保持可用）。
- 让「主干不得携带客户业务资产」成为可反复执行、失败即阻塞的机械判定。

**Non-Goals:**
- 不清理 `openspec/changes/archive/**` 下的 91 个含真机证据的归档文档，也不改写任何已推送历史 —— 该范围需要单独决策，本次不夹带。
- 不改动已推送提交，不做任何 `--force` 操作。
- 不替换 `govee_chat_flash` 模型别名、`com.govee.home` 包名、`D:\Govee` 默认路径等 63 个功能性引用 —— 替换它们会改变运行行为并超出本变更范围。
- 不新增自定义异常类（`engines/` 红线要求先立项）。

## Decisions

### 决策 1：`0038` 迁移保持原样，另加一条数据迁移收敛数据

`0038` 是已发布迁移，`0039` 显式依赖它。三个备选的代价：

| 备选 | 问题 |
| --- | --- |
| 删除 `0038` | `0039` 的 `dependencies` 指向不存在的迁移，`migrate` 直接失败；且已执行该迁移的库 `django_migrations` 留存记录，状态不一致 |
| 就地改写 `_SNAPSHOT_*` | 属于「改已发布迁移」：新库播种新文案、旧库无变化，同一迁移号在不同库产生不同结果，历史不可重放 |
| **新增数据迁移覆盖（选定）** | 迁移图完整，两个方向都收敛，且反向操作可恢复 |

选定方案的实现要点：新迁移做**词级收敛**，只替换厂商标识本身（短语优先、裸标识兜底、大小写不敏感），保留提示词其余结构与人工改动。比「整段快照精确匹配」更窄：人工改过但没删干净的行同样会被收敛，而不是被跳过。反向为 `RunPython.noop` —— 占位符无法无损还原，且还原等于重新写入客户业务信息，本迁移按设计单向。

### 决策 2：门禁内容匹配限定在受管目录，不做全仓匹配

全仓匹配会命中 63 个功能性引用文件，门禁一上线就是红的，等于不可用。因此内容匹配只覆盖 `engines/agents/config/data/app_info/` 与 `engines/ae_harness/workflow/sop/steps/` 这两个存放业务资料的目录；再叠加一份精确路径黑名单，防止已删资产被重新加回。判定口径为大小写不敏感的子串匹配，同时检查路径与内容。

### 决策 3：门禁挂在 `check_gates.py` 并复用 `static-checks` job，不新增 job

三个备选的代价：

| 备选 | 问题 |
| --- | --- |
| 新增第 7 个 CI job | AGENTS.md 的验收口径写死「6 个 job 全绿」，改这个数字属于修改 AGENTS.md 条款，需先走变更申请 |
| 仅 pre-commit 钩子 | 只在本地生效，`--no-verify` 可绕过，且仓库未配置统一 `core.hooksPath`，装了也不保证团队一致 |
| **`check_gates.py` 新门禁 + 复用现有 job（选定）** | 本地 `python run.py check` 自动覆盖；CI 把既有 `--only silent-except` 扩为 `--only silent-except,business-asset`，job 数不变，无需改 AGENTS.md |

### 决策 4：`app_info` 采用「删文件 + 摘引用」，不走「留空 token」

依据 `agent_config.yaml` 自带注释（「删掉本行即不加注入」），摘除两行 `app_info:` 是该字段被支持的正规用法。保留一个内容为空的 `govee_home.md` 会让目录继续携带厂商标识，反而违反门禁。

## 模块防火墙自检

- **跨 App import**：无新增。改动只涉及 `ai_assistant` 自己的管理命令与迁移，以及 `engines/` 内部两处常量表。
- **依赖方向**：`engines/` 仍不反向依赖 `apps.*`；`backend_bridge` 只依赖 `engines.ae_harness`，与现状一致。
- **写操作收敛**：新增迁移只操作 `ai_assistant` 自身的 `AIAGent.prompt_*` 字段，写入发生在该 App 的 `migrations/` 内，属于该 App 自己的写路径，不跨越其他 App 的 `api.py` 边界。
- **前端**：本次不涉及前端，不直连数据库，无仪表盘写操作。

## Risks / Trade-offs

- [数据迁移误覆盖人工编辑过的提示词] → 只在 `prompt_*` 仍精确等于原快照文本时改写；不匹配的行跳过并在输出里计数。
- [迁移编号与并行分支冲突] → 取当前最大编号的下一个号（`0064` 之后为 `0065`），落地前重新确认一次。
- [门禁误杀将来新增的其他厂商资产] → 受管目录 + 受限标识清单都做成可扩展常量，清单条目集中在一处。
- [删除 `govee_widget` 后旧调用方报错] → 属预期的 **BREAKING**；`run_ui_sop` 的 `choices` 由 `SPEC_KEYS` 派生，非法值在参数解析阶段即被拒绝，且帮助文案同步更新，不会出现指向缺失文件的路径。
- [内容匹配漏判二进制或编码异常文件] → 按 UTF-8 解码并忽略解码失败的字节，宁可放行也不因解码问题误报。

## Migration Plan

1. 删除两个业务资产文件；摘除 `agent_config.yaml` 两处 `app_info:` 与 `SPEC_KEYS` 的 `govee_widget` 键；同步 `run_ui_sop` 帮助文案。
2. 新增数据迁移 `0065_*`：正向按词级替换收敛厂商标识，反向为 `noop`（单向）。
3. 在 `utils/check_gates.py` 增加 `business-asset` 门禁并注册到 `build_gates()`；把 CI `static-checks` 的 `--only` 参数扩为两个门禁名。
4. 本地跑 `python run.py check` 确认全绿。
5. **回退**：代码与配置改动由单个提交承载，`git revert <sha>` 即可。数据侧不可回滚（迁移反向为 `noop`），这是单向收敛的既定代价。
