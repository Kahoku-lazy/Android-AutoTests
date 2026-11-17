# 侧栏入口图标补齐与分组内配色区分

## Why

侧栏「用户管理」「模型配置」的图标方块是空的：两处写的 `data-lucide` 名（`users` / `cpu`）没有登记进 `lucideIconSubset`，`createIcons` 找不到图标就只留下一个色块，用户看到的是两个空方框。配色也有同样的问题：运营三项都取 `--c-ops`、设备与串口都取 `--c-device`，同一分组里并排的入口长得一模一样，扫视时无法靠颜色区分。

## What Changes

- 自绘两个图标（24 网格、线宽 2、圆头圆角，与 lucide 同一套视觉重量）：**用户管理**＝一大一小两个人头 + 后肩；**模型配置**＝芯片本体 + 裸片 + 八根引脚。两个都登记进 `lucideIconSubset`，模板照旧只写 `data-lucide` 名。
- 侧栏入口配色改为「同一分组内互不相同」：串口日志 `--c-device` → `--c-workflow`；运营三项 `--c-ops`×3 → `--c-account` / `--c-element` / `--c-ops`；任务清单 `--c-ai` → `--c-task`（与 AI 助手分开）。
- 新增两个**入口级**模块色别名 `--c-account`、`--c-task`，都复用调色板已有原子（`--color-blue-68-s64`、`--color-purple-56`），不新增 `--color-*`。
- 补测试：每个导航图标都已在子集里登记、同分组内入口不同色 —— 前者能挡住这次的「空方块」回归。

## 关联文档

无关联 PRD 编号：本次是需求方 2026-11-17 按侧栏截图直接提出的缺陷与配色调整。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-sidebar-nav`：新增「入口图标必须已登记」「同一分组内入口不得同色」两条要求。

## Impact

- `frontend/src/shared/icons/lucide-registry.ts`（自绘图标 + 登记）
- `frontend/src/shared/components/sidebarNavConfig.ts`（图标名与 `MOD_COLORS`）
- `frontend/src/shared/styles/tokens.css`（两个入口级别名）
- `frontend/tests/shared/p0/sidebarNavConfig.spec.ts`（图标登记与配色断言）
- `.agents/skills/doodle-craft/SKILL.md`、`references/tokens.md`（登记新的彩笔令牌口径）
