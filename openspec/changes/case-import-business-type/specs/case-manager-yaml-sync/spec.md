## MODIFIED Requirements

### Requirement: 导入保留执行提示与元数据

导入 MUST 把每步可选的页面锚点（`anchor`：`page` / `entry` / `target`，单值不超过 120 字）与日志证据（`log`：`sku`、`port`、`keywords`）原样写入用例步骤，并在读回时原样返回。导入 SHALL 识别 YAML 中的可选元数据并映射为平台字段：数值优先级 1/2/3 分别映射 `P0` / `P1` / `P2`，也可直接给 `P0` / `P1` / `P2`；系统取 `ANDROID` / `WEB` / `IOS` / `API` 中的首个合法值；类型缺失时为 `AUTO`，给出时含「自动化」才为 `AUTO`，否则 `FUNC`；业务类型「家电 / 照明 / APP」映射 `appliance` / `lighting` / `app`；模块与前置条件取原文字。

导入 SHALL 接受一个**默认业务类型**参数，取值 `appliance` / `lighting` / `app`，缺省 MUST 为 `appliance`。YAML 显式给出业务类型时 MUST 以 YAML 为准；未给出时 MUST 使用该默认值。命令行同步与网页导入 MUST 都支持该参数；取值不在枚举内时 MUST 拒绝导入并列出可选值。其余元数据缺失时 MUST 使用默认值（优先级 `P1`、系统 `ANDROID`）而不是拒绝导入。

#### Scenario: 页面锚点保真

- **WHEN** 导入的某一步带 `anchor: {page: 详情页, entry: 颜色, target: 色温滑块}`
- **THEN** 读回该步骤时三个键的值与原文相同

#### Scenario: 日志证据保真

- **WHEN** 导入的某一步带 `log: {sku: H6810, port: 7005, keywords: [switch_on, switch_off]}`
- **THEN** 读回该步骤时型号、端口与关键词顺序与原文相同
- **AND** 同一关键词出现两次时，读回仍为两次

#### Scenario: 数值优先级映射

- **WHEN** YAML 中某条用例的 `priority` 为数值 1
- **THEN** 导入后该用例优先级为 `P0`

#### Scenario: 元数据缺失使用默认值

- **WHEN** YAML 只给 `title` 与 `steps`，没有任何元数据，且导入未指定默认业务类型
- **THEN** 导入后优先级 `P1`、系统 `ANDROID`、类型 `AUTO`、业务类型 `appliance`

#### Scenario: 指定默认业务类型后导入

- **WHEN** 以默认业务类型 `lighting` 导入一份没有 `business` 字段的 YAML
- **THEN** 导入的每条用例业务类型都是 `lighting`
- **AND** 重复导入后仍为 `lighting`（不会被刷回 `appliance`）

#### Scenario: YAML 显式业务类型优先

- **WHEN** 导入时指定默认业务类型 `lighting`，而某条用例的 YAML 写了 `business: 家电`
- **THEN** 该条用例业务类型为 `appliance`
- **AND** 同文件其余未写 `business` 的用例为 `lighting`

#### Scenario: 非法默认业务类型被拒

- **WHEN** 导入时指定的默认业务类型不在 `appliance` / `lighting` / `app` 之内
- **THEN** 导入被拒绝并列出可选值
- **AND** MUST NOT 落库任何一行
