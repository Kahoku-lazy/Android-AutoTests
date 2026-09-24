# 场景一：平台内 Vue 页面 / 组件

在本仓做**真实前端改动**时走这条路：改的是平台代码，样式由 Element Plus 全局覆盖 + `shared/` 共享件提供，最终要过前端门禁与 openspec 验收。

组件级规格见 [components/](components/)；页面层规则见 [page-layout.md](page-layout.md)；令牌检索见 [tokens.md](tokens.md)。

## 1. 四层不越界

| 层 | 是什么 | 谁能改 |
|:--:|--------|--------|
| 页面骨架 | `.doc-page` / `.doc-body` / `.doc-section` / `wb-shell` 作用域 | 模块 |
| 基础原子 | Element Plus 组件（Button / Input / Table / Dialog…） | 全局覆盖只改 `style.css` + `tokens.css` 的 `--el-*` |
| 业务组件 | `shared/components/**`（卡片 / Badge / KPI / 三态…） | 共享件自身；模块只组合 |
| 视觉令牌 | `shared/styles/tokens.css` | 改值只改 T0 原子 |

上层**不反向侵入**下层：模块不许给共享件补第二套皮肤，也不许绕过共享件自造同类零件。

## 2. 先判层，再动手（L0–L5）

模块只拥有自己页面的 **L2–L5**，不拥有 L1（侧栏 + 主区壳）。归属表、标准骨架、滚动与宽度规则见 [page-layout.md](page-layout.md) §4.0–4.7。三种页面变体（卡片网格 + KPI / 表格列表 + 筛选栏 / 左树 + 右内容）也在那里，复制骨架改字段即可。

## 3. 落点表（改什么，改哪里）

| 你要做什么 | 查哪 | 改哪里 |
|-----------|------|--------|
| 新建页面 | [page-layout.md](page-layout.md) §4.7 页面变体 | 复制骨架变体，改字段 |
| 加卡片 / 做数据展示 | [components/cards.md](components/cards.md) | 复制组件规格，按选型判据挑卡 |
| 改按钮 / 表格 / 弹窗 / 表单 | [components/general.md](components/general.md)、[data-display.md](components/data-display.md)、[overlays.md](components/overlays.md)、[form-controls.md](components/form-controls.md) | 全局覆盖改 `style.css` + `tokens.css` 的 `--el-*`；模块确需差异才写 `.<模块根类> :deep()` |
| 改颜色 / 字体 / 间距 / 圆角 / 阴影 / 动效 | [tokens.md](tokens.md) | `tokens.css` 的 T0 主 token；`--app-*` / `--el-*` 是兼容别名（= `var(原子)`），别名层不许再出现字面量 |
| 改页面布局 / 排查不可滚动 | [page-layout.md](page-layout.md) | 组件 `scoped CSS`（用 `var(--*)`） |
| 新增设计规则 | — | 先确认需求方明确提出；落地后同步 `tokens.md` + `tokens.css`（组件/版式再同步对应参考） |
| 想照抄某个旧写法 | [known-gaps.md](known-gaps.md) | 那两张表是"别照抄"清单 |

## 4. 取数与三态

页面取数统一三态，共享件见 [components/feedback.md](components/feedback.md)：

- 加载中 → `SkeletonCard`；取数失败 → `ErrorState`（带重试）；成功但为空 → `EmptyState`。
- **加载期间不得渲染空态**（假空态）；弹窗 / 抽屉内的原地异步操作才用 `v-loading`，表格加载走 `AppTable` 的 `loading`。
- 表格与分页只走共享 `AppTable` + `usePagination`（见 [components/data-display.md](components/data-display.md)）。

## 5. 验证与门禁

```bash
cd frontend && npm run lint:styles      # 样式硬门禁 G1–G5（颜色原子唯一 / 无纯色字面量 / 引用完整 / 阴影圆角动效 / 字号刻度）
cd frontend && npx vue-tsc --noEmit     # 类型
cd frontend && npx eslint src/          # 代码规范
```

- 只跑与改动直接相关的最小测试集；全量回归需先向用户申请。
- 工程门禁（布局裁剪 / 契约 / 可达性 / 四态）用 `vue-frontend-check` skill。
- 编码规范（Vue / TS / 文件组织 / 500 行上限）以 `frontend/AGENTS.md` 为准；本技能只管视觉与结构口径。

## 6. 交付前

过一遍 [../SKILL.md](../SKILL.md) 的「提交前自检」；交付说明里用一句话交代「采用了哪套既有默认」（哪个骨架变体 + 哪些共享件），供需求方否决或微调。

验收契约（改到对应层时对照）：`openspec/specs/frontend-l0-design-tokens`、`frontend-l2-page-region`、`frontend-l3-container`、`frontend-l3-content-block`、`frontend-l4-data-surface`、`frontend-l5-overlay`，以及 `frontend-doodle-*` 系列（卡片 / 按钮 / 表格 / 侧栏 / 子页导航）。
