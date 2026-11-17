## Context

见 proposal.md - Why。行为合同见本变更的两份 delta spec。

当前代码里，助手名片在 `ai_assistants`，只存 `assistant_id`、展示字段、`role_id` 与工具勾选。提示词和模型在 `ai_roles` / `ai_model_configs`。对话首次发送时，后端把当时名片冻成 snapshot，再交给 `build_card_agent`。SOP 不读这些对话栏。

平台 SOP 的入口是 `run_sop_once`：固定读 `ui_task.yaml`，再由 `build_sop_roles` 用提示词文件名和模型短名造一对角色。`run_sop` 本身只收已经建好的执行者、验收者与 `SopSpec`。任务上传的 YAML 是用例格式，`task_runner` 没有把它交给 `load_spec`。规格 `sop-task-run` 与这段代码不一致，本变更不修那条缝。

`create_agent` 仍保留旧短名和提示词文件名兼容。新调用必须传提示词正文与 `provider` / `api_key_env` / `model_name` / `base_url`。工具在创建之后由调用方挂载。`engines/` 不得查库。

用量记录按角色名绑定密钥环境变量名，逐次记录里没有模型名。任务收尾用执行者模型名给整单 token 计价。

## Goals / Non-Goals

**Goals:**

- 工作流记录只存两个名片编号，运行时现解析。
- 新装配函数复用 `create_agent` 与 `select_tools`，编排仍走 `run_sop`。
- 新任务类型与控制设备任务分开收尾，双模型费用只落在新类型上。

**Non-Goals:**

- 不替换 `device_control`，不改 `ui_task.yaml`，不重写 `sop-task-run`。
- 不让 YAML 指定角色，不支持每步换人。
- 不把 SOP 放进助手对话页，不冻结 snapshot。
- 不把设备序列号做成必填。
- 不做工作流复制、排序、归档或启用/停用；删除是物理删除。

## Decisions

**D1：工作流表放在 `ai_assistant`，运行记录仍用 `task_list.Task`。**

工作流是名片的组合，不是一次执行。放 `ai_assistants` 旁边，写库走 `ai_assistant.api`。一次运行仍是任务：`TaskKind` 增加 `assistant_sop`，附件存里程碑 YAML，执行链仍由 `task_runner` 拉起。

备选：把绑定字段直接加到 `Task`。拒绝，因为同一条工作流要能多次运行，绑定不应随某次附件变化。

**D2：解析留在后端，引擎只收绑定参数。**

`ai_assistant.api` 提供只读解析：输入两个 `assistant_id`，输出两侧的运行名、提示词正文、连接参数、工具勾选。名片或 `AIRole` 缺失时抛明确错误，由任务收尾写成失败。`backend_bridge` 新函数只收这些参数，调用 `create_agent` 两次，再分别挂工具。不得 import `backend.apps` 或 `django`。

运行名用名片显示名。两侧显示名相同时，在其中一侧追加 `assistant_id`，保证用量按角色名归组时不会叠成一条。

**D3：验收工具在装配时取交集，不改名片勾选。**

执行侧调用现有 `select_tools`。验收侧先按只读预设取出目录，再与名片勾选的函数名取交集。交集为空时仍创建验收角色，只是没有工具。未知名字沿用 `select_tools` 的拒绝语义。

备选：创建时改写验收名片的勾选。拒绝，因为活绑定要求名片本身不被工作流改写。

**D4：里程碑 YAML 复用 `load_spec`，上传校验单独做。**

文件格式已经是 `name` / `steps[]` / `subject` / `description` / `max_attempts`。新入口把上传正文写成临时文件后调用 `load_spec`。用例格式在交给 `load_spec` 之前拒绝，避免被当成缺字段的里程碑而报错含糊。YAML 中多出来的角色字段不读取。

`load_spec` 不增加角色段。角色不进步骤文件，是已定口径。

**D5：新装配函数与 `build_sop_roles` 并列，不改旧函数。**

旧函数继续服务 `run_sop_once`。新函数不传 `model_short`，不传提示词文件名。一次运行新建一对实例，跑完即弃。取消、观测、报告目录沿用 `backend_bridge` 现有中间件与 `REPORT_ROOT`。

**D6：费用按次计价只加在新任务收尾。**

逐次用量需要带上模型名。记录层按角色名绑定密钥的方式保留；新增「角色名 → 模型名」绑定，在每次模型调用结束时写入该次记录。新任务收尾按该模型名调用现有价目函数，再相加。模型名缺失的该次记 0，并在结果里留可读说明。

`device_control` 的 `_price_costs` 仍把整单交给一个模型名。不改那条函数的入参语义。

价目本身不改：仍只登记 `deepseek-flash` 与 `deepseek-v4-pro`，其它模型名按既有规格返回 0。

**D7：设备可选，不生成空 serial 开场。**

新入口不调用「设备为空则拒绝」的提交校验。提供了 serial 时，才把现有开场模板追加到 `spec.task`。未提供时，`spec.task` 只用 YAML 的 `task`，缺省则用流程名。

**D8：两张卡同在一个组件文件里，视觉各自成立；页面按助手在上、工作流在下分区，中间一条分区虚线。**

线型白名单按**文件**判定，把虚线抄进新组件会被门禁拦住。所以工作流便签卡与助手颜料片同放 `AssistantCard.vue`，由 `item.kind` 分支：

