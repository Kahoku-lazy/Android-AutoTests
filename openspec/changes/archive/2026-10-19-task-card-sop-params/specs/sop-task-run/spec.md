## REMOVED Requirements

### Requirement: 开场说明由任务目标与设备组成
**Reason**: 新卡片不再提交任务目标与文档，执行开场改为设备序列号的固定模板。
**Migration**: 旧任务的 goal / 文档仍留在库中，但不再拼进执行开场；新任务按固定模板生成。

## ADDED Requirements

### Requirement: 开场说明由设备序列号组成

系统 SHALL 用固定模板生成执行开场说明，只交给第一条用例的第一步：

`本次要操作的设备 serial 是：{device_serial}。每一步的设备动作都必须带上它。`

开场说明 MUST 只由设备序列号决定，MUST NOT 读取任务目标、文档附件或 YAML 正文。设备序列号为空时系统 MUST 在提交阶段拒绝创建任务，MUST NOT 用空串生成开场。

#### Scenario: 设备序列号进入开场

- **WHEN** 任务设备序列号为 `R5CT62RH88F`
- **THEN** 第一步收到的开场说明为「本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。」

#### Scenario: 开场不拼目标与文档

- **WHEN** 历史任务带有任务目标或文档附件
- **THEN** 执行开场仍只有设备序列号那一句，不追加目标或文档正文

#### Scenario: 设备为空不生成任务

- **WHEN** 提交时设备序列号为空
- **THEN** 系统拒绝创建任务，不进入执行

## MODIFIED Requirements

### Requirement: 同一 YAML 的多条用例按文件顺序跑完

一次任务 MUST 按 YAML 中的用例顺序依次执行。任务指定了 `case_title` 时 MUST 只执行标题完全匹配的那一条用例，其余用例 MUST NOT 执行；`case_title` 为空时 MUST 执行全部用例。后一条用例 MUST NOT 复用前一条的角色对话。选择哪条用例 MUST 由 `case_title` 决定，MUST NOT 用任务标题或任务目标去匹配。指定的 `case_title` 在 YAML 中不存在时，系统 MUST 让任务以可读原因失败，MUST NOT 静默改为执行全部用例。某条用例失败时，系统 MUST NOT 开始排在它后面的用例。

#### Scenario: 两条用例依次执行

- **WHEN** YAML 中用例标题依次为「甲」和「乙」，`case_title` 为空，且「甲」完成
- **THEN** 系统先跑完「甲」，再跑「乙」

#### Scenario: 前一条失败则停止后续用例

- **WHEN** 「甲」未完成
- **THEN** 「乙」不会开始，任务状态为失败

#### Scenario: 指定用例只跑该条

- **WHEN** YAML 中用例标题依次为「甲」和「乙」，`case_title` 为「乙」
- **THEN** 系统只执行「乙」，不执行「甲」

#### Scenario: 指定用例不存在时失败

- **WHEN** `case_title` 为「丙」，但 YAML 中没有标题为「丙」的用例
- **THEN** 任务以可读原因失败，且不执行任何用例
