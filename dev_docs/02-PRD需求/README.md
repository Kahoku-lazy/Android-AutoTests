# 02-PRD 需求

> 本目录为**全部需求文档唯一存放处**。
> Markdown 结构固定：**1 份总需求 + 7 份子模块 PRD + 本 README**。
> HTML 全功能规格（对齐现网）放在子目录 [`html/`](./html/)。

## 产品总需求

- ✅ [`实际需求文档.md`](./实际需求文档.md) — 总 PRD v1.0（平台定位、用户故事地图、七模块全景）

## 子模块 PRD（Markdown）

| 序号 | 文件 | 模块 |
|:--:|------|------|
| 01 | [`子PRD-01-element-locator.md`](./子PRD-01-element-locator.md) | 元素定位 |
| 02 | [`子PRD-02-device-pool.md`](./子PRD-02-device-pool.md) | 设备管理 |
| 03 | [`子PRD-03-case-manager.md`](./子PRD-03-case-manager.md) | 用例管理 |
| 04 | [`子PRD-04-test-runner.md`](./子PRD-04-test-runner.md) | 执行引擎 |
| 05 | [`子PRD-05-report-generator.md`](./子PRD-05-report-generator.md) | 测试报告 |
| 06 | [`子PRD-06-ai-assistant.md`](./子PRD-06-ai-assistant.md) | AI 助手 |
| 07 | [`子PRD-07-dashboard.md`](./子PRD-07-dashboard.md) | 仪表盘 |

## HTML 全功能规格（以现网代码为准）

结构对齐仪表盘标杆：业务视角 · 技术视角 · 数据链 · 状态机 · 治理验收 · Agent 提示词 · 现状差距。

| 文件 | 模块 | 现网端点摘要 |
|------|------|-------------|
| [`html/子PRD-01-element-locator-全功能需求.html`](./html/子PRD-01-element-locator-全功能需求.html) | 元素定位 | 13 REST + 1 WS |
| [`html/子PRD-02-device-pool-全功能需求.html`](./html/子PRD-02-device-pool-全功能需求.html) | 设备管理 | 13 REST（含局域网） |
| [`html/子PRD-03-case-manager-全功能需求.html`](./html/子PRD-03-case-manager-全功能需求.html) | 用例管理 | 10 REST |
| [`html/子PRD-04-test-runner-全功能需求.html`](./html/子PRD-04-test-runner-全功能需求.html) | 执行引擎 | 12 REST + 1 WS |
| [`html/子PRD-05-report-generator-全功能需求.html`](./html/子PRD-05-report-generator-全功能需求.html) | 测试报告 | 4 REST |
| [`html/子PRD-06-ai-assistant-全功能需求.html`](./html/子PRD-06-ai-assistant-全功能需求.html) | AI 助手 | 31 REST + AgentScope SSE |
| [`html/子PRD-07-dashboard-全功能需求.html`](./html/子PRD-07-dashboard-全功能需求.html) | 仪表盘 | 只读聚合 |

> 若 MD 与 HTML「现状差距」冲突，**以现网代码 + HTML 为准**，并回写 MD。

## 方法论（不落本地 md）

以下内容**直接写在** [`../index.html`](../index.html) → PRD 需求阶段内嵌栏目：

- 需求矛盾分析方法（Gate 1 辅助）
- 优秀设计约定（标杆需求/交互范例收录规则）
