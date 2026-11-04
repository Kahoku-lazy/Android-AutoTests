## MODIFIED Requirements

### Requirement: Assembly uses the supplied roles

装配 MUST 使用调用方提供的角色工厂来构造每一步的角色：每推进一步 MUST 现建执行角色与验收角色实例，重试同一步 MUST 复用该步已建的那一对实例。跨步骤 MUST NOT 复用同一个执行者或验收者实例，也 MUST NOT 继承上一步的对话上下文。由于新实例没有历史，本次运行的开场输入（至少包含设备序列号）MUST 重放进**每一步**的执行者提示与验收者提示；MUST NOT 只交给第一步。装配 MUST NOT 替换角色的系统提示词、工具包或技能；实例的角色名与模型 MUST 由工厂决定，事件流与判决仍按角色名归集。角色工厂缺失或返回不可用对象时，装配 MUST 失败并说明是执行侧还是验收侧用不了。

#### Scenario: Started roles are bound to every step

- **WHEN** 执行角色工厂与验收角色工厂都能给出已启动的角色，并且步骤输入完整
- **THEN** 流程每一步都由该步现建的两个角色执行和验收，重试上限沿用本次装配给出的次数

#### Scenario: Instances are not shared across steps

- **WHEN** 一个含三步的流程开始运行
- **THEN** 三步各自持有不同的执行者与验收者实例，第二步开始时的上下文里没有任何第一步的对话内容

#### Scenario: Retry stays on the same instances

- **WHEN** 某一步第一次验收不通过、进入重试
- **THEN** 这次重试复用该步第一次开始时建的那一对实例，不重新构造角色

#### Scenario: Opening context reaches every step

- **WHEN** 本次运行的开场输入里给出了设备序列号
- **THEN** 每一步的执行者提示与验收者提示都含该序列号，第二步及之后的实例不必从历史里找它

#### Scenario: A role that has not started cannot be assembled

- **WHEN** 角色工厂缺失，或它给出的角色尚未启动
- **THEN** 装配失败，错误说明指向尚未启动的那个角色

## ADDED Requirements

### Requirement: Each step carries its own anchors and log evidence

步骤输入 SHALL 在「动作」与「要核对的结果」之外，允许携带两项可选的结构化补充：`anchor`（本步要去的页面、入口与目标元素）与 `log`（本步日志证据的型号、端口与关键词）。装载时 MUST 校验：`anchor` 只允许字符串键值且键名限于 `page` / `entry` / `target`；`log` 出现时 MUST 同时给出非空 `sku`、正整数 `port` 与至少一个非空关键词，关键词可以用 `keyword` 单个给出或 `keywords` 列表给出（最多 6 个，重复项表示该关键词要命中多次），两者 MUST NOT 同时出现；违反 MUST 拒绝装载并给出可读原因。注入时 MUST 只注入当前步：`anchor` MUST 只进入执行角色的步骤提示，`log` MUST 只进入验收角色的步骤提示；执行角色的提示 MUST NOT 出现 `log` 内容或该步要核对的结果，验收角色的提示 MUST NOT 出现 `action` 或 `anchor` 内容。缺少这两项时，该步的提示与既有行为完全一致。

#### Scenario: Anchors reach the executor only

- **WHEN** 某步给出 `anchor` 且没有 `log`，该步开始
- **THEN** 执行角色收到的提示里含页面与入口描述，且不含该步要核对的结果；验收角色收到的提示里不含页面与入口描述

#### Scenario: Log evidence reaches the verifier only

- **WHEN** 某步给出 `log`（`sku=H6810`、`port=7005`、`keyword=timer_configs_set_success`）
- **THEN** 验收角色收到的提示里含这三个字段，执行角色的提示里不含它们

#### Scenario: Multiple keywords are checked one by one

- **WHEN** 某步的 `log.keywords` 是 `[switch_on, lumi_set_success, lumi_set_success]`
- **THEN** 验收角色收到的提示按该顺序列出三个关键词，并写明「逐个查、同一关键词出现两次要命中两次、全部命中才算通过」

#### Scenario: A malformed log block is refused

- **WHEN** 某步给了 `log` 但缺 `keyword`，或 `port` 不是正整数
- **THEN** 装载失败并给出可读原因，不产生可运行流程

#### Scenario: Steps without the new fields keep working

- **WHEN** 用例的每一步都只有 `action` 与 `assert`
- **THEN** 装配与提示内容与本变更前一致，唯一差别是每步新建角色实例

### Requirement: Verifier steps carry the per-SKU log keyword catalog

验收角色的步骤提示 SHALL 带上该步型号的关键词目录（`功能点 → 关键词`），来源是 `engines/agents/config/data/log_keywords/<SKU>.md`，按 `log.sku` 选取。某步没有 `log.sku` 时，装配 MUST 用用例级型号（从用例标题识别，例如「H6810 定时功能测试」→ `H6810`）取同一份目录，MUST NOT 因为缺 `log` 就跳过注入；此时提示里 MUST NOT 出现具体关键词，只给目录让验收按功能点选。目录缺失或不可读时 MUST NOT 中断该步：提示里 MUST 明确写出「该型号关键词目录缺失」，并把判定退回「先截图核对页面」。目录存在时，其条目 MUST 只包含全量关键词目录里已登记的关键词；一个都不符时 MUST 视为目录损坏并按缺失处理，MUST NOT 把臆造的关键词交给验收角色。

#### Scenario: Catalog is attached to the step

- **WHEN** 某步 `log.sku` 为 `H6810`，且该型号目录存在
- **THEN** 验收角色收到的提示里含该型号的「功能点 → 关键词」条目

#### Scenario: Case-level SKU fills in for old steps

- **WHEN** 某步没有 `log`，但用例标题里有型号 `H6810`
- **THEN** 验收角色收到的提示里仍含 H6810 的关键词表，且不含具体关键词那一行

#### Scenario: Missing catalog degrades instead of failing

- **WHEN** 某步 `log.sku` 对应的目录不存在
- **THEN** 该步照常开始，验收角色提示里写明目录缺失并可退回截图核对，运行不因缺目录中断

#### Scenario: Unknown keywords are dropped

- **WHEN** 目录里出现全量关键词目录没有登记的关键词
- **THEN** 该条目不进入验收提示，其余条目照常注入

## REMOVED Requirements

### Requirement: Recent steps keep screenshots

**Reason**: 该需求假设所有步骤共用同一份跨步对话上下文，需要用「保留最近 3 步截图」来控制膨胀。改为每步新建角色实例后，跨步上下文不复存在，没有任何历史截图需要裁剪；而单步内部的图片上限继续由 `ContextConfig.max_image_num` 与上下文压缩承担。保留该需求会要求实现一套对空上下文做裁剪的逻辑，属于无对象的约束。

**Migration**: 不涉及数据迁移。装配改为每步新建实例后，删除依赖该需求的裁剪实现与断言（现存代码里没有独立的跨步裁剪实现，实际由框架的图片上限兜底）；如需临时回退到共享实例，恢复旧装配方式即可，该需求随旧装配方式一起恢复。
