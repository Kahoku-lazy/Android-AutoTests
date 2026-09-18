## 1. 共享 SketchCard

- [x] 1.1 新增 `frontend/src/shared/helpers/sketchCard.ts`：`sketchToneAt` / `sketchTiltAt`（八 `--c-*`、固定倾角表）；新增 `SketchCard.vue`（虚线壳、图标方块、title/desc/meta、可选删除、键盘、reduced-motion）；验证：单测覆盖壳类名、空描述、删除不冒泡、Enter 进入
- [x] 1.2 新增 `frontend/tests/shared/p0/SketchCard.spec.ts`；验证：vitest 相关用例通过

## 2. 三处列表替换

- [x] 2.1 `case-manager/ProjectList.vue` 用 SketchCard + cycle；去掉 `__accent` 私有样式；验证：进入/删除逻辑不变
- [x] 2.2 `element-locator/ProjectList.vue` 用 SketchCard + cycle、无删除；去掉父级 nth-child transform 与 `__accent`；验证：进入 `code` 工作台不变
- [x] 2.3 `workflow/PrototypeList.vue` 用 SketchCard + cycle；去掉 `__accent` 私有样式；验证：进入/删除逻辑不变

## 3. 文档与门禁

- [x] 3.1 更新 doodle-craft `components.md` 与 `frontend/AGENTS.md` SketchCard 条目
- [x] 3.2 `cd frontend && npm run typecheck`；本变更文件无新 TS 错误
