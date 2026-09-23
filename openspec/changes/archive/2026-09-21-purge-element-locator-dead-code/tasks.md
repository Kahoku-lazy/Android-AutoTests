## 1. `api.ts` 导出面收敛（46 → 18）

- [x] 1.1 记录删除基线：列出 `api.ts` 现存的 46 个 `export function`，逐个在 `frontend/src` 检索得到消费者文件清单；验证：输出 46 行清单，其中 26 行消费者清单为空（仅命中 `api.ts` 自身），作为后续删除的依据
- [x] 1.2 删除遗留 Pages / Elements / Flows 共 10 个导出：`apiPages`、`apiUpdatePage`、`apiFlows`、`apiCreateFlow`、`apiDeleteFlow`、`apiGetPageElements`、`apiAddElementToPage`、`apiBatchAddElementsToPage`、`apiClearAll`、`apiBatchMovePages`；验证：`frontend/src` 内逐个检索命中 0
- [x] 1.3 删除遗留 Web 元素与 Web 分组共 7 个导出：`apiListWebElements`、`apiBatchImportWebElements`、`apiListWebGroups`、`apiCreateWebGroup`、`apiUpdateWebGroup`、`apiDeleteWebGroup`、`apiBatchMoveWebGroups`；验证：`frontend/src` 内逐个检索命中 0
- [x] 1.4 删除遗留 API 分组与端点列表共 6 个导出：`apiListApiGroups`、`apiCreateApiGroup`、`apiUpdateApiGroup`、`apiDeleteApiGroup`、`apiBatchMoveApiGroups`、`apiListApiEndpoints`；验证：`frontend/src` 内逐个检索命中 0
- [x] 1.5 删除遗留 Web 流共 3 个导出：`apiListWebFlows`、`apiCreateWebFlow`、`apiDeleteWebFlow`；验证：`frontend/src` 内逐个检索命中 0
- [x] 1.6 删除传递性死亡的 2 个导出 `moveLocatorItem`、`batchDeleteLocatorFiles`（在第 2 组删除其唯一调用方之后执行）；验证：全仓检索两名字命中 0，且 `api.ts` 中 `export function` 计数为 18
- [x] 1.7 收敛分组注释：删除因上述删除而**实际变空**的分组标题（`── Flows（router）──` / `── Web group management … ──` / `── API group management … ──` / `── Web page flows ──`；原任务括号里多列了 `── Pages ──` / `── Elements ──` / `── Element Manager … ──`，这三组仍有存活导出，标题保留），把首个分组标题里的 `move` 去掉，并同步更新文件头那段因本次删除而失真的资源清单注释；验证：`api.ts` 内不存在下方零导出的分组标题，且每个保留的分组标题下至少有 1 个导出

## 2. `useLocatorTree` 收敛

- [x] 2.1 删除 `removeFiles` 的定义与 `return` 中的暴露项；验证：`frontend/src` 内检索 `removeFiles` 命中 0
- [x] 2.2 删除 `moveTreeItem` 的定义与 `return` 中的暴露项；验证：`frontend/src/modules/element-locator` 内检索 `moveTreeItem` 命中 0，且 `frontend/src/modules/case-manager/composables/useProjectTree.ts` 中的同名方法未被改动
- [x] 2.3 清理随之失效的 import：从 `useLocatorTree.ts` 的 import 列表移除 `batchDeleteLocatorFiles`、`moveLocatorItem`；验证：该文件 import 列表与函数体内实际使用逐一对应，`npm run typecheck` 不出现未使用导入报错

## 3. 编译门槛（在改测试之前确认源码收敛干净）

- [x] 3.1 `npm run typecheck`（**验收口径已修订，见 3.1a**）；验证：与 element-locator 相关的 error = 0，且错误集合不新增
- [x] 3.1a 修订依据留痕：改动后共 30 个 error，全部落在 `tests/dashboard/p0/useDashboardStats.spec.ts`(12) / `tests/dashboard/p1/DashboardView.logic.spec.ts`(8) / `tests/dashboard/p1/ModuleNavigator.spec.ts`(7) / `src/modules/case-manager/components/ProjectTree.vue`(3)；这 4 个文件经检索均不 import element-locator，且无一条 error 提及 element-locator、已删符号或 device-inspector（另一个消费者）。故属改动前既有错误（工作区处于其他模块在途重构中），「退出码 0」在本变更范围内不可达，口径改为「本模块相关 error = 0 且不新增」
- [x] 3.2 `npx vite build`；验证：退出码 0，`✓ built in 54.56s`（受限沙箱下 esbuild 子进程管道 EPERM，需 `danger-full-access`；产物 `frontend/dist/` 已被 `.gitignore:60` 忽略）

## 4. `api.spec.ts` 重写为 18 个存活函数的用例

