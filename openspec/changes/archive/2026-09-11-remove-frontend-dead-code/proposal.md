## Why

前端共享层（`frontend/src/shared/`）累积了 5 个零消费方文件、共 464 行：AI 流式状态机、存储抽象、WS 地址构造、步骤字段常量、模块色常量。它们既无导入方，又让"共享层准入判据（第二个真实消费方）"失去可信度——审计时无法区分"活的基础设施"与"死代码"，会误导后续的共享层判断。现在清理成本为零（无行为变化），收益是共享层重新可读。

## What Changes

- 移除 5 个零引用文件（464 行 / 425 非空行）：
  - `frontend/src/shared/sse/SSEMessageBuilder.ts`（306 行）— 全仓库 0 消费方；`src` 内 `new WebSocket`、`EventSource`、`ReadableStream` 均为 0，前端不存在流式通道
  - `frontend/src/shared/composables/useStorage.ts`（66 行）— `useStorage` / `useRawStorage` 0 引用
  - `frontend/src/shared/ws-url.ts`（6 行）— `wsUrl` 0 引用
  - `frontend/src/shared/constants/steps.ts`（73 行）— 5 个导出全部 0 引用
  - `frontend/src/shared/constants/module-colors.ts`（13 行）— 文件自述"暂无消费方……保留待清理"
- 移除随之变空的目录 `frontend/src/shared/sse/`、`frontend/src/shared/constants/`
- **无 BREAKING**：无导入方、无运行时行为变化、无 API/协议/依赖变更

## 关联文档

- 无 PRD/ARCH 关联：纯死代码清理，不改变需求级行为，判定依据来自共享层审计分析
> 记录时点：删除已先行完成（用户直接指令），本变更为实施后补录，tasks.md 逐条附验证证据

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯删除零引用文件，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 删除范围：`frontend/src/shared/{sse/SSEMessageBuilder.ts, composables/useStorage.ts, ws-url.ts, constants/steps.ts, constants/module-colors.ts}`
- 产品代码零改动、后端零改动、依赖零改动
- 遗留文档引用（本次不改，仅记录，供后续文档同步）：`dev_docs/项目笔记/1.md:78,167`、`dev_docs/03-设计与架构/技术栈参考.md:160`、`frontend/tests/PLAN-batch2-3modules.md:497`
- 未纳入本变更的相邻死代码（另行决策）：`shared/components/AnimatedMenuIcon.vue`（被 import 但模板未使用）、`tokens.css` 4 个无消费方 `--app-sidebar-*` 令牌、`types/ai.ts` 的 `ConnectionMode` 残留类型
