## Why

`frontend/src/shared/icons/index.ts` 是自绘 SVG 图标体系的唯一真相源，模块头注释写「24 个图标」，但实测该文件 `export const Icon*` 共 **45** 个（经 `makeIcon` 渲染函数导出）。注释与实现不符，接手者据此判断规模会误判。

## What Changes

- `frontend/src/shared/icons/index.ts` 头部注释「24 个图标」→「45 个图标」
- 同段其余描述经复核与实现一致，保持不动：「覆盖：设备管理、测试执行、元素定位、AI 助手、报告、用例等场景」·「使用 Vue 3 `defineComponent` + `h()` 渲染函数」
- 纯注释修订：不改任何导出名、路径数据、props 与渲染行为

## 关联文档

- 图标规范：`frontend/AGENTS.md` 硬性规范 §1.7（新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`）
- 无 PRD/ARCH 编号（注释订正，无行为变化）

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- （无）本变更不改变规格级行为，故 `.openspec.yaml` 设 `skip_specs: true`

## Impact

- `frontend/src/shared/icons/index.ts`（仅第 3 行注释）
- 不改令牌、不改组件结构、不涉及构建与运行时
