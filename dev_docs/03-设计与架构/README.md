# 03-设计与架构

> 结构对齐 `02-PRD需求`：**1 份总设计真相 + 模块设计 MD + 技术栈/工具 + `html/` 图册与报告**。  
> 同主题多份文档的角色划分见 [`html/对比-同主题文档差异.html`](./html/对比-同主题文档差异.html)。

## 总设计（1）

| 文件 | 说明 |
|------|------|
| [`当前实现架构方案.md`](./当前实现架构方案.md) | **主文档** · 基于代码的架构真相（通道、分层、模式、技术栈） |

## 模块设计（Markdown）

| 模块 | 文件 |
|------|------|
| AI 助手 | [`模块-AI助手-技术架构与功能设计.md`](./模块-AI助手-技术架构与功能设计.md) |
| 元素定位 | [`模块-元素定位-元素管理页UI改动总结.md`](./模块-元素定位-元素管理页UI改动总结.md) |

> 其余模块的「要什么」在 `02-PRD需求/`；本目录以图册/审查/原型为主，见下方 `html/`。

## 技术栈

| 文件 | 说明 |
|------|------|
| [`技术栈-README.md`](./技术栈-README.md) | 技术选型与素材约定 |
| [`技术栈-命名统一标准.md`](./技术栈-命名统一标准.md) | 前后端 / API / DB 命名 |
| [`技术栈-animal-island-ui设计素材.md`](./技术栈-animal-island-ui设计素材.md) | 动森 design token |
| [`技术栈-PROMPT-animal-island-ui一键提示词.md`](./技术栈-PROMPT-animal-island-ui一键提示词.md) | HTML 报告生成提示词 |

## 工具

| 文件 | 说明 |
|------|------|
| [`工具-VUE_API_CONTRACT.md`](./工具-VUE_API_CONTRACT.md) | 前后端接口契约 |

## HTML（`html/`）

### 对比（必读）

- [`html/对比-同主题文档差异.html`](./html/对比-同主题文档差异.html) — 同主题多文档的主/参考/原型/已删裁决

### 平台总设计图册与报告

| 文件 | 角色 |
|------|------|
| [`html/总设计-模块化架构设计方案.html`](./html/总设计-模块化架构设计方案.html) | 理想架构 + 差距 + 路线 |
| [`html/总设计-模块化架构分析报告_20260709.html`](./html/总设计-模块化架构分析报告_20260709.html) | 耦合/防火墙快照 |
| [`html/总设计-架构审查报告_20260705.html`](./html/总设计-架构审查报告_20260705.html) | 历史审查基线 |
| [`html/总设计-模块代码复杂度分析报告_20260709.html`](./html/总设计-模块代码复杂度分析报告_20260709.html) | 复杂度指标 |
| [`html/总设计-system-architecture.html`](./html/总设计-system-architecture.html) | 五层图 |
| [`html/总设计-data-model.html`](./html/总设计-data-model.html) | 数据模型图 |
| [`html/总设计-testhub-architecture.html`](./html/总设计-testhub-architecture.html) | TestHub 对标（非现网） |
| [`html/结构-frontend-architecture.html`](./html/结构-frontend-architecture.html) | 前端模块边界图 |
| [`html/结构-产品原型导航页.html`](./html/结构-产品原型导航页.html) | 低保真原型入口 |

### 按模块（原型 / 审查 / 流程）

| 模块 | 文件 | 角色 |
|------|------|------|
| 仪表盘 | [`html/模块-仪表盘-dashboard.html`](./html/模块-仪表盘-dashboard.html) | 原型 |
| 设备管理 | [`html/模块-设备管理-devices.html`](./html/模块-设备管理-devices.html) | 原型 |
| 元素定位 | [`html/模块-元素定位-elements.html`](./html/模块-元素定位-elements.html) | 原型 |
| 用例管理 | [`html/模块-用例管理-cases.html`](./html/模块-用例管理-cases.html) | 原型 |
| 执行引擎 | [`html/模块-执行引擎-架构审查报告_设备执行控制管线_20260705.html`](./html/模块-执行引擎-架构审查报告_设备执行控制管线_20260705.html) | **主审查** |
| 执行引擎 | [`html/模块-执行引擎-execution-flow.html`](./html/模块-执行引擎-execution-flow.html) | 流程图 |
| 执行引擎 | [`html/模块-执行引擎-runner.html`](./html/模块-执行引擎-runner.html) | 原型 |
| 测试报告 | [`html/模块-测试报告-report-generator-redesign.html`](./html/模块-测试报告-report-generator-redesign.html) | **主 UI 设计** |
| 测试报告 | [`html/模块-测试报告-reports.html`](./html/模块-测试报告-reports.html) | 早期原型 |
| 登录认证 | [`html/模块-登录认证-login.html`](./html/模块-登录认证-login.html) | 原型 |

## 边界

| 类型 | 目录 |
|------|------|
| 需求 / AC | `02-PRD需求/` |
| 架构 / 图 / 审查 / 原型 | **本目录** |
| 编程工作流 / 质量 / 测试 | `05-开发与测试/{模块}/` |
