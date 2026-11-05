## REMOVED Requirements

### Requirement: 用例编写角色按需求原子产出完整用例文档

**Reason**: 产物由「七节 Markdown + 13 字段用例表」换成三段式结构化数据（状态机 → 业务流场景 → 用例），文档改为渲染派生物；五阶段工作流与 13 字段契约随之作废。

**Migration**: 改用本 delta ADDED 的三条编写要求（状态机、场景枚举、边界与场景法用例）。历史任务结果与用例库中的存量用例按 legacy 保留，不回填。

### Requirement: 用例验收角色独立判卷

**Reason**: 判卷口径从 A–H 八组清单收窄为两条事实判断（数据是否与需求一致、是否捏造），旧清单中的覆盖率、方法数、优先级比例、字段完整性不再是验收项。

**Migration**: 改用「用例验收角色只判数据一致与捏造」；验收模型仍独立于编写模型，仍只看产物与需求正文。

### Requirement: 编写与验收成对运行

**Reason**: 编排从「双轨（SOP / 目标流水线）+ 模块循环」收敛为一条目标流水线，执行者只构建一次，不再按模块逐份运行。

**Migration**: 改用「编写与验收走单一目标流水线」。

### Requirement: 需求按模块切分

**Reason**: 编写角色改为通过增量工具分次交付，单次输出长度天然有界；不再需要按行号切模块，也不再需要独立的模块规划角色。

**Migration**: 大需求由编写角色在同一轮流水线内分多个批次追加场景与用例完成，删除模块规划角色与确定性回退切块。

### Requirement: 输出截断检测与拆分

**Reason**: 产物不再是一次生成的整篇长文档，单次工具调用超限时由工具报错并要求重试该批次，不需要按 token 上限判定截断、也不需要把模块递归二分。

**Migration**: 单批追加超过上限时工具 MUST 报错且不写入半份数据；编写角色拆成更小批次重试。

### Requirement: 模块化结果拼装

**Reason**: 交付物是结构化产物，Markdown 由平台按产物渲染；不再有「按模块拼接多份七节文档」。

**Migration**: `Task.result` 用 `artifact` 承载三段产物，`document` 承载渲染后的 Markdown，`modules` 字段移除。

### Requirement: 模块文档存储

**Reason**: 存储对象从「整篇 Markdown」改为「三段结构化产物的增量片段」，读写接口与校验方式都变了。

**Migration**: 改用「三段式产物增量交付与存储」；`save_case_module_document` / `read_case_module_document` 不再提供。

### Requirement: 确定性校验

**Reason**: 旧校验（七节齐全、ID 唯一、13 字段、方法数、P0 比例、E2E 条数、覆盖率、模糊词）整条删除，换成只核对事实的预检。

**Migration**: 改用「事实预检」；覆盖率类指标降为告警且在报告可见，不阻断通过。

### Requirement: 编写角色用计划模式跟踪五阶段

**Reason**: 五阶段被三段式取代，交付边界由产物工具承担，计划清单不再具有工程约束力。

**Migration**: 编写角色与验收角色都不再装配 `TaskCreate` / `TaskGet` / `TaskList` / `TaskUpdate`。

## ADDED Requirements

### Requirement: 编写角色产出需求状态机

编写角色 MUST 在写场景与用例之前先产出需求状态机，由 `states` 与 `transitions` 两部分组成，每项 MUST 带 `source`（需求原文片段）。状态 MUST 是可被截图或日志区分的最小页面/模式，MUST NOT 把每个弹窗拆成状态，MUST NOT 用一个状态概括多个页面。需求没有写明的状态或迁移 MUST NOT 编造。

#### Scenario: 需求给出明确的模式切换

- **WHEN** 需求写「点击场景模式后进入场景页，可切换 Nature / Festival 标签」
- **THEN** 状态机含「详情页」与「场景页」两个状态，含一条 `详情页 --点击场景模式--> 场景页` 的迁移
- **AND** 三个 `source` 都能在需求原文中找到

#### Scenario: 状态必须声明可观察性

- **WHEN** 某状态只能通过设备灯光或内部计数判断
- **THEN** 该状态 `observable=false` 且 `observe_by` 写明原因
- **AND** 任何用例 MUST NOT 把它写成 `expect_state`

#### Scenario: 需求没写的状态不造

- **WHEN** 需求未提及加载态，而实际页面有加载圈
- **THEN** 编写角色 MUST NOT 把它写成状态
- **AND** 若必须区分，MUST 登记到「待确认」并标 `uncertain=true`

### Requirement: 编写角色由状态机路径枚举业务流场景

编写角色 MUST 以状态机迁移路径为唯一来源枚举场景，每个场景 MUST 含 `id`、`title`、`path`（状态序列，长度 ≥2）、`transitions`、`type`、`source`。`type` MUST 取 `主流程` / `异常` / `回退` / `中断恢复` / `并发` 之一。`异常` 与 `回退` MUST 从 `guard` 与需求写明的失败分支派生，MUST NOT 凭空设计需求里没有的分支。

