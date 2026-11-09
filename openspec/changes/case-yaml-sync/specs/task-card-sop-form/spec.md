## ADDED Requirements

### Requirement: 新建任务弹窗按用例来源提交

新建任务弹窗 SHALL 包含：任务标题、智能体、用例来源、设备四项固定字段，以及随用例来源切换的用例输入区。用例来源 MUST 为单选，取值 `平台用例` 或 `本地 YAML`，默认 MUST 为 `平台用例`。来源为 `平台用例` 时，弹窗 MUST 提供「项目 → 用例文件 → 用例」的选择器（用例可多选），且 MUST NOT 要求上传 YAML；来源为 `本地 YAML` 时，弹窗 MUST 提供一份 YAML 与「测试指定用例」下拉，且 MUST NOT 要求选择平台用例。切换用例来源时 MUST 清空另一来源已做的选择，提交 MUST 只带当前来源的用例输入。任务标题、智能体、设备 MUST 为必填；平台用例来源 MUST 至少选中 1 条用例，本地 YAML 来源 MUST 已选择一份 YAML。字段缺失时提交按钮 MUST 置灰或被拒绝并说明缺少哪一项。

#### Scenario: 平台用例来源不要求上传 YAML

- **WHEN** 用户把用例来源选为「平台用例」
- **THEN** 弹窗出现项目、用例文件与用例选择器
- **AND** 不出现 YAML 上传入口，也不要求选择测试指定用例

#### Scenario: 本地 YAML 来源不要求选择平台用例

- **WHEN** 用户把用例来源选为「本地 YAML」
- **THEN** 弹窗出现 YAML 上传与测试指定用例下拉
- **AND** 不要求选择平台用例

#### Scenario: 切换来源清空另一侧选择

- **WHEN** 用户先选了 3 条平台用例，随后把来源切到「本地 YAML」
- **THEN** 已选的平台用例被清空
- **AND** 切回「平台用例」时选择器为空，不保留此前的勾选

#### Scenario: 未选用例时不能提交

- **WHEN** 用户填好标题、智能体与设备，但平台用例来源下未选中任何用例
- **THEN** 提交按钮置灰，或提交被拒绝并提示需要选用例

### Requirement: 弹窗提交载荷按用例来源区分

提交时前端 MUST 以 multipart 发送 `title`、`agent_id`、`device_serial`、`device_label` 与 `case_source`（`platform` 或 `yaml`）。来源为 `platform` 时 MUST 额外发送 `case_ids`（JSON 数组字符串），MUST NOT 发送 `config` 文件与 `case_title`。来源为 `yaml` 时 MUST 额外发送 `config` 文件与可为空的 `case_title`，MUST NOT 发送 `case_ids`。两种来源 MUST NOT 发送 `goal`、`documents`、`assistant_route`。设备下拉 MUST 展示可连地址（有型号时附带型号）。选中 USB 设备时 `device_serial` MUST 为该 USB 序列号；选中局域网设备时 `device_serial` MUST 为 `IP:端口`；提交值 MUST NOT 是从 `_adb-tls-connect._tcp` 别名拆出的硬件序列号。

#### Scenario: 平台用例来源的提交字段

- **WHEN** 用户选择 2 条平台用例、设备与智能体后提交
- **THEN** 请求体含 title、agent_id、device_serial、case_source=platform 与 case_ids 数组
- **AND** 请求体不含 config 文件与 case_title

#### Scenario: 本地 YAML 来源的提交字段

- **WHEN** 用户上传 YAML、选择「全部用例」后提交
- **THEN** 请求体含 title、agent_id、device_serial、case_source=yaml、case_title 空串与 config 文件
- **AND** 请求体不含 case_ids

#### Scenario: USB 设备提交序列号

- **WHEN** 用户选择地址为 `R5CT62RH88F` 的设备并提交
- **THEN** 请求中的 device_serial 为 `R5CT62RH88F`

#### Scenario: 局域网设备提交 IP 与端口

- **WHEN** 用户选择地址为 `192.168.35.57:39569` 的设备并提交
- **THEN** 请求中的 device_serial 为 `192.168.35.57:39569`

### Requirement: 平台用例来源由后端物化为执行 YAML

来源为 `platform` 时，平台 SHALL 把 `case_ids` 对应的用例按选择顺序物化为一份可执行 YAML，并以配置附件形式随任务保存，执行链 MUST 继续使用既有 SOP 入口，MUST NOT 为平台用例新开执行分支。物化前 MUST 校验：至少 1 条用例、全部用例存在且属于当前用户、物化文本通过平台 YAML 校验。任一条不满足时 MUST 拒绝提交并返回可读原因，MUST NOT 创建任务。任务详情 MUST 能读回该配置附件正文，供排障与重跑。

#### Scenario: 平台用例任务生成配置附件

- **WHEN** 用户提交含 2 条平台用例的任务
- **THEN** 任务存在一份配置附件，正文为这 2 条用例组成的 YAML
- **AND** 任务按既有 SOP 入口启动

#### Scenario: 用例不属于当前用户时拒绝

- **WHEN** 提交的 `case_ids` 中包含他人项目下的用例
- **THEN** 接口拒绝提交并说明用例不存在或无权限
- **AND** MUST NOT 创建任务

#### Scenario: 重跑沿用同一份物化 YAML

- **WHEN** 平台用例来源的任务失败后被重跑
- **THEN** 新任务复制原任务的配置附件正文
- **AND** 新任务的执行输入与原任务一致

## MODIFIED Requirements

### Requirement: 智能体单选且必选

智能体下拉 SHALL 为单选，选项 MUST 来自平台当前支持的流程；当前 MUST 只有 `sop` 一个选项。未选择智能体时提交按钮 MUST 置灰。用户选择某个流程后，弹窗 MUST 展示该流程对应的参数组；当前 `sop` 的参数组即用例来源及其对应的用例输入（平台用例或本地 YAML）、设备。系统 MUST NOT 允许同时选择多个智能体。

#### Scenario: 未选智能体不能提交

- **WHEN** 用户没有选择智能体
- **THEN** 提交按钮置灰，无法提交

#### Scenario: 选择 sop 后出现 SOP 参数

- **WHEN** 用户选择当前唯一可用的 `sop` 流程（Agent-01）
- **THEN** 弹窗展示用例来源、对应的用例输入与设备

#### Scenario: 不允许复选

- **WHEN** 用户操作智能体下拉
- **THEN** 只能选中一个选项，无法多选

## REMOVED Requirements

### Requirement: 新建任务弹窗只提交 SOP 参数

**Reason**: 用例来源从「只有本地 YAML」扩展为「平台用例 / 本地 YAML」二选一，固定五项字段与「配置 YAML 必填」的描述已不成立。

**Migration**: 由新增需求「新建任务弹窗按用例来源提交」取代；本地 YAML 路径与既有校验保持不变。

### Requirement: 弹窗提交载荷固定

**Reason**: 提交载荷不再是单一固定集合，而是按 `case_source` 分支（平台用例带 `case_ids`、本地 YAML 带 `config`）。

**Migration**: 由新增需求「弹窗提交载荷按用例来源区分」取代；`title` / `agent_id` / `device_serial` / `case_title` / `config` 字段名与语义保持兼容。
