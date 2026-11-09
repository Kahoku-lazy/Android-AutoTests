# case-manager-yaml-sync Specification

## Purpose
让本地 YAML 用例与平台用例库互通：同一份 YAML 既能从目录同步进库、也能在网页导入，还能把库里的用例原样导出为可执行 YAML；导入与导出全程保留执行侧需要的页面锚点（`anchor`）与日志证据（`log`），使「平台用例直接执行」与「本地 YAML 上传执行」拿到等价的输入。

## Requirements

### Requirement: 按目录同步 YAML 用例

系统 SHALL 提供按本地目录同步 YAML 用例的命令行入口：递归读取目录下所有 `.yaml` / `.yml`，每份 YAML 映射为目标项目下的一张用例表，表名取文件在目录内的相对路径。项目 SHALL 可按名称指定，不存在时创建。同步 MUST 为幂等：同一份 YAML 重复同步 MUST NOT 产生重复的表或用例行。表内以用例标题为匹配键，已存在则覆盖更新，不存在则新建。未出现在本次 YAML 中的旧行默认 MUST 保留，只有显式开启清理时 MUST 删除。无法解析或结构不合法的文件 MUST 被跳过并计入结论，MUST NOT 影响其余文件的同步。

#### Scenario: 首次同步建项目与用例表

- **WHEN** 对一个含 7 份 YAML 的目录执行同步，目标项目尚未创建
- **THEN** 创建该项目，并为每份 YAML 建一张同名用例表
- **AND** 结论中给出的用例条数等于各文件用例条数之和

#### Scenario: 重复同步不产生重复数据

- **WHEN** 对同一目录连续执行两次同步
- **THEN** 项目、用例表与用例行的数量与第一次完成时相同
- **AND** 结论中的新建条数为 0、更新条数等于已存在条数

#### Scenario: 未开启清理时保留缺席行

- **WHEN** 某张表在库中有 12 行，而对应 YAML 已删掉其中 1 条用例，本次同步未开启清理
- **THEN** 该表仍保留 12 行
- **AND** 结论中不报告删除

#### Scenario: 开启清理时删除缺席行

- **WHEN** 同上场景但本次同步开启了清理
- **THEN** 该表只剩 YAML 中剩余的 11 行
- **AND** 结论中报告删除 1 行

#### Scenario: 坏文件不阻断其余文件

- **WHEN** 目录中有一份 YAML 不是用例列表（例如根节点是字符串）
- **THEN** 该文件被跳过并在结论中给出文件名与原因
- **AND** 其余文件照常同步
- **AND** 命令以成功退出码结束

### Requirement: 网页导入 YAML 到用例库

系统 SHALL 提供上传导入接口：用户在某个用例项目内上传一份 YAML，服务端 SHALL 按与目录同步一致的规则解析并写入该项目。目标用例表可通过表编号指定，也可以缺省；缺省时 MUST 以 YAML 文件名（去扩展名）作为表名，已存在则复用。导入 MUST NOT 因同名用例而失败，MUST 采用覆盖更新。YAML 无法解析、根节点不是用例列表、某条用例缺标题或缺步骤、或步骤缺动作/断言时，接口 MUST 拒绝导入、MUST 返回可读原因，且 MUST NOT 落库任何一行。项目不属于当前用户时 MUST 返回不存在。

#### Scenario: 上传导入成功

- **WHEN** 用户向自己的项目上传一份含 12 条用例的 YAML，未指定目标表
- **THEN** 接口返回导入条数与新建/更新明细
- **AND** 该项目下出现一张以文件名命名的用例表，含 12 行

#### Scenario: 结构非法时整体不落库

- **WHEN** 上传的 YAML 中第 3 条用例缺少步骤
- **THEN** 接口返回失败与可读原因（含用例标题）
- **AND** 该项目下 MUST NOT 新增或修改任何用例行

#### Scenario: 文件名相同的重复导入复用同一张表

- **WHEN** 用户两次上传同名 YAML
- **THEN** 两次导入落在同一张用例表
- **AND** 表中用例行数不因重复导入而翻倍

#### Scenario: 越权项目被拒

- **WHEN** 用户向不属于自己的项目上传 YAML
- **THEN** 接口返回项目不存在
- **AND** MUST NOT 写入任何数据

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

### Requirement: 平台用例导出为可执行 YAML

系统 SHALL 能把选中的平台用例导出为可执行 YAML 文本：根节点为用例列表，每项含 `title` 与 `steps`，每步含 `action` 与 `assert`，该步存在执行提示时附 `anchor` 与 `log`，不存在时 MUST NOT 输出空节点。导出文本 MUST 能通过平台 YAML 校验，用例顺序 MUST 与选择顺序一致。导出 MUST NOT 修改库中数据。选中的用例不存在或不属于当前用户时 MUST 报错且不产出文本；未选中任何用例时 MUST 报错。

#### Scenario: 导出结果可通过平台校验

- **WHEN** 把某文件中的 3 条用例导出为 YAML
- **THEN** 导出的文本能被平台 YAML 校验接受
- **AND** 用例标题与步骤数与库中一致

#### Scenario: 往返保真

- **WHEN** 把一份带 `anchor` 与 `log` 的 YAML 导入后再导出
- **THEN** 导出文本的用例标题、每步动作/断言、页面锚点与日志证据与原始 YAML 等价

#### Scenario: 无执行提示时不写空节点

- **WHEN** 导出的步骤既没有 `anchor` 也没有 `log`
- **THEN** 该步只含 `action` 与 `assert`
