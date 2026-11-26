## Purpose

把 deepeval 封装成可复用的引擎能力：上层只传「样本 + 方法 + 裁判」，引擎返回分数、理由与一份官方看板产物。它不认平台角色、不落库、不读业务表，是评测语义的唯一实现处。

## ADDED Requirements

### Requirement: 评测语义只在引擎层实现

评测的算法与结果结构 MUST 只在 `engines/eval` 内实现；其它层 MUST NOT import deepeval。

引擎 MUST 提供：裁判模型构造、评测方法目录、一次运行入口；MUST NOT 依赖 `django`、MUST NOT 依赖 `backend.apps.*`、MUST NOT 写数据库。

#### Scenario: 其它层不直接依赖 deepeval

- **WHEN** 检索仓库里 `import deepeval` 的位置
- **THEN** 只出现在 `engines/eval` 内
- **AND** `backend/apps/ai_assistant` 只通过 `engines.backend_bridge` 调用评测

### Requirement: 裁判模型由调用方指定

引擎 MUST 接受调用方传入的厂商、密钥环境变量名、模型名与可选端点，构造可被官方 metric 使用的裁判模型。

裁判模型 MUST NOT 写死在引擎里；MUST NOT 由引擎自己读平台配置表。

#### Scenario: 换裁判模型不改引擎代码

- **WHEN** 调用方把判分模型从 A 换成 B 并传入新的厂商与模型名
- **THEN** 同一次评测使用 B 打分
- **AND** 引擎代码无需修改

### Requirement: 评测方法可枚举且带判定点

引擎 MUST 提供方法目录，每项 MUST 至少包含：方法标识、名称、适用对象、判定点文本（评测逻辑）、默认阈值。

上层展示「用什么方法评的」时 MUST 直接读取该判定点文本，MUST NOT 在页面另写一份。

#### Scenario: 页面能看到判定点

- **WHEN** 上层读取方法目录
- **THEN** 每项带可直接展示的判定点文本
- **AND** 文本与引擎实际打分使用的判定点一致

### Requirement: 一次运行产出一份官方看板与结构化结果

一次评测运行 MUST 调用 deepeval 官方 `evaluate()`，并通过 `DisplayConfig` 同时开启：结果目录落盘（`test_run_*.json`）与 HTML 看板导出。

返回值 MUST 包含：每个样本的分数与理由、看板 HTML 路径、test_run JSON 路径、判分调用用量。

引擎 MUST NOT 自己拼装图表。

#### Scenario: 跑完能拿到看板文件

- **WHEN** 用两个样本发起一次评测
- **THEN** 结果里给出看板 HTML 路径
- **AND** 该文件存在且可被浏览器打开

#### Scenario: 每个样本都有分数与理由

- **WHEN** 评测结束
- **THEN** 每个样本一条记录，含 0–1 分与理由文本
- **AND** 记录与看板里的条目一一对应