#### Scenario: 主流程场景

- **WHEN** 需求写「打开详情页 → 进入场景页 → 选择灯效 → 应用」
- **THEN** 产出一条 `主流程` 场景，`path` 为四个状态的序列
- **AND** `transitions` 列出走过的四条迁移 id

#### Scenario: 异常分支必须有出处

- **WHEN** 需求写明「配网超时后回到待配网」
- **THEN** 产出一条 `异常` 场景覆盖该分支，`source` 指向这句原文

#### Scenario: 需求没写的异常不造

- **WHEN** 需求没有提到断网、断电、多设备并发
- **THEN** 编写角色 MUST NOT 产出对应场景，需要时 MUST 登记到「待确认」

### Requirement: 编写角色用边界与场景法编写用例

每条用例 MUST 从某个场景派生，含 `id`、`title`、`scenario_id`、`pre_state`、`steps`、`boundary`、`method`、`priority`、`source`。`steps` MUST 是「动作 → 期望状态」序列，`expect_state` MUST 是可观察状态，首步 MUST 对齐场景起点，末步 MUST 落在场景终态。`method` MUST 至少含 `场景法`；覆盖到阈值、上限、下限、时长、字符数的用例 MUST 给出至少一项 `boundary`，且同时包含边界内与边界外。需求未给出上限时 MUST NOT 猜数值。

#### Scenario: 场景法主用例

- **WHEN** 场景 SC-001 是「详情页 → 场景页 → 选择灯效」
- **THEN** 至少产出一条用例，`scenario_id=SC-001`，`method` 含 `场景法`
- **AND** 每步 `expect_state` 都是已声明的可观察状态

#### Scenario: 边界取值带出处

- **WHEN** 需求写「名称最多 22 个字符」
- **THEN** 产出边界项 `{param: "名称长度", values: ["22", "23"], source: "名称最多 22 个字符"}`
- **AND** 该用例覆盖 22 与 23 两种取值

#### Scenario: 上限未给出不猜

- **WHEN** 需求只写「名称长度有限制」而没给数字
- **THEN** 编写角色 MUST NOT 写出具体字符数
- **AND** 该参数 MUST 登记到「待确认」，相关用例 `uncertain=true`

### Requirement: 三段式产物增量交付与存储

系统 SHALL 提供任务级产物存储与增量写入工具：`save_state_machine`、`append_scenarios`、`append_cases`、`read_artifact`。写入工具 MUST 校验结构与必填字段，不合法时 MUST 返回可读错误且 MUST NOT 写入半份数据；单批 MUST 有大小上限，超限 MUST 报错，MUST NOT 静默截断。同 id 再写一次 MUST 原位覆盖（供驳回后定点修改），MUST NOT 产生重复条目。工具返回 MUST 只回「本次条数与累计条数」，MUST NOT 回显内容。产物 MUST 以结构化数据保存，MUST NOT 只存整篇 Markdown。

#### Scenario: 驳回后按 id 定点修正

- **WHEN** 验证者点名用例 `TC-001` 的某一步数值无出处
- **THEN** 编写角色用同一 id 重新 `append_cases` 一条修正版
- **AND** 该用例被原位替换，产物里不出现两条 `TC-001`

#### Scenario: 分批追加

- **WHEN** 编写角色分 3 次调用 `append_cases`，每次 10 条
- **THEN** 存储里累计 30 条，每次返回「已追加 10 条，累计 10/20/30 条」

#### Scenario: 非法数据不落库

- **WHEN** 某次 `append_cases` 中有一条用例缺少 `scenario_id`
- **THEN** 工具返回可读错误并指出第几条缺哪个字段
- **AND** 该批 MUST NOT 部分写入

#### Scenario: 验收读实文

- **WHEN** 验收角色判卷
- **THEN** 它通过 `read_artifact` 读到实际用例与其 `source`
- **AND** MUST NOT 以 `report` 摘要作为判卷依据

### Requirement: 三段式产物渲染

平台 MUST 从结构化产物确定性渲染 Markdown 文档与 Mermaid `stateDiagram-v2` 状态图，MUST NOT 让模型另外写一份。Markdown MUST 依次含状态机摘要、场景表、用例表，结果写入 `Task.result.document`；Mermaid 写入 `Task.result.artifact.diagram`。产物与渲染结果不一致时 MUST 以产物为准并重新渲染。

#### Scenario: 渲染三节

- **WHEN** 产物含 8 个状态、12 条迁移、6 条场景、30 条用例
- **THEN** `document` 依次含状态机摘要、场景表（6 行）、用例表（30 行）
- **AND** `diagram` 能画出 12 条迁移