- [x] 4.1 重写 `cases` 表为 11 个沿用用例，路径改为带尾斜杠的 router 形式，并删除已不存在的 `/create` 断言：`apiPageItems`、`apiUpdateElement`、`apiGetPages`、`apiCreatePage`、`apiDeletePage`、`apiCreateWebElement`、`apiUpdateWebElement`、`apiDeleteWebElement`、`apiCreateApiEndpoint`、`apiUpdateApiEndpoint`、`apiDeleteApiEndpoint`；验证：11 条的 url 与 `api.ts` 实际调用字面量逐字符一致
- [x] 4.2 新增 7 个项目化函数用例：`listLocatorProjects`、`getLocatorProjectTree`、`createLocatorDirectory`、`updateLocatorDirectory`、`deleteLocatorDirectory`、`apiGetWebElement`、`apiGetApiEndpoint`；验证：`api.ts` 的 18 个导出与 `cases` 表覆盖的名字集合完全相等（双向差集为空）
- [x] 4.3 确认用例不引用已删导出；验证：在 `frontend/tests/element-locator` 内检索 26+2 个已删名字命中 0
- [x] 4.4 运行该 spec（受限沙箱下需 `danger-full-access`，否则 Node 子进程管道 EPERM 无法启动）；验证：`npx vitest run tests/element-locator` 输出 18 passed / 0 failed

## 5. Python 守护调用面下限重登记

- [x] 5.1 记录基线并实测 N：**N = 111**（由守护失败文案直接读出），对照原登记下限 130（注释原记实测 136）。顺序偏差留痕：本任务排在源码删除之后，未能「先跑确认改动前通过」；等价证据是失败集恰为 1 个（`test_scanner_finds_the_expected_volume`），其余 6 个（含四面的 resolve 断言）全部通过 —— 说明本次删除未引入任何尾斜杠或路由解析违规，而原下限 130 < 原实测 136 必然通过
- [x] 5.2 把 `MIN_PER_SURFACE["frontend"]` 重登记为 `floor(N * 0.95)`，并在注释中写明本次下调依据（`api.ts` 死代码清退删除 28 个调用点，非扫描器退化）；验证：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 全绿
- [x] 5.3 确认只动了这一个面的下限；验证：`git diff tests/graybox/unit/test_api_path_callers.py` 仅含 `frontend` 下限数值与该注释，`tests` / `yaml` / `catalog` 三个面与 `EXCEPTIONS` 清单未被改动

## 6. 门禁与验收

- [x] 6.1 `python -m pytest tests/graybox/unit -q`（**验收口径已修订，见 6.1a**）；验证：本变更相关测试全绿，且 0 个失败/错误与本变更相关
- [x] 6.1a 修订依据留痕：全量套件 `7 failed, 289 passed, 11 errors`。7 个 failed **全部**在 `tests/graybox/unit/test_ai_engine_config.py`（AI 供应商构造，与本变更无关）；11 个 errors **全部**是 `PermissionError`（`test_env_loader.py` / `test_kb_files.py`，沙箱禁止写工作区外路径所致）。`test_api_path_callers.py` 整体落在 289 passed 内，即第 5 组重登记后的守护在完整套件中通过。故「全绿」受既有失败与沙箱限制所限不可达，口径改为「本变更相关测试全绿、无相关失败」
- [x] 6.2 `npm run lint:styles`（`node tests/check-style-gates.mjs`）；验证：退出码 0，本模块零违规
- [x] 6.3 逐项静态复验（结果：全仓排除 `node_modules`/`dist`/`__pycache__` 后共 100 处命中，全部落在三类**预期留痕**文件上：`frontend/src/modules/case-manager/**` 的 4 处 `moveTreeItem`（该模块自己的同名方法，任务 2.2 要求不动）、两份历史计划文档（D7 决定不改）、以及本变更自身的 proposal/design/tasks 工件；`frontend/src/modules/element-locator/**` 与 `tests/**` 命中 0）：对第 1 组 26+2 个已删标识符与 `removeFiles` / `moveTreeItem` 做全仓检索（排除 `node_modules` / `dist`）；验证：全部命中 0，并输出命中清单
- [x] 6.4 存活面复核（结果：18/18 每个均有 ≥1 个生产消费者；`apiGetPages` 的消费者仍是 device-inspector 的 `SavedPagePicker.vue` / `SaveToElementsDialog.vue`）：18 个导出每个至少 1 个生产消费者；验证：输出 18 行「导出名 → 消费者文件」清单，无空行
- [x] 6.5 `git diff --stat` 与 `proposal.md` 的 Impact 段逐文件核对；验证：恰好 4 个文件（`api.ts`、`useLocatorTree.ts`、`api.spec.ts`、`test_api_path_callers.py`），不含 `apps/**`、`shared/**`、`tokens.css`
- [x] 6.6 观感零变化核对；验证：改动文件清单不含任何 `.vue`，`git diff` 中无模板与样式改动
