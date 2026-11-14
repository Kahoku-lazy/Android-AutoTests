# backend-bridge-agent Specification

## Purpose
让平台能直接调用一个「UI 执行」智能体：用 `engines/ae_harness/` 的原语装配角色、跑一次任务、把 HTML 报告落到平台目录，并把 token 用量作为结构化数据交回，全程不打印、不交互、不依赖后端。

## Requirements

### Requirement: 平台角色只经 ae_harness 原语装配

平台侧 UI 执行角色 MUST 经 `ae_harness.agents.create_agent` 创建，MUST NOT 直接构造 `Agent`，MUST NOT 导入 `ae_harness.assistant` 下的任何模块。

角色 MUST 装载三样东西：选定的模型配置（短名由调用方传入）、`UI_EXECUTOR_PROMPT` 提示词、全量设备工具。

#### Scenario: 装配出的角色可用设备工具

- **WHEN** 构建平台 UI 执行角色
- **THEN** 返回的智能体带全量设备工具
- **AND** 其密钥环境变量名可从返回值读到

#### Scenario: 不依赖控制台入口

- **WHEN** 审查本目录的导入
- **THEN** 不存在对 `ae_harness.assistant` 的导入
- **AND** 不存在对 `ae_harness.workflow` 的导入

### Requirement: 一次运行的入口契约

本目录 MUST 提供「跑一次任务」的入口：接收任务文本与模型短名等参数，返回结构化结果，MUST NOT 打印、MUST NOT 读命令行参数、MUST NOT 进入交互循环。

返回结果 MUST 至少包含：最终文本、报告文件路径、日志文件路径、token 四类合计、按密钥环境变量名分组的调用次数、逐次用量明细。

入口 MUST 在运行期间挂观测中间件，使压缩决策与最终提示词随产物落盘。

#### Scenario: 跑完拿到结构化结果

- **WHEN** 调用一次运行入口并正常结束
- **THEN** 返回值含最终文本与报告路径
- **AND** 含 token 四类合计与按密钥分组

#### Scenario: 结果不依赖打印

- **WHEN** 调用入口
- **THEN** 该函数不向标准输出写任何内容

### Requirement: 报告落在平台目录

报告 MUST 输出到 `仓库根/logs/agents/backend_bridge/`，每次运行一个独立子目录，文件名含时间戳与角色键。

路径 MUST 只在一处定义，其它模块 MUST NOT 自行拼接该路径常量。

#### Scenario: 报告路径符合约定

- **WHEN** 一次运行结束
- **THEN** 报告文件位于 `logs/agents/backend_bridge/<时间戳>/` 下
- **AND** 同一次运行的 JSONL 与 HTML 在同一子目录

#### Scenario: 目录按需创建

- **WHEN** 目标目录不存在
- **THEN** 入口自动创建它，不抛异常

### Requirement: 采集不引入后端依赖

本目录 MUST NOT 导入 `django.*` / `apps.*`，MUST NOT 直接读写数据库，MUST NOT 发起 HTTP 调用。

token 入账 MUST 由调用方（后端）负责：本目录只把用量整理成结构化数据返回。

#### Scenario: 无 Django 环境可运行

- **WHEN** 在未安装 Django 的环境里调用入口
- **THEN** 运行与报告产出照常

#### Scenario: 审查导入

- **WHEN** 检查本目录所有模块的导入
- **THEN** 不存在 `django`、`apps`、`backend` 前缀的导入

### Requirement: 控制台入口零影响

本变更 MUST NOT 修改 `engines/ae_harness/` 下任何代码。

#### Scenario: 控制台入口行为不变

- **WHEN** 变更实施后运行 `python -m engines.ae_harness.assistant.agent_executor`
- **THEN** 行为与参数与变更前一致

### Requirement: 报告可经接口读取

平台 MUST 提供报告列表与单文件读取两个接口。列表 MUST 新的在前，返回运行名、报告名、日志名与大小。

单文件读取 MUST 走路径白名单：只接受「运行目录名 + 文件名」两段结构，解析后 MUST 仍在报告根目录内；越界与非法文件名 MUST 拒绝。文件不存在 MUST 返回 404，路径非法 MUST 返回 400。

#### Scenario: 列出最近报告

- **WHEN** 报告根下存在多个运行目录
- **THEN** 列表按运行名倒序返回
- **AND** 每项含报告名与日志名

#### Scenario: 拒绝目录穿越

- **WHEN** 请求的目录名或文件名含 `..` 或非法扩展名
- **THEN** 返回参数错误，不读取任何文件

### Requirement: 运行用量写入既有账本

平台一次运行的逐次用量 MUST 写入 `usage_ledger` 的既有账本，MUST NOT 另建第二套 token 表。

