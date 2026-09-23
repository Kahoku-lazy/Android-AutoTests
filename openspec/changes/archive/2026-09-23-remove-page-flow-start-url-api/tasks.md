## 1. 前端起点收敛

- [x] 1.1 `types/workflow.ts`：`StartKind` 收敛为 `'app' | 'page'`，类型注释改为「StartNode: launch app / page-as-entry」。验证：`vue-tsc --noEmit` 报 3 条错误，全部是既有基线 `case-manager/components/ProjectTree.vue`，workflow 模块 0 条
- [x] 1.2 `stores/workflowStore.ts`：`setStartKind` 删除 url/api 分支、`start_url` / `start_api` 默认值写入、labelMap/statusMap 的 url/api 文案与函数上方注释；删除 `setStartUrl` / `setStartApi` 及其导出。验证：`grep start_url|start_api|setStartUrl|setStartApi frontend/` 命中 0
- [x] 1.3 `composables/useVueFlowAdapter.ts`：`PageFlowNodeData` 删除 `startUrl` / `startApi`；`startKind` 改为「非 `page` 一律归 `app`」归一化。验证：新增单测断言历史 `url` / `api` / 缺省三类都映射为 `app` 且数据里无 URL/API 字段，7/7 通过
- [x] 1.4 `components/vueflow/PageFlowNode.vue`：删除「URL」「API」按钮与两个 `.pf-pkg` 输入框，副文案条件收敛为 `startKind === 'page'`。验证：`grep startKind === 'url'|'api' frontend/` 命中 0
- [x] 1.5 `registry/nodeRegistry.ts`：起点注册项注释由「支持 4 种模式」改为「支持 2 种模式」。验证：与 1.1～1.4 的模式集合一致

## 2. 后端语义摘要同步

- [x] 2.1 `apps/workflow/semantics.py`：起点分支只读 `package_name`。验证：`grep start_url|start_api apps/` 命中 0；`python manage.py check` → System check identified no issues；`ruff check` All checks passed；`ruff format --check` 1 file already formatted

## 3. 测试

- [x] 3.1 新增 `frontend/tests/workflow/p0/start-node.spec.ts`（4 条属性契约 + 3 条适配层断言）。验证：`npx vitest run --project workflow/p0` → 7 passed
- [x] 3.2 后端语义摘要回归：仓库无 `tests/workflow` 目录，改以 `temps/semantics_start_probe.py` 直调 `semantics.build_graph_digest` —— 起点条目为 `{start_kind: 'app', package_name: 'com.example.app'}`，带 `start_url` / `start_api` 残留键的输入不产生对应输出键，断言全过

## 4. 门禁与验收

- [x] 4.1 前端门禁：`vue-tsc --noEmit`（3 条既有 ProjectTree 基线，0 新增）✅；`eslint src/`（0 error / 69 warning，全部既有）✅；`npm run lint:styles`（批 1/1b/2/3/4 全过，裸色存量清单未上升）✅；`vitest --project workflow/p0`（7 passed）✅。**偏离见 4.4**
- [x] 4.2 反向复核：`grep start_url|start_api|startUrl|startApi|setStartUrl|setStartApi` 在 `frontend/` 与 `apps/` 命中 **0**；`grep "'url'|'api'|打开 URL|调用 API|ApiNode"` 在 `frontend/src/modules/workflow` 命中 **0**。起点相关残留清零
- [ ] 4.3 真浏览器冒烟（Playwright）：登录 → `/workflow` → 打开含起点的页面流原型 → 核对起点模式区只剩两个按钮、「启动 App」下只有「包名」、切换后保存不报错。**未执行**（Playwright 同样需要 spawn 浏览器进程）
- [ ] 4.4 补齐 4.1 未能完成的两项：全量 `npx vitest run` 与 `npx vite build`。**本会话沙箱阻塞**：Vite/Vitest 通过 esbuild 子进程（管道 stdio）转译 `.vue` 与打包配置，受限沙箱下必现 `Error: spawn EPERM`；已按规程对同一命令各申请一次放宽沙箱，两次申请均无应答（单次阻塞满 10 分钟墙钟后中止），故不再重试。**已取得的部分证据**：用临时垫片跳过 Vite 的 `net use` 探测并以 `--pool=threads` 跑全量 → `Test Files 19 failed | 32 passed (51)`、`Tests 170 passed (170)`、**断言失败 0 条**；19 个失败文件全部是 spawn EPERM（import `.vue` 的 spec），与本变更无关。`vite build` 在**加载 vite.config.js 阶段**即 EPERM，尚未进入本项目源码编译
- [x] 4.5 `vue-frontend-check` 门禁（静态，范围 = 本次改动的 5 个源文件）：calibration §7 强制扫描 12 条命令全部执行；改动文件命中项均为**既有**（`nodeRegistry.ts` 节点色表＝已登记画布色例外、`PageFlowNode.vue` 既有样式间距、`useVueFlowAdapter` 的 `explainConnection` 本地结果对象非信封解包）；`@click` 4 处全在 `<button>` 上；本变更未触碰 api 层，六.1/6.2/6.3 协议对照 N/A

## 5. 归档

- [x] 5.1 `npx openspec validate remove-page-flow-start-url-api --strict` 通过（Change is valid）；`npx openspec archive remove-page-flow-start-url-api -y` 已执行 → 归档为 `openspec/changes/archive/2026-09-23-remove-page-flow-start-url-api/`，delta 已 sync 出主 spec `openspec/specs/page-flow-start-node/spec.md`（+3 requirements），`npx openspec validate --specs --strict` 56 passed / 0 failed。**归档时 4.3 / 4.4 仍未完成（12/15 tasks），经用户确认后由 `--yes` 放行——两项验证缺口保持未打勾**
- [x] 5.2 清理一次性探针（`temps/wf_start_kind_probe.py`、`temps/semantics_start_probe.py`）；保留 `temps/vite-net-use-shim.cjs` 与两份门禁日志供复跑

## 附：本会话实测结论（归档留痕）

| 项 | 命令 | 结果 |
|---|---|---|
| 存量数据 | `wf_documents` 全表遍历 | 2 篇文档 / 1 个起点 / `start_kind='page'`；**无 `url` / `api` 取值** → 无需数据迁移 |
| 类型 | `npx vue-tsc --noEmit` | 3 条错误，全部为既有 `ProjectTree.vue` 基线；workflow 0 条 |
| Lint | `npx eslint src/` | 0 error / 69 warning（全部既有） |
| 样式门禁 | `npm run lint:styles` | 批 1 / 1b / 2 / 3 / 4 全过 |
| 单测（新） | `npx vitest run --project workflow/p0` | 7 passed |
| 单测（全量） | `--pool=threads` + 垫片 | 32 / 51 文件通过，170 用例通过，**断言失败 0**；19 文件因 spawn EPERM 未收集 |
| 构建 | `npx vite build` | **未执行成功**（加载 vite.config.js 阶段 EPERM） |
| 后端 | `manage.py check` / `ruff check` / `ruff format --check` | 通过 |
| 后端语义 | `build_graph_digest` 直调 | 起点摘要有 `start_kind` / `package_name`，无 `start_url` / `start_api` |
| 残留复核 | 6 组 grep | 起点相关命中全部为 0 |
| 归档 | `npx openspec archive ... -y` | 归档至 `archive/2026-09-23-remove-page-flow-start-url-api/`；sync +3 requirements；`validate --specs --strict` 56 passed / 0 failed |
| 未跑 | 4.3 浏览器冒烟 / 4.4 全量 vitest + `vite build` | 沙箱阻塞，未执行（归档时经用户确认放行） |
