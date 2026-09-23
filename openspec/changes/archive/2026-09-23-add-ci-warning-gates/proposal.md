## Why

仓库的四道静态检查存在覆盖缺口，规则写在纸面但无人执行：前端的代码检查（eslint）与类型检查（vue-tsc）从未接入 CI，prettier 的 CI 检查范围漏掉 `.ts`，后端 ruff 的 CI 范围漏掉 `engines/`。这些缺口里的问题只能靠人工偶然发现，且会持续累积。

## What Changes

- 在 `.github/workflows/ci-phase1.yml` 新增 4 道**仅警告不拦截**的检查：
  1. 前端代码检查：`cd frontend && npm run lint`（eslint src/）
  2. 前端类型检查：`cd frontend && npm run typecheck`（vue-tsc --noEmit）
  3. prettier 检查范围：由 `src/**/*.{vue,js,css}` 扩展为包含 `.ts`
  4. 后端 ruff 检查范围：由 `apps/ config/ gateway/ shared/ models/` 扩展为包含 `engines/`
- 四道检查均以「失败不阻断构建」的形式接入，并在 CI 日志中输出失败摘要，用于量化存量问题规模。
- 将 `eevog` 纳入 CI 触发分支名单（原名单为 `main` / `Kahoku` / `Aaron` / `feat/*` / `fix/*`），使上述检查在 eevog 分支上可被实际执行与验证。
- **BREAKING**：无。不改变运行期行为，不新增运行时依赖。
- 本变更**不**把任何检查转为拦截。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更属工具链类改动，需求来源为代码规范与门禁盘点时发现的覆盖缺口，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。本变更为纯 CI 工具链接入，不引入新的系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 仅影响 `.github/workflows/ci-phase1.yml` 一个文件；不涉及 `apps/` 各模块、前端页面、API 契约、数据模型或依赖。
- CI 运行时长增加约 2 个步骤的实际耗时（eslint、vue-tsc 为新增执行；另 2 道为既有命令的范围扩展）。
- 存量代码违规**不会**导致构建失败，但会在 CI 日志与 PR 注解中暴露；这些数字作为后续「转拦截」的基线。
- 触发面变化：`eevog` 分支的每次推送将开始触发本 workflow（此前该分支无任何 CI 运行记录）。此后该分支的 CI 结论由既有拦截型检查决定。