- 助手形体：纸底 + 2.5px 墨色虚线框 + 笔色硬影 + 图钉 + 头像或笔色圆，居中。
- 工作流形体（Tape Strip，参考 StyleKit Hand-Drawn Doodle → Notebook Artifacts）：白卡 + 1.5px 浅墨虚线框 + 顶部半透明笔色胶带，左对齐，静止无影；底部一排是「配置 / 任务」两枚文字按钮站在色块位置，右侧一块纯色占位块（无交互）。

两区块之间用 `SectionDivider`（1.5px 浅墨虚线）分隔，并把它登记为虚线白名单的第 6 个落点；两块间距由 24px 抬到 40px。胶带颜色取该工作流**执行助手**的 `marker`（执行助手不存在回落 teal），用同一支笔色的 `color-mix(..., transparent)` 做上浓下淡的半透明渐变，不写死颜色。

备选：新建 `WorkflowCard.vue` 并登记进白名单。拒绝，因为同一套「卡上虚线」会有两份声明，改一处要改两处。

备选：给胶带换成某个固定蓝色。拒绝，因为卡片是「一卡一色」，胶带必须跟着这张卡的笔色走。

**D9：编辑整幅回写三字段，删除只删记录。**

`PATCH` 与 `POST` 共用 `SopWorkflowInputSerializer` 与 `prepare_workflow`：名称非空、两侧名片存在、两侧可为同一张。校验失败时不保存任何字段（先算完字段字典再赋值），不留下半改记录。

`DELETE` 只删工作流行：名片、Agent 配置与历史任务都不动。历史任务把 `workflow_id` 记在自己的 `result` JSON 里，不是外键，所以删工作流不影响已提交任务的详情；该任务如果再被重跑，会因为解析不到工作流而失败，这是预期。

备选：软删（加 `is_active`）让旧任务仍能重跑。拒绝，因为本变更没有「工作流停用」的语义，多一列会让「列表」与「解析」都要判断状态。

**D10：运行弹窗只带工作流编号、YAML 与可选设备地址。**

工作流由卡片带入，弹窗不再出现「已有 SOP」下拉，也不让用户改标题（标题用工作流名）。提交字段与既有 `POST /tasks/submit/` 完全一致，后端不为弹窗新增入参。提交成功后关闭弹窗并提示任务编号，YAML 与设备选择清空。

设备不手填：下拉的选项来自设备管理（`GET /api/devices/`），取值口径与新建任务完全一致（USB 出序列号、局域网出 `IP:端口`、无线调试别名记录不列）。这套地址口径抽到 `shared/helpers/device-address.ts`，任务清单与助手页共用一份，避免「同一个设备在两个入口提交出两种地址」。设备仍是可选项：空选项默认选中，取不到设备列表时只提示、不拦提交。

备选：在助手模块里再写一份 `IP:port` 判断。拒绝，因为这会把「什么地址能连上」变成两处规则，迟早漂移。

## 模块防火墙自检

- `task_list` 只通过 `ai_assistant.api` 解析名片，不 import 其 service / views。
- 工作流的增删改只写在 `ai_assistant.api`。任务的创建、附件与终态只写在 `task_list.api`。
- `backend_bridge` 不 import `backend.apps` 或 `django`。名片解析不放进 `engines/`。
- `ae_harness` 不新增创建入口，不读工作流表，不读提示词文件。
- 前端只调 HTTP。不直连数据库，仪表盘不因本变更增加写操作。
- 新跨模块依赖只有一条：`task_list` → `ai_assistant.api` 的只读解析。不能把解析放进 `task_list`，否则会复制名片与 Agent 配置的读取规则。
- 工作流卡的编辑与删除都只经 `ai_assistant.api`，前端不直连 ORM；删除不触碰名片与任务表。

## Risks / Trade-offs

- [活绑定让同一次重跑与上次结果不同] → 接受。详情保留本次实际使用的两个 `assistant_id` 与运行名，不回写名片。
- [报告仍按每步两次回复区分执行者与验收者] → 一期不换人，顺序不变。若以后每步换人，先改报告推断，不在本期做。
- [验收勾选与只读目录交集为空] → 允许启动。验收者仍能根据步骤说明与执行者交付给出判决；需要看设备时，用户应在验收名片上勾选只读工具。
- [用量记录增加模型名字段] → 只追加字段。旧 JSONL 没有该字段时，控制设备任务不读它。
- [AgentScope SOP 仍是实验接口] → 不封装第二套循环。升级时只复核 `SOPStep.reply_stream` 的先执行后验收顺序。

## Migration Plan

1. 加工作流表与 `assistant_sop` 任务类型。旧任务行的 `task_kind` 不变。
2. 新入口与新装配先落库函数和单测，不改 `run_sop_once`。
3. 用量记录追加模型名后，只让新任务收尾读取。
4. 工作流编辑/删除接口与前端分区卡片最后落地：先加接口与单测，再把页内表单换成卡片与两个弹窗。
5. 回退：停用新入口与新任务类型；工作流表可保留空数据。前端回退到页内表单时，`PATCH` / `DELETE` 接口可先留着不调用。`device_control` 的装配、YAML 校验与整单计价不参与本次改动，无需数据回写。

## Open Questions

无。角色引用、绑定位置、YAML 格式、新入口、一对角色、工具来源、活绑定、费用口径与设备非必填均已确认。
