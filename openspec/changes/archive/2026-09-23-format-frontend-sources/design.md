## Context

动机见 proposal.md。现状与约束（2026-09-23 实测）：

- 配置：`frontend/.prettierrc`（`semi: false`、`singleQuote: false`、`trailingComma: all`、`printWidth: 100`、`tabWidth: 2`、`arrowParens: always`）。
- 不合规规模：`src/**/*.{vue,js,css}` **110 个文件**、`src/**/*.ts` **98 个文件**。
- package.json 已有 `format` 脚本，但只覆盖 `{ts,vue,css}`、**漏掉 `.js`**；CI 的阻塞门禁覆盖 `{vue,js,css}`、**漏掉 `.ts`**。两端范围不一致是这两个红灯长期共存的原因之一。
- 约束一：`AGENTS.md` 测试范围收敛条款——禁止主动跑全量回归；本次属大范围机械改动，验证需用"该工具自身的检查"而非跑测试套件。
- 约束二：仓库规范明确"格式类要求以工具配置为准"，因此**不改配置**，只让源码服从既有配置。

## Goals / Non-Goals

**Goals:**

- 两处 prettier 门禁（阻塞范围与 `.ts` 范围）同时转绿。
- 让后续改动的 diff 不再混入格式噪音。

**Non-Goals:**

- 不改 `.prettierrc` 任何选项（改配置会改变"什么算合规"，属独立议题）。
- 不统一 package.json `format` 脚本与 CI 检查的范围差异（属独立议题，本次只消费现状）。
- 不触碰 `frontend/src` 之外的文件，不触碰 `tools/`、`engines/`、`apps/`。
- 不做任何语义修改。

## Decisions

### 决策 1：一次性对两个范围同时格式化，而不是分批

- 理由：两个范围同源同配置，分批只会让第一次的 diff 在第二次被再动一遍（`{vue,js,css}` 与 `.ts` 无重叠文件，但同属一次"让源码服从配置"的动作）；一次完成可让两处门禁同时转绿。
- 备选：先只修阻塞范围（vue/js/css）。被否——`.ts` 的 98 个文件仍是红灯，后续仍要再来一次大 diff。

### 决策 2：用 `prettier --write` 直接落盘，不做人工挑选

- 理由：工具输出即配置的确定性结果，人工挑选等于引入主观风格，违背"以工具配置为唯一真相源"。
- 风险控制：落盘后逐类核对"不合规数 = 0"，并用类型检查确认无语法破坏。

### 决策 3：验证以「工具自身检查 + 类型检查」为最小集，不跑测试套件

- 理由：prettier 是纯语法树级重排版，不改变语义；类型检查能捕获任何格式化引入的语法破坏，成本远低于测试套件，且符合测试范围收敛条款。
- 备选：跑 `npm test` 全量前端套件。被否——条款禁止主动跑全量回归，且对本类改动的边际价值低。

## 模块防火墙自检

本变更只重排前端源码空白与标点：

- 跨 App import：不涉及。
- 跨 App import service / runner / consumer / state_machine：不涉及。
- INSERT / UPDATE / DELETE 收敛到 api.py：不涉及（无写库行为）。
- 前端不直连数据库、仪表盘不做写操作：不涉及。

无新增跨模块依赖。

## Risks / Trade-offs

- [大 diff 掩盖语义改动] → 提交信息明确声明"仅格式"；必要时用忽略空白的 diff 复核（`git diff -w`）。
- [格式化意外破坏模板/字符串] → 以 `vue-tsc` 与 `prettier --check` 复核；如出现语法错误，回滚该文件并单独处理。
- [与并行会话的改动冲突] → 本变更单独成提交，且在提交前确认工作区无其他未提交改动（当前为干净状态）。

## Migration Plan

- 生效方式：合并后两处门禁即转绿，无部署步骤。
- 验证：`npx prettier --check "src/**/*.{vue,js,css}"` 与 `"src/**/*.ts"` 均为 0 不合规；`npx vue-tsc --noEmit` 通过。
- 回滚：`git revert` 该提交即可（纯格式，无状态残留）。