幂等键 MUST 唯一标识「来源 + 执行 ID + 轮次」，重复写入 MUST 更新而非新增。厂商 MUST 由密钥环境变量名推断后交给账本归一。单条失败 MUST NOT 影响其它条，也 MUST NOT 向上抛错。

#### Scenario: 两条用量写入两行

- **WHEN** 一次运行产出两条用量记录
- **THEN** 账本新增两行，来源与模型被带上

#### Scenario: 重复写入不新增

- **WHEN** 同一执行 ID 与同一轮次再次写入
- **THEN** 账本行数不变

### Requirement: 平台执行有可用的触发入口

平台 MUST 提供一个可执行的一次性触发入口，把「跑一次 → 出报告 → 入账」串起来，使本变更在尚无 HTTP 触发口时仍可端到端验证。

#### Scenario: 命令跑通全链路

- **WHEN** 执行该入口并给一条任务
- **THEN** 报告落在平台报告目录
- **AND** 用量写入账本

### Requirement: 平台角色出现在 AI 助手对话清单

AI 助手的对话卡片清单 MUST 同时包含引擎侧单智能体与平台侧角色，平台卡片 MUST 有稳定的编排键。

平台键 MUST 与引擎侧键不重名；遇到未知键时 MUST 仍然返回 404。

#### Scenario: 清单同时列出两边

- **WHEN** 请求对话卡片清单
- **THEN** 结果含引擎侧既有的编排键
- **AND** 含平台侧编排键

### Requirement: 平台编排键走平台会话

对话一轮请求命中平台键时，MUST 走平台会话运行，MUST NOT 走引擎侧单智能体会话；未命中时 MUST 回退到引擎侧，行为不变。

一轮对话 MUST 返回本轮文本；MUST 在同一个连接内复用同一个角色实例，使多轮上下文连续；换设备 MUST 只更新设备字段。

#### Scenario: 平台键返回本轮文本

- **WHEN** 用平台键发起一轮对话
- **THEN** 返回该轮回复文本

#### Scenario: 同一连接复用角色

- **WHEN** 同一连接键连续发起两轮
- **THEN** 两轮使用同一个角色实例
- **AND** 各轮各产出一份报告

#### Scenario: 引擎侧键行为不变

- **WHEN** 用引擎侧键发起对话
- **THEN** 仍走原有单智能体会话

### Requirement: 平台对话每轮入账

平台键的每一轮对话 MUST 把该轮用量写入既有账本，执行 ID MUST 能定位到该轮报告目录。

入账失败 MUST NOT 阻断对话返回。

#### Scenario: 一轮写一条账

- **WHEN** 平台键完成一轮对话
- **THEN** 账本新增该轮的用量行
- **AND** 对话文本照常返回

### Requirement: 事件面板展示全量过程

平台一轮对话的事件面板 MUST 展示该轮的关键过程：每次模型调用的模型名与 token、每段思考全文、每段回复全文、每次工具调用的入参与输出全文（含结果状态）。

增量事件 MUST 在内存折叠成段，MUST NOT 逐条刷屏。

#### Scenario: 工具调用可见入参与输出

- **WHEN** 一轮对话调用了工具
- **THEN** 面板出现该工具的名字、完整入参与完整输出
- **AND** 出现结果状态

#### Scenario: 思考与结论可见全文

- **WHEN** 一轮对话产生思考与最终结论
- **THEN** 面板同时展示两者全文

### Requirement: 编排卡片带上线日期

对话编排卡片 MUST 带一个上线日期，供使用方判断新旧；日期 MUST 来自代码内显式声明的常量，MUST NOT 由运行时时间冒充。

界面 MUST 在卡片上展示该日期，并 MAY 给最新的一张加标注；默认选中项 MUST NOT 因日期排序而改变。

#### Scenario: 卡片显示日期

- **WHEN** 打开对话页
- **THEN** 每张卡片显示上线日期
- **AND** 最新的一张有标注

#### Scenario: 默认选中不受影响

- **WHEN** 平台卡上线日期晚于引擎侧卡
- **THEN** 默认选中仍是清单第一张

### Requirement: 对话页只保留平台角色

AI 助手对话页的编排清单 MUST 只包含平台侧角色。引擎侧单智能体清单 MUST 为空，除非另开变更新增。

未知编排键 MUST 仍然返回 404，MUST NOT 因为清单为空而静默放行。

#### Scenario: 只剩平台卡

- **WHEN** 请求对话卡片清单
- **THEN** 结果只有平台侧键
- **AND** 不含引擎侧键

#### Scenario: 未知键仍拒绝

- **WHEN** 用已被移除的引擎侧键发起对话
- **THEN** 返回 404