#### Scenario: 渲染是派生的

- **WHEN** 有人手工改了 `document` 文本
- **THEN** 平台以产物重新渲染并覆盖该改动
- **AND** `document` MUST NOT 被当作产物来源

### Requirement: 用例验收角色只判数据一致与捏造

验收角色 SHALL 只判两件事：用例数据是否与需求正文一致、是否存在自推测或捏造。判定 MUST 只依据需求正文、结构化产物与事实预检结论，MUST NOT 采信编写角色的自述，MUST NOT 评价需求本身，MUST NOT 以覆盖率、方法数、优先级比例、字段完整性或文档结构驳回。`result` MUST 为 `pass` / `fail`，`message` 在 `fail` 时 MUST 给出「用例编号 + 原文出处」，在 `pass` 时 MUST 写清核对过的用例条数与剩余待确认项。

#### Scenario: 用例数值在需求里找不到

- **WHEN** 某条用例写「亮度调到 85%」，而该条 `source` 与需求正文都没有出现 85
- **THEN** 事实预检返回确定性问题
- **AND** 验收角色判 `fail`，`message` 点名该用例与「需求未给出该数值」

#### Scenario: 全部数据可追溯

- **WHEN** 所有 `source` 都能在需求原文中找到，且引用的状态与场景均已声明
- **THEN** 验收角色 MUST NOT 以「覆盖率不足」「字段不全」为由驳回
- **AND** 判 `pass`，`message` 写清核对的用例条数与剩余待确认项

#### Scenario: 验收不越界

- **WHEN** 状态机只覆盖需求的一部分功能，但已产出的用例数据全部与原文一致
- **THEN** 验收角色 MUST NOT 因「状态机不完整」判 fail
- **AND** 只在 `message` 里提示未覆盖的功能名供人判断

### Requirement: 编写与验收走单一目标流水线

引擎 SHALL 用一条目标流水线（GoalPipeline）跑编写与验收：执行者为编写角色、验证者为验收角色，验证者每轮重开上下文，最多 3 轮驳回，单轮结构化输出最多重问 3 次。系统 MUST NOT 再提供 SOP 与目标流水线两条并行路径，MUST NOT 引入第三个角色。执行者 MUST 通过增量工具写入产物，并在结束前用 `report` 给出摘要；验证者 MUST 先取事实预检再判卷。任一轮 `pass` 即整轮 `completed`，3 轮仍 `fail` 或连续 3 次无合法结构化输出时 MUST 判 `failed` 并保留最后产物与全部判决。

#### Scenario: 首轮通过

- **WHEN** 编写角色第一轮写入完整三段产物，验证者取预检后判 `pass`
- **THEN** 任务结果为 `completed`，含产物、预检结论与一条判决

#### Scenario: 驳回后定点补写

- **WHEN** 验证者判 `fail` 并点名三条用例的数值与原文不符
- **THEN** 同一执行者保留自身上下文并收到驳回原文，只修改这三条后重新交付
- **AND** 引擎 MUST NOT 把上一版产物全文重新拼进输入

#### Scenario: 三轮未通过

- **WHEN** 第三轮验证仍判 `fail`
- **THEN** 整轮判 `failed`，结果保留最后一次产物、预检结论与三轮判决

#### Scenario: 结构化输出持续失败

- **WHEN** 执行者连续 3 次没有给出符合 schema 的结构化输出
- **THEN** 整轮判 `failed`，`reason` 写明「未产出合法结构化输出」

### Requirement: 事实预检

平台 MUST 在每轮验证前用代码核对三类事实：每个状态/迁移/场景/用例的 `source` 归一空白后是需求正文子串；用例的 `pre_state`/`expect_state`/`scenario_id` 与迁移的 `from`/`to` 均已声明；用例与边界项中的数值出现在其自身 `source` 或某条边界 `source` 里。预检 MUST 以只读工具提供给验收角色，并在任务结果保留 `blocking` 与 `warnings`。存在确定性问题时该轮 MUST NOT 判为通过；覆盖率类指标 MUST 只进 `warnings`。

#### Scenario: source 不是原文

- **WHEN** 某条迁移 `source` 写「支持 16 万色」，而需求原文是「1600 万色」
- **THEN** 预检返回「出处不在需求原文中」并附最接近的原文片段
- **AND** 该轮不得判为通过

#### Scenario: 数值捏造

- **WHEN** 某条用例步骤里出现「3 秒内」，而该用例 source 与边界项都没有出现 3
- **THEN** 预检返回数值不可追溯
- **AND** 该轮不得判为通过

#### Scenario: 覆盖率不足只告警

- **WHEN** 状态机有 12 条迁移，场景只走了 9 条
- **THEN** 预检把 3 条未覆盖迁移列入 `warnings`
- **AND** MUST NOT 因此判该轮失败
