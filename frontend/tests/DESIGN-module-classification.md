# 前端 Vitest 模块分类与报告增强 — 设计文档

> 日期：2026-08-13
> 状态：已评审通过
> 目标读者：后续所有模块的测试开发者、reviewer

## 背景与目标

登录、仪表盘两个模块已有 Vitest 用例，后续还有 devices / cases / runner 等更多模块要测。
现状问题：

1. Vitest UI 报告页只按 P0/P1 两栏混排，模块多了无法按模块浏览；
2. 没有"一键只跑某模块"的命令；
3. 没有全模块测试进度的总注册表；
4. UI 报告内容单薄（仅用例名 + 通过状态），无模块/测试点/结果的汇总视图。

目标：建立**模块 → 优先级**两级分类体系，让 UI 报告页、运行命令、静态 HTML 报告、
文档索引四处共享同一套分类，新增模块零配置。

---

## 1. 目录约定（维持现状，文档化）

```
frontend/tests/
  helpers/            # 通用挂载工具，不算模块
  reports/            # 报告产物，不算模块
  <module>/           # 模块目录（= src/modules/<name> 或 views 的模块名）
    p0/               # 必测 *.spec.ts
    p1/               # 建议测 *.spec.ts
    p2/README.md      # 仅登记不测项，不放用例
  PRIORITY_TEMPLATE.md
  README.md           # 总注册表（见 §5）
  run.mjs
  generate-html-report.mjs
```

**模块判据**：`tests/` 下一级目录含 `p0` 或 `p1` 子目录、且其中存在 `*.spec.ts`，才算模块。
`helpers/`、`reports/` 因此自动排除，无需维护白名单。

---

## 2. UI 报告页分栏：动态生成「模块/优先级」project

`frontend/vite.config.js` 的 `test.projects` 从静态两栏改为**启动时扫描生成**：

- 扫描 `frontend/tests/*/` 一级子目录；
- 对每个模块目录检查 `p0`、`p1` 子目录：**内含 `*.spec.ts` 才生成对应 project**（空目录不生成，避免 UI 出空栏）；
- project 定义（继承根配置）：

```js
{
  extends: true,
  test: {
    name: 'login/p0',            // 命名 = 目录路径风格，UI 侧栏按此显示
    include: ['tests/login/p0/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    css: false,
  },
}
```

- 当前效果：UI 侧栏出现 `dashboard/p0`、`dashboard/p1`、`login/p0`、`login/p1` 四栏，
  同模块相邻、按优先级排列；新增模块只建目录即自动出现；
- `p2` 只有 README、无 spec，不生成 project；
- include 路径用正斜杠拼接（Windows 兼容），模块名从目录名读取；
- 扫描代码放在 `isTest` 判断之后，不影响 `npm run dev` / build。

### 明确不做

- 不改 UI 主题、不引入额外分组插件——project 分栏是 Vitest UI 原生的分组单元；
- 不按模块拆多个 vite.config（一个根配置 + 动态 projects 已够）。

---

## 3. 运行命令：run.mjs 预设

`tests/run.mjs` 在现有 preset 基础上新增两个，共用同一套模块扫描逻辑（提取为 run.mjs 内部函数）：

```bash
node tests/run.mjs                # 全量（默认，行为不变）
node tests/run.mjs module login   # 只跑指定模块（= vitest run tests/login，含 p0+p1）
node tests/run.mjs prio p0        # 跨模块跑指定优先级：扫描后拼 --project login/p0 --project dashboard/p0 ...
node tests/run.mjs html           # 静态 HTML 报告（见 §7）
node tests/run.mjs all            # 终端 + junit + json + 按模块汇总打印（新增汇总）
node tests/run.mjs ui             # Vitest UI（不变）
```

- `prio` 显式拼接 `--project <module>/p0` 列表，**不依赖 `--project` 通配语法**（版本间有差异，避免踩坑）；
- `all` 模式跑完后解析 `tests/reports/report.json`，终端打印每模块：文件数 / 通过 / 失败 / 耗时；
- 原有 `verbose / junit / json / watch / ui / file` 预设保持行为不变。

`frontend/package.json` scripts 变更：

| script | 变更 |
|--------|------|
| `test:p0` | `vitest run --project P0` → `node tests/run.mjs prio p0` |
| `test:p1` | 同上 → `node tests/run.mjs prio p1` |
| `test:module` | 新增 → `node tests/run.mjs module` |
| `test:report:html` | 新增 → `node tests/run.mjs html` |
| 其余 | 不变 |

---

## 4. 用例命名规范（统一测试点表达）

报告的分组靠路径，测试点的表达靠命名。全平台统一：

```ts
describe('[P0] <被测单元>')    // composable / 组件 / 编排器名
it('<场景>：<预期>')            // 场景=操作或输入；预期=断言结果；多预期用「，」并列
```

规则：

1. 一条用例只测一个行为，场景与预期用全角「：」分隔；
2. **模块名不写进命名**——由文件路径 + project 分栏承载，避免冗余与搬迁改名成本；
3. 断言顺序与命名中预期顺序一致；
4. 反例：`it('测试登录')`（无场景无预期）、`it('登录成功, 写token, 跳转')`（半角逗号、无「：」）。

动作：审计现有 17 个 spec 文件（login 11 + dashboard 6），不合规用例名微调，断言不动。

---

## 5. 模块注册表：tests/README.md 重构为总注册表

结构：

1. 目录约定图（§1）；
2. **模块注册表**：平台全部前端模块，登记测试状态：

