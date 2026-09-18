## 1. 结构微调（保留文案与 SVG）

- [x] 1.1 在 `AppSidebar.vue` 品牌区增加 `.brand-mark`（保留「AI」「自动化测试平台」文案），验证：展开态仍可读原品牌文案
- [x] 1.2 为导航 Lucide 图标增加方盒包装类（如 `.nav-ico`），不改 `data-lucide` / icon 名，验证：各入口 SVG 仍按原 icon 渲染

## 2. 侧栏 chrome 与导航样式

- [x] 2.1 改 `AppSidebar.style.css`：侧栏底为暖纸色、右侧改为墨色虚线分隔；品牌区/底栏虚线分隔，验证：无粗实线挡板观感
- [x] 2.2 实现 nav hover（浅黄 + 微旋转）与 active（黄底 + 虚线描边 + `3px 3px 0` 模块色偏移阴影），验证：多模块切换 active 阴影色随 `--mod-color` 变化
- [x] 2.3 图标方盒：白底、墨色描边、主题色协调；折叠态仍可识别 active，验证：折叠/展开切换正常

## 3. 行为回归与文档

- [x] 3.1 确认折叠、拖宽、账号菜单、退出仍可用且 `data-testid` 保留，验证：手动点一遍关键交互
- [x] 3.2 如 `frontend/AGENTS.md` / doodle-craft layout 有侧栏实线/书签条口径，同步为虚线黄底板描述，验证：文档与实现一致

## 4. 验收

- [x] 4.1 对照 `temps/hand-drawn-doodle-sidebar.html` 目视侧栏，并跑 `cd frontend && npm run typecheck`；验证：风格接近模板、文案/SVG 保留；typecheck 无本变更新增报错
