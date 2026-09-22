## 1. device-pool 测试对齐

- [x] 1.1 `tests/device-pool/p0/api.spec.ts`：11 条表项 `url` 补尾斜杠；验证：文件内 `url:` 共 11 条、全部以 `/` 结尾，与 `src/modules/device-pool/api.ts:6,17,23,27,31,35,39,43,47` 的 8 个端点逐一对得上（`/devices/scan` 3 条、`/devices/S1` 2 条各按同一 URL 重复）
- [x] 1.2 `tests/device-pool/p1/DevicePoolView.logic.spec.ts:104`：`toBe(2)` → `toBe(3)`；验证：`DEFAULT_PAGE_SIZE = 5`（`constants.ts:46`）→ `ceil(12 / 5) = 3`，同用例 106-110 行的收敛断言不变且通过
- [x] 1.3 `npx vitest run tests/dashboard tests/device-pool`；验证：**Test Files 14 passed (14) / Tests 85 passed (85)，exit 0**（此前同命令 5 文件红、17 例失败）

## 2. dashboard 测试对齐

- [x] 2.1 删除 `tests/dashboard/p1/ModuleNavigator.spec.ts`（被测组件 HEAD 已不存在：`git cat-file -e HEAD:frontend/src/modules/dashboard/components/ModuleNavigator.vue` 失败）；验证：`grep ModuleNavigator frontend/tests` 命中 0
- [x] 2.2 `tests/dashboard/p0/useDashboardStats.spec.ts`：fixture 去掉 `trend` / `reports` / `elements.breakdown` / `pass_rate` / `page_flows` / `test_cases` / `new_cases` / `new_cases_week`，补齐契约必填的 `ai_usage`（零值 `ZERO_AI_USAGE`）与 `charts.ai_tokens` / `charts.deepseek_cost`；4 个用例断言改为真实 DTO；验证：三类覆盖（逐字段映射 / 空对象回退 / 部分缺字段回退）都在，且 `grep -E "trend|reports|page_flows|new_cases|pass_rate"` 命中 0
- [x] 2.3 `tests/dashboard/p1/DashboardView.logic.spec.ts`：fixture 同上瘦身 + 补必填字段，`:121-122` 的 `elementBreakdown` 期望改为 1 类 `[android]`；验证：同用例 113-120 行的 `caseBreakdown` 四类断言不变且通过，「getElementItem 命中 web」用例（依赖 fixture 的 `type_breakdown` 数据）仍通过
- [x] 2.4 `tests/README.md` dashboard 行 P1 文件数 4→3、说明去掉「导航」；`tests/dashboard/p2/README.md` 不测行去掉 `ModuleNavigator`
- [x] 2.5 `npx vitest run tests/dashboard`；验证：**Test Files 5 passed (5) / Tests 40 passed (40)，exit 0**（此前 3 文件红 + 1 文件 0 用例可收集）

## 3. 门禁与归档

- [x] 3.1 `openspec validate fix-stale-frontend-specs --strict`；验证：`Change fix-stale-frontend-specs is valid`（含 skip_specs 说明，零 delta）
- [x] 3.2 `npx vitest run`（全量）；验证：**Test Files 46 passed (46) / Tests 235 passed (235)，exit 0**，日志内无 `FAIL` / `Timeout terminating`（基线：同 5 个文件红、17 例失败；全量 47 文件）
- [x] 3.3 `npx vue-tsc --noEmit`；验证：本单相关 spec 的类型报错**清零**（基线 `temps/vue-tsc-before.txt` 中 27 条分布在这 3 个 dashboard spec + ModuleNavigator）；残留 3 条全部在 `src/modules/case-manager/components/ProjectTree.vue:430-434`（别人在飞的改动，本单未碰）
- [x] 3.4 `npm run lint:styles`；验证：退出码 0（批 1 / 1b / 2 / 3 / 4 全通过）
- [x] 3.5 `npx vite build`；验证：退出码 0，`✓ built in 1m 12s`
- [x] 3.6 归档到 `openspec/changes/archive/2026-09-21-fix-stale-frontend-specs/`；验证：`openspec/changes/` 下不再有 `fix-stale-frontend-specs`

## 4. 实施中的发现

- 4.1 只删多余字段后 `vue-tsc` 才暴露被掩盖的必填缺失：`TS2353`（多余属性）与 `TS2741`（缺 `ai_usage`）/ `TS2739`（缺 `charts.ai_tokens`、`charts.deepseek_cost`）分两轮才报全。第一轮只补 `charts` 子键时 `ai_usage` 仍不报，补完 `charts` 后才出现——「一次报全」的假设不成立，必须逐轮跑到干净。
- 4.2 「部分字段缺失」用例的 `as DashboardRawData` 单次断言已不合法（TS2352：缺 10 个必填属性、重叠不足），改为 `as unknown as DashboardRawData` 并加注释说明「故意只给两个分区」——这是测试**有意**注入残缺输入的表达方式，不是掩盖类型错误。
- 4.3 `tests/dashboard/p2/README.md:9` 仍写「9 个子组件」，而 `src/modules/dashboard/components/` 现只有 5 个组件；不由本单改动引起，作为伴随发现登记、未改。
