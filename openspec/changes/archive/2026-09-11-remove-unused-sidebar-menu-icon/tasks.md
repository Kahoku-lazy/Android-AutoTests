## 1. 删除前判定

- [x] 1.1 全仓库复核引用 → `AnimatedMenuIcon` 仅 3 处（`AppSidebar.vue:12` 的 import、`frontend/AGENTS.md` 清单、`dev_docs/项目笔记/1.md:464`），且无 kebab 标签 `<animated-menu-icon>`、无 `:is="Animated…"`、无 `resolveComponent`、无测试引用、无 CSS 类引用；验证"无渲染点"成立
- [x] 1.2 git 历史定位成因 → `git show cc721d74` 显示唯一渲染行被删除、import 被保留；判定为**迁移遗留**而非"待启用"素材

## 2. 改动

- [x] 2.1 删除 `frontend/src/shared/components/AnimatedMenuIcon.vue`（247 行）；验证 `Test-Path` 为 False
- [x] 2.2 移除 `AppSidebar.vue` 的 `import AnimatedMenuIcon from './AnimatedMenuIcon.vue'`；验证该行消失且 `AnimatedMascot` 的 import（line 11）与渲染（line 227）保留
- [x] 2.3 `frontend/AGENTS.md` 侧边栏清单移除该行（4 条 → 3 条）；用 read 工具校验文件仍为正常 UTF-8 中文，未破坏其它章节

## 3. 门禁验证

- [x] 3.1 `frontend` 范围内搜索 `AnimatedMenuIcon` / `animated-menu` → **0 处**；`AnimatedMascot` 仍为 import + 渲染各 1 处
- [x] 3.2 前端类型检查 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`（workdir: frontend）→ 输出 50 行 / 35 条 TS 报错，与删除前**完全一致**，其中提及 `AppSidebar` / `Animated*` 的 **0 行**；判定未引入类型错误
- [x] 3.3 `git status --porcelain -- frontend/src/shared frontend/AGENTS.md` → 本变更恰好 3 项：`D AnimatedMenuIcon.vue`、`M AppSidebar.vue`、`M frontend/AGENTS.md`（同范围内的其余 M/D 为用户在途改动）
