## Purpose

把「新建任务」弹窗收敛成 SOP 参数表单：智能体单选且必选，选中的流程决定要填哪些参数；当前流程只有 `sop`，参数为一份 YAML、一台设备与可选的指定用例。用例下拉由前端直接解析 YAML 标题，提交时只带这五项。

## ADDED Requirements

### Requirement: 新建任务弹窗只提交 SOP 参数

新建任务弹窗 SHALL 只包含五个字段：任务标题、智能体、配置 YAML、设备、测试指定用例。弹窗 MUST NOT 再提供任务目标或文档附件入口。任务标题、智能体、配置 YAML、设备 MUST 为必填；测试指定用例 MUST 允许为空（空=跑 YAML 中的全部用例）。

#### Scenario: 五个字段齐备

- **WHEN** 用户打开新建任务弹窗
- **THEN** 只看到任务标题、智能体、配置 YAML、设备、测试指定用例五个字段，没有任务目标与文档上传

#### Scenario: 必填项缺失时不能提交

- **WHEN** 任务标题、智能体、配置 YAML、设备中任意一项为空
- **THEN** 提交按钮不可用，或提交被拒绝并提示缺少哪一项

#### Scenario: 用例允许不选

- **WHEN** 用户选好标题、智能体、YAML 与设备，但不选测试指定用例
- **THEN** 允许提交，表示执行该 YAML 的全部用例

### Requirement: 智能体单选且必选

智能体下拉 SHALL 为单选，选项 MUST 来自平台当前支持的流程；当前 MUST 只有 `sop` 一个选项。未选择智能体时提交按钮 MUST 置灰。用户选择某个流程后，弹窗 MUST 展示该流程对应的参数组；当前 `sop` 的参数组即 YAML、设备与测试指定用例。系统 MUST NOT 允许同时选择多个智能体。

#### Scenario: 未选智能体不能提交

- **WHEN** 用户没有选择智能体
- **THEN** 提交按钮置灰，无法提交

#### Scenario: 选择 sop 后出现 SOP 参数

- **WHEN** 用户选择当前唯一可用的 `sop` 流程（Agent-01）
- **THEN** 弹窗展示配置 YAML、设备与测试指定用例

#### Scenario: 不允许复选

- **WHEN** 用户操作智能体下拉
- **THEN** 只能选中一个选项，无法多选

### Requirement: 测试指定用例来自 YAML 标题

选中 YAML 后，前端 SHALL 在浏览器内解析该文件的根节点，读取每条用例的 `title`，填充「测试指定用例」下拉。下拉 MUST 含一个「全部用例」选项（值为空）。YAML 无法解析、根节点不是用例列表、或某条用例缺少非空 `title` 时，前端 MUST 给出可读提示，并且 MUST NOT 生成可选项。切换或清除 YAML 时 MUST 清空已选用例。

#### Scenario: 解析出多个标题

- **WHEN** 用户选择一份含「甲」「乙」两条用例的 YAML
- **THEN** 测试指定用例下拉包含「全部用例」「甲」「乙」

#### Scenario: 解析失败给出提示

- **WHEN** 用户选择一份无法解析的 YAML
- **THEN** 页面提示该文件无法解析，且用例下拉没有可选项

#### Scenario: 换文件后清空已选用例

- **WHEN** 用户先选了「甲」，随后更换了 YAML 文件
- **THEN** 已选的测试指定用例被清空，重新按新文件的标题生成

### Requirement: 弹窗提交载荷固定

提交时前端 MUST 以 multipart 发送：`title`、`agent_id`、`device_serial`、`case_title`（可为空）与 `config` 文件。前端 MUST NOT 再发送 `goal`、`documents` 或 `assistant_route`。设备下拉 MUST 展示设备 serial（有型号时附带型号），并把选中的 serial 原样提交。

#### Scenario: 提交字段

- **WHEN** 用户填好五项并提交
- **THEN** 请求体含 title、agent_id、device_serial、case_title 与 config，不含 goal、documents、assistant_route

#### Scenario: 用例为空串

- **WHEN** 用户选择「全部用例」后提交
- **THEN** 请求中的 case_title 为空串，表示跑全部用例