| 模块 | 目录 | 状态 | P0 文件 | P1 文件 | 说明 |
|------|------|------|---------|---------|------|
| dashboard | `tests/dashboard/` | ✅ P0+P1 | 2 | 4 | 数据编排/卡片/导航 |
| login | `tests/login/` | ✅ P0+P1 | 8 | 3 | 校验/流程/卡片 |
| devices | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| inspector | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| elements | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| cases | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| runner | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| reports | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| ai-assistant | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| workflow | — | ⬜ 未开始 | 0 | 0 | 待开测 |

（模块清单以 `frontend/src/router.js` 实际路由模块为准，实现期对照校正一次。）

3. 命令说明（§3 表）；
4. `PRIORITY_TEMPLATE.md` 的「新模块开测 Checklist」补两步：**登记注册表**、**核对命名规范**。

---

## 6. 静态 HTML 报告页（C）

### 6.1 生成链路

```
node tests/run.mjs html
  → vitest run --reporter=json --outputFile.json=tests/reports/report.json
  → node tests/generate-html-report.mjs（新增，纯 Node，无依赖）
  → tests/reports/html/index.html（自包含单文件：内联 CSS/JS，可直接分发/归档）
```

### 6.2 数据源（已实测 vitest 4.1.10 JSON 结构）

- 顶层：`numTotalTests` / `numPassedTests` / `numFailedTests` / `success` / `testResults[]`
- `testResults[].name`：文件**绝对路径**（如 `D:/.../tests/dashboard/p0/StatsCard.spec.ts`）
- `assertionResults[]`：`ancestorTitles[]`（describe 链）/ `fullName` / `title` / `status` / `duration` / `failureMessages[]`
- 读取用 `fs.readFileSync(path, 'utf8')`；**禁止用 PowerShell/Get-Content 当数据通道**（默认编码会乱码，实测已踩）

### 6.3 解析规则

- 模块与优先级：对 `testResults[].name` 正则 `tests[\\/]([^\\/]+)[\\/]p([01])[\\/]`；
  匹配不到的文件归入「未分类」分区（防御性兜底）；
- 测试点 = `fullName`（`[P0] 单元 场景：预期`），场景段 = 第一个「：」后的内容；
- 结果 = `status`（passed / failed / pending / todo），失败行内展示 `failureMessages` 首条。

### 6.4 页面结构

1. 顶部 KPI：总用例 / 通过 / 失败 / 失败率 + 模块数 + 生成时间；
2. 按模块分区（按模块名排序，模块内 P0 在前）：
   - 模块头：模块名 + P0/P1 各自统计（通过/失败/文件数）；
   - 展开后用例表列：**测试点（场景：预期）/ 结果 / 耗时 / 失败详情**；
3. 全量通过时顶部显示成功横幅；有失败时失败分区自动置顶展开。

### 6.5 视觉规范

遵循项目 `html-report` skill（animal-island-ui 设计规范，design token / 配色 / 组件样式），
实现期加载该 skill 的 references/PROMPT.md 后落代码。

### 明确不做（本期）

- 不做「测试步骤」流水列——vitest 无 step API，需 console 输出 + 自定义 reporter 采集，成本与侵入性不成比例；场景信息由用例名承载；
- 不做历史趋势 / 多次运行对比——报告是单次运行快照；
- 不引入外部 JS/CSS 依赖——单文件自包含。

---

## 7. 影响面清单

| 文件 | 改动 | 风险 |
|------|------|------|
| `frontend/vite.config.js` | 动态扫描生成 projects | 低（isTest 分支内） |
| `frontend/tests/run.mjs` | 新增 module/prio/html 预设 + all 汇总打印 | 低 |
| `frontend/tests/generate-html-report.mjs` | 新增生成器 | 低 |
| `frontend/package.json` | test:p0/p1 改走 run.mjs；新增 test:module / test:report:html | 低 |
| `frontend/tests/README.md` | 重构为总注册表 | 文档 |
| `frontend/tests/PRIORITY_TEMPLATE.md` | 命名规范节 + Checklist 补登记步骤 | 文档 |
| `tests/login/**` `tests/dashboard/**` | 仅命名微调，断言不动 | 极低 |

不改：`src/` 业务代码、`tests/helpers/`、`tests/reports/` 既有文件格式（junit.xml / report.json 内容格式不变）。

---

## 8. 成功标准（验收清单）

1. `npx vitest run` 全量 107 用例通过，数量与改造前一致；
2. UI 报告页左侧出现 `dashboard/p0` `dashboard/p1` `login/p0` `login/p1` 四栏，各自只含本模块本优先级用例；
3. `npm run test:p0` 只跑两个模块的 p0（30 条），`test:p1` 同理；
4. `node tests/run.mjs module login` 只跑 login（11 文件），`module dashboard` 只跑 dashboard（6 文件）；
5. `node tests/run.mjs html` 生成 `tests/reports/html/index.html`，浏览器打开：KPI 正确、模块分区正确、用例表中文不乱码、失败用例能展开看到失败信息；
6. `tests/README.md` 注册表登记全部平台模块（对照 router.js），dashboard/login 状态 ✅；
7. 命名审计完成：全部用例名符合「场景：预期」模板；
8. `npm run dev`、`npm run build` 不受 vite.config 改动影响。

---

## 9. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-13 | 初版：模块×优先级分栏 + 命令 + 注册表 + 命名规范 + HTML 报告 |
