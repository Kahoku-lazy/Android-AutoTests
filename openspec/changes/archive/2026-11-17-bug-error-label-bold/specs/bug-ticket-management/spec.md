## ADDED Requirements

### Requirement: 错误内容行首标签加粗

BUG 单详情「错误内容」卡里的每一行 MUST 按「行首标签 + 值」渲染：行首标签（含冒号原文，如 `来源任务：`）MUST 以 `font-weight: var(--app-font-weight-bold)`（700）呈现，冒号之后的值 MUST 保持常规字重；两者 MUST 同为 14px 等宽字体，字号 MUST NOT 因加粗而改变。

标签识别 MUST 走模块内纯函数（`helpers/errorDetail.ts::splitErrorDetail`），MUST NOT 在组件里写解析逻辑。判定规则 MUST 为：行首连续不超过 12 个字符 + 一个中文或英文冒号，且该段 MUST NOT 含空白与斜杠；冒号后紧跟 `//` 的行 MUST 整行当正文（避免把 URL 协议段当标签）。没有行首标签的行（堆栈、缩进片段、纯文本）MUST 整行当正文，MUST 保留原有前导空白与折行行为。加粗 MUST NOT 改变卡片底色、描边、硬影与行高。

#### Scenario: 字段名与值字重不同

- **WHEN** 打开详情里带 `来源任务：#227 …`、`任务状态：failed` 的 BUG 单
- **THEN** 每行冒号及其之前的字段名计算字重为 700
- **AND** 冒号之后的值为常规字重（400），字号同为 14px

#### Scenario: 堆栈行不被当标签

- **WHEN** 详情含 `  at run (runner.js:12)` 这类行
- **THEN** 该行整行按正文渲染，前导空格保留
- **AND** 行内不出现加粗片段

#### Scenario: URL 不被拆成标签

- **WHEN** 详情含 `https://example.com/a:b`
- **THEN** 整行按正文渲染，不把 `https:` 摘出来加粗

#### Scenario: 卡片几何与行高不变

- **WHEN** 比较加粗前后的错误内容卡
- **THEN** 底色渐变、1.5px 描边、4px 硬影与行距一致
- **AND** 长内容仍在卡内滚动
