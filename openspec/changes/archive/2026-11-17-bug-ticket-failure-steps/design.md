## Context

见 proposal.md 的 Why。当前工作流终态只把没通过的步骤名放进 `Task.result.failed`，期望结果留在步骤 YAML 的 `description`，收口后不再可读。`bug_manager` 只读这份结果和最后一条 `StepInterruptedEvent`，详情把纯文本丢进一张错误卡。任务清单已不再注册 `/tasks/:id`，BUG 单的关联链接是死链。

约束：`bug_manager` 只读 `Task`，写库只走自己的 `api.py`；登记失败不能改任务终态；任务删除后 BUG 单仍要能读；不恢复任务详情页，不把 HTML 报告正文抄进台账。

## Goals / Non-Goals

**Goals:**

- 收口时一次写完失败步骤快照，之后登记与展示都只读这张快照。
- 一张当前工作流失败对应一张 BUG 单，详情能直接回答四问。
- 旧的按用例拆单与纯文本详情继续可用。

**Non-Goals:**

- 不从 `task_events`、HTML 报告或步骤 YAML 回补历史单。
- 不改任务状态、计费、工作流编排，也不恢复 `/tasks/:id`。
- 不把工具返回、截图、日志搬进 BUG 单。

## Decisions

### 1. 失败步骤写进 `Task.result.failed_steps`

收口成功路径在 `task_runner.py` 组结果时，按步骤顺序写入没通过的步骤。每步字段固定为：

| 字段 | 来源 |
| --- | --- |
| `seq` | 步骤顺序，从 1 起 |
| `name` | 步骤名 `subject` |
| `expected` | 该步必须达成的结果；取不到时写「未记录」 |
| `actual` | 最后一次验收说明；空则写「未记录」 |
| `attempts` | 实际尝试次数 |
| `kind` | `verdict` / `provider` / `device` / `platform` / `interrupted` |

`failed` 仍保留步骤名列表，列表摘要仍读 `reason`，避免任务清单摘要变长。`workflow_id` 继续由既有合并逻辑保留。

步骤对象现在只有 `subject` / `passed` / `attempts` / `message`，没有期望结果。收口前把步骤 YAML 的 `description` 按同序配到结论上，只在 `task_runner.py` 组载荷时使用，不改 SOP 引擎的步骤模型。

备选：登记时再读 YAML。任务附件可能已删，且 `bug_manager` 不应读任务附件实现。不采用。

### 2. 抛错和中断也写同形的一步

| 终态 | `kind` | 步骤名 | 期望 | 实际 |
| --- | --- | --- | --- | --- |
| 步骤没通过 | `verdict` | 步骤名 | 该步 `description` | 验收说明 |
| 模型拒绝 | `provider` | 模型拒绝 | 该步应完成 | 短原因 |
| 设备命令失败 | `device` | 设备命令失败 | 该步应完成 | 短原因 |
| 平台错误 / 无步骤结论 | `platform` | 平台错误 | 每步都有验收结论 | 短原因 |
| 预算、进程丢失、停机超时 | `interrupted` | 任务中断 | 流程应跑完 | `cause` 对应的中文原因 |

抛错路径若内存里已经有没通过的步骤，以这些步骤为准，`kind` 仍取抛错类别，避免现在「`provider` 短路、丢掉步骤」的行为。清扫写成的中断在 `task_list.api` 收口载荷里带上同形的一步，`bug_manager` 不解释 `cause`。

备选：只给 `verdict` 写步骤，抛错继续一句原因。用户无法区分「停在哪一类、期望是什么」。不采用。

### 3. BUG 单用可空 JSON 字段保存快照

`BugTicket` 增加可空 JSON 字段 `failure`，形状为 `{"steps": [...]}`。空值表示旧单。`detail` 继续保存给人读的短文，供关键字搜索和旧详情兜底。

当前 `assistant_sop` 的来源键固定 `task`。标题为 `步骤未通过：<第一个步骤名>`；非步骤失败用类别中文名，如 `模型拒绝：<任务标题>`。多个步骤都在 `failure.steps` 里，不另建来源键。

没有 `failed_steps` 的历史 `device_control` / `case_authoring` 仍走现有提取，来源键不变。已存在的 `case:<hash>` 行不被删除、不被合并。

重复登记仍只更新标题、正文、`failure` 与任务快照，不碰 `status` / `resolved_at`。

备选：把四问拼进 `detail`，前端再解析。旧正文规则已经要识别冒号，再叠一层结构会把堆栈和 URL 判错。不采用。

### 4. 接口返回快照，页面不解析 `detail`

列表与详情都返回 `failure_steps`。没有快照时为空数组。详情另返回 `report_run` / `report_name`：任务还在且结果里两者都有才返回，否则空串。BUG 单不保存报告路径副本；任务删除后入口自然消失，符合「没有报告就不给按钮」。

前端详情：有 `failure_steps` 时按四问渲染，第一项展开，其余用原生 `details` 折叠。没有时沿用现有错误卡与行首加粗。字号仍只取 16px / 14px。卡片几何沿用现有错误卡，不新造皮肤。

「查看报告」复用任务清单已有的报告读取函数，不在 BUG 页再拼一套报告地址。列表关联任务列改为纯文本任务编号。

### 5. 原因类别只在 BUG 单翻译

`kind` 到中文的对照放在 `bug_manager` 与前端常量各一份，取值只有规格里的五类。任务清单状态标签仍是「任务失败 / 已中断」，不按 `kind` 拆标签。

## 模块防火墙自检

- `task_list` → `bug_manager`：仍只在终态写库后调用 `bug_manager.api.record_task_bugs`。
- `bug_manager` → `task_list`：只读 `Task` 与既有的 `TaskEvent` 查询；不 import `task_runner`、`task_reports` 或 views。报告定位从 `Task.result` 读取。
- 写库仍只在 `bug_manager/api.py`。新增字段由迁移添加，视图不直写 ORM。
- 前端只经 `/api/bugs/*` 取 BUG 数据；打开报告复用任务清单已公开的报告读取函数，不直连数据库，不请求已下线的 `/api/tasks/{id}/report/`。

## Risks / Trade-offs

- [抛错发生在步骤结论产生之前] → 用类别中文名作唯一步骤，实际结果用短原因，不假装知道步骤名。
- [历史单没有期望结果] → 不回补；详情退回原文。新任务从收口开始有快照。
- [同步把旧的按用例单和新的任务级单同时留下] → 只对没有快照的旧结果保持拆单；有快照的当前任务固定来源键 `task`。
- [报告文件后来被清掉] → 按钮只表示当时有定位；打开失败沿用任务清单现有错误提示，不把报告正文存进 BUG 单。
- [JSON 字段增加列表体积] → 一步通常只有短句；列表上限仍是 500 条。不在列表返回 `detail` 全文。

## Migration Plan

1. 先加可空 `failure` 字段，旧行读出来为空，行为不变。
2. 再改收口与提取。新失败任务自动带快照；历史任务靠「同步历史错误」补录，不写数据迁移脚本。
3. 最后改详情与链接。回退时前端忽略 `failure_steps`，后端字段可留空，不需要删列才能恢复旧页面。

## Open Questions

无。一张单、第一失败步做标题、有报告才显示按钮，已按本轮确认写入规格。
