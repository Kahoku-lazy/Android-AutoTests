## REMOVED Requirements

### Requirement: 任务卡片提交
**Reason**: 卡片改为 SOP 参数表单，任务目标与文档不再参与执行；提交字段改为标题、智能体、YAML、设备、用例。
**Migration**: 旧客户端仍可提交 `title/goal/config/documents/device_serial`，后端保留字段但不把目标与文档拼进执行开场；新前端按新契约提交。

### Requirement: 新建任务必须填写独立标题
**Reason**: 被「新建任务必须填写标题并可选指定用例」整体替换，标题仍必填，但不再与任务目标成对落库。
**Migration**: 标题字段不变；旧任务的 `goal` 保留在库中仅供历史查看。

### Requirement: 新建任务选择平台小助手上的助手
**Reason**: 智能体改为独立必选项并提交 `agent_id`，不再只提交线路键 `assistant_route`。
**Migration**: 旧请求仍带 `assistant_route` 时按当前平台智能体处理；新前端提交 `agent_id`。

### Requirement: 任务附件分为配置与文档
**Reason**: 新卡片只保留一份 YAML，文档附件入口移除；执行开场也不再拼接文档正文。
**Migration**: 历史任务的文档附件仍保留可查看；新提交只落一份 YAML。

## ADDED Requirements

### Requirement: 任务卡片提交 SOP 参数

系统 SHALL 允许用户从任务卡片提交一条控制设备任务。提交表单 MUST 包含任务标题、智能体、配置 YAML 与设备；测试指定用例 MUST 可选。任务标题与设备 MUST 非空；`agent_id` MUST 指向平台当前支持的智能体；配置 MUST 恰好一份 YAML。设备不再允许留空回退到第一台在线设备。

#### Scenario: 提交一条 SOP 任务

- **WHEN** 用户填写任务标题、选择智能体、上传一份合法 YAML、选择一台设备并可选地选择一条用例后提交
- **THEN** 系统创建任务记录，保存标题、智能体、设备、用例与 YAML 正文，并进入按设备调度的执行流程

#### Scenario: 缺少设备时拒绝提交

- **WHEN** 用户没有选择设备即提交
- **THEN** 系统拒绝创建任务并提示设备为必填，不再自动绑定第一台在线设备

#### Scenario: 缺少智能体时拒绝提交

- **WHEN** 请求中没有合法的 `agent_id`
- **THEN** 系统拒绝创建任务并提示需要选择智能体

#### Scenario: 缺少 YAML 时拒绝提交

- **WHEN** 请求中没有 YAML 或带了多份 YAML
- **THEN** 系统拒绝创建任务并说明需要恰好一份 YAML 配置

### Requirement: 新建任务必须填写标题并可选指定用例

系统 SHALL 在任务提交表单中提供独立的「任务标题」字段，标题 MUST 非空。表单 SHALL 提供「测试指定用例」字段，取值 MUST 为空串（全部用例）或 YAML 中的某个用例标题。任务记录 MUST 同时保存标题与 `case_title`。

#### Scenario: 标题与用例分别落库

- **WHEN** 用户填写标题「校准色温」、选择用例「甲」后提交成功
- **THEN** 任务记录的标题为「校准色温」，`case_title` 为「甲」

#### Scenario: 标题缺失拒绝提交

- **WHEN** 用户未填写任务标题即提交
- **THEN** 系统拒绝创建任务并提示标题为必填

### Requirement: 新建任务必须选择智能体

系统 SHALL 在新建任务弹窗提供单选智能体下拉。选项 MUST 与平台当前支持的流程一致；当前 MUST 只有 `sop` 一个选项。用户未选择智能体时 MUST 不允许提交。提交 MUST 带上该智能体的 id，后端 MUST 校验该 id 存在且其控制设备线路的执行与验收模型齐全。

#### Scenario: 单选智能体后提交

- **WHEN** 用户选择当前唯一的 `sop` 智能体并提交
- **THEN** 请求带上该智能体的 id，后端按该智能体装配执行与验收模型

#### Scenario: 智能体未选时不能提交

- **WHEN** 用户打开弹窗但未选择智能体
- **THEN** 提交按钮置灰，请求不会发出

#### Scenario: 智能体未登记时拒绝提交

- **WHEN** 请求中的 `agent_id` 不存在，或对应智能体缺少执行 / 验收模型
- **THEN** 系统拒绝创建任务并返回可读原因

### Requirement: 新建任务只需一份 YAML 配置

系统 SHALL 在新建任务中只提供配置类附件，且 MUST 只接受一份 YAML（`.yaml` / `.yml`，UTF-8）。csv 与 json MUST 被拒绝。系统 MUST 在提交时检查扩展名与 YAML 结构；检查不通过时 MUST 拒绝创建任务并返回可读原因。文档类附件入口 MUST NOT 出现在新弹窗中。

#### Scenario: 一份 YAML 可以提交

- **WHEN** 用户附上一份合法 YAML 后提交
- **THEN** 系统创建任务并保留该 YAML 正文

#### Scenario: 两份 YAML 被拒绝

- **WHEN** 请求带上两份 YAML
- **THEN** 系统拒绝创建任务并说明只能有一份配置

#### Scenario: 不再接受文档附件

- **WHEN** 用户查看新建任务弹窗
- **THEN** 弹窗中没有文档上传入口
