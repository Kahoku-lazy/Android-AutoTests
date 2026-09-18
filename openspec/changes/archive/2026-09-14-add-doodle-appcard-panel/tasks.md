## 1. AppCard 钉板壳

- [x] 1.1 扩展 `AppCard.vue`：`tone` / `tilt` / `pin`（默认有图钉）；去掉依赖彩色顶条 class 作为唯一强调；验证：story/单测或目视虚线+硬阴影+图钉
- [x] 1.2 更新 `workbench-theme.css` 与 `style.css`：`.ac-card` 钉板规则；移除/停用 `.ac-card::before` 顶条；验证：报告页 AppCard 自动换皮
- [x] 1.3 收窄 `motion.css` 对 `.wb-shell .el-card` 的模糊抬升，避免钉板被盖成漂浮卡；验证：hover 为回正硬阴影

## 2. 仪表盘趋势

- [x] 2.1 `dashboard/index.vue` 四张趋势改为 `AppCard` + `sketchToneAt`/`sketchTiltAt` cycle；验证：无裸 el-card 趋势壳
- [x] 2.2 清理 `DashboardView.style.css` 中针对 el-card body 的旧实线圆角覆写；验证：布局网格仍正确

## 3. 文档与门禁

- [x] 3.1 更新 `frontend/AGENTS.md` AppCard 说明 + ECharts 硬编码例外；更新 doodle-craft `components.md` 钉板规格
- [x] 3.2 补/更 AppCard 相关单测（若有）；`cd frontend && npm run typecheck` 本变更文件无新错
