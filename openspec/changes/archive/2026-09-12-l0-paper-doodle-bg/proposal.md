## Why

当前 L0 使用点阵纸纹，与 `temps/hand-drawn-doodle-sidebar.html` 的「暖白素描纸 + 稀疏 SVG 涂鸦」观感不一致；工作台内层还叠了一套点阵，视觉噪音更大。需要把平台背景收敛到原型口径，同时不破坏现有 L0「视口固定 + 内层滚动」策略。

## What Changes

- 去掉 L0 `body` 点阵，改为纯暖白纸面（对齐原型 `--paper: #fffef5`）
- 在主内容区（`.main-content`）增加一层 `pointer-events: none` 的稀疏 SVG 涂鸦装饰（星、咖啡渍环、波浪线等），内容层盖在上方
- 去掉 `.doc-page--fixed .doc-body` 上的第二套点阵，避免双纹理
- 同步更新设计令牌与文档口径：从「强制点阵纸纹」改为「暖白纸面 + 涂鸦装饰」
- 不改侧栏/顶栏结构，不改模块业务布局

## 关联文档

- UI 参考原型：`temps/hand-drawn-doodle-sidebar.html`（`bg-doodles` + `--paper`）
- 前端 L0 口径：`frontend/AGENTS.md`（视口 / 文档流）
- 主题技能约束：`.agents/skills/doodle-craft/references/layout.md` §4.2（本变更将改写「禁止纯色 / 强制点阵」条款）
- 无独立 PRD/ARCH 编号；属视觉主题对齐，不改业务接口

## Capabilities

### New Capabilities

- `frontend-l0-paper-doodle`: 平台 L0 纸面底色与主区涂鸦背景层的可见行为与约束

### Modified Capabilities

- （无；`openspec/specs/` 下暂无既有前端背景能力）

## Impact

- 前端样式：`frontend/src/style.css`、`frontend/src/shared/styles/tokens.css`、`frontend/src/App.vue`
- 新增共享装饰层（建议 `shared/components` 或等价静态层）
- 文档：`frontend/AGENTS.md`、`.agents/skills/doodle-craft/references/layout.md`（及必要时 DESIGN 相关口径）
- 不影响 API、鉴权、模块路由；登录页会跟随 L0 纸色变化
