# 前端 Vitest 模块分类与报告增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立「模块 → 优先级」两级测试分类：Vitest UI 按模块分栏、run.mjs 一键跑模块/优先级、静态 HTML 报告按模块分组、README 总注册表，并统一用例命名规范。

**Architecture:** 单一扫描逻辑（`tests/module-scan.mjs`）供 vite.config 与 run.mjs 共用，避免清单漂移；HTML 报告复用 vitest JSON reporter 输出，生成器为纯 Node 无依赖单文件。

**Tech Stack:** Node ≥20（ESM）、Vitest 4.1.10（projects / JSON reporter）、Vite 5、纯 JS 工具脚本（无新 npm 依赖）

**规格来源：** [DESIGN-module-classification.md](./DESIGN-module-classification.md) — 本计划中所有"验收"条目编号对应其 §8。

## Global Constraints

- **提交纪律（重要）**：本仓库工作区有大量未提交改动，且 index 中有他人/先前的 staged 文件。每个 commit **只 add 本任务涉及的文件**，用 pathspec 提交：`git commit -m "..." -- <file1> <file2>`。禁止 `git commit -am`、禁止不带 `--` 的整仓提交（历史上曾误提交 staged 文件）。
- pre-commit hook 会自动 stash 未 staged 文件并跑 ruff，属正常现象。
- 所有命令在 `frontend/` 目录下运行（另有说明除外）。
- Commit message 用 Conventional Commits，本计划统一 `test:` 前缀。
- project 命名格式固定为 `<module>/<prio>`（如 `login/p0`）；include 路径必须用正斜杠拼接。
- 不修改 `src/` 业务代码；`tests/helpers/`、`tests/reports/` 既有文件格式（junit.xml / report.json 内容）不变。
- 新增 npm script 命名与现有对齐：`test:module`、`test:report:html`。
- 设计文档 §8 八条验收是终验清单，逐条过。

---

### Task 1: module-scan.mjs — 模块扫描共享逻辑

**Files:**
- Create: `frontend/tests/module-scan.mjs`

**Interfaces:**
- Produces: `scanModules(): Array<{ name: string, prios: Array<'p0'|'p1'> }>`（按 name 升序）；`listProjects(): string[]`（形如 `['dashboard/p0', 'dashboard/p1', 'login/p0', 'login/p1']`）
- Consumes: 无

- [ ] **Step 1: 创建扫描模块**

完整文件内容：

```js
/**
 * 测试模块扫描 — vite.config.js 与 run.mjs 共用的模块清单来源
 * 模块判据：tests/ 下一级目录，含 p0/p1 子目录且其中存在 *.spec|*.test 文件。
 * helpers/、reports/ 因无 p0/p1 自动排除，无需维护白名单。
 */
import { existsSync, readdirSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const TESTS_DIR = dirname(fileURLToPath(import.meta.url))
const PRIORITIES = ["p0", "p1"]
const SPEC_RE = /\.(test|spec)\.(js|ts)$/

export function scanModules() {
  const modules = []
  for (const entry of readdirSync(TESTS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const prios = []
    for (const prio of PRIORITIES) {
      const dir = join(TESTS_DIR, entry.name, prio)
      if (existsSync(dir) && readdirSync(dir).some((f) => SPEC_RE.test(f))) {
        prios.push(prio)
      }
    }
    if (prios.length) modules.push({ name: entry.name, prios })
  }
  return modules.sort((a, b) => a.name.localeCompare(b.name))
}

export function listProjects() {
  return scanModules().flatMap((m) => m.prios.map((p) => `${m.name}/${p}`))
}
```

- [ ] **Step 2: 验证扫描结果**

Run（frontend 目录）:
```bash
node -e "import('./tests/module-scan.mjs').then(m => console.log(JSON.stringify(m.scanModules()), '|', m.listProjects().join(' ')))"
```

Expected（顺序与内容完全一致）:
```
[{"name":"dashboard","prios":["p0","p1"]},{"name":"login","prios":["p0","p1"]}] | dashboard/p0 dashboard/p1 login/p0 login/p1
```

- [ ] **Step 3: Commit**

```bash
git add frontend/tests/module-scan.mjs
git commit -m "test: 新增模块扫描共享逻辑 module-scan.mjs" -- frontend/tests/module-scan.mjs
```

---

### Task 2: vite.config.js 接入 — UI 报告页按模块分栏

**Files:**
- Modify: `frontend/vite.config.js`（import 区 + test 块）

**Interfaces:**
- Consumes: `scanModules` from `./tests/module-scan.mjs`（Task 1）
- Produces: vitest projects 命名 `login/p0`、`login/p1`、`dashboard/p0`、`dashboard/p1`（Task 3 的 `--project` 引用、验收 §8.2 依赖）

- [ ] **Step 1: 添加 import**

在 `frontend/vite.config.js` 顶部 import 区（`node:url` import 之后）加一行：

```js
import { scanModules } from './tests/module-scan.mjs'
```

- [ ] **Step 2: 替换 test 块为动态生成**

将现有 `test: { projects: [...] }` 整块（含 `// Vitest UI 按 project 分栏：P0 / P1（P2 故意无用例）` 注释起的静态两栏）替换为：

```js
  test: {
    // Vitest UI 按 project 分栏：每模块 × 优先级（login/p0、login/p1…），
    // 由 module-scan.mjs 扫描 tests/ 生成，新增模块零配置
    projects: scanModules().flatMap((m) =>
      m.prios.map((prio) => ({
        extends: true,
        test: {
          name: `${m.name}/${prio}`,
          include: [`tests/${m.name}/${prio}/**/*.{test,spec}.{js,ts}`],
          environment: 'jsdom',
          css: false,
        },
      })),
    ),
  },
```

- [ ] **Step 3: 验证全量运行与分栏过滤**

Run:
```bash
npx vitest run
```

Expected: `Test Files 17 passed (17)`、`Tests 107 passed (107)`，数量与改造前一致（验收 §8.1）。

Run:
```bash
npx vitest run --project login/p0
```

Expected: 只跑 8 个 login/p0 文件，全部通过，输出中不出现 dashboard 或 p1 文件。

Run:
```bash
npx vitest run --project dashboard/p1
```

Expected: 只跑 4 个 dashboard/p1 文件，全部通过。

- [ ] **Step 4: Commit**

```bash
git add frontend/vite.config.js
git commit -m "test: Vitest 按模块×优先级动态生成 project 分栏" -- frontend/vite.config.js
```

---

### Task 3: run.mjs module/prio 预设 + package.json scripts

**Files:**
- Modify: `frontend/tests/run.mjs`
- Modify: `frontend/package.json`（test:p0 / test:p1 两行 + 新增 test:module）

**Interfaces:**
- Consumes: `scanModules` / `listProjects` from `./module-scan.mjs`（Task 1）
- Produces: `node tests/run.mjs module <name>`（未知名报错并列出可用）、`node tests/run.mjs prio <p0|p1>`；npm scripts `test:p0` `test:p1` `test:module`（Task 8 终验引用）

- [ ] **Step 1: 重写 run.mjs 的预设处理**

将 `frontend/tests/run.mjs` 中 `const mode = ...` 至 `process.exit(result.status ?? 1)` 之间的预设逻辑重写。完整替换后文件如下（保留文件头注释与 reportsDir、mkdirSync 逻辑，更新用法注释）：

```js
#!/usr/bin/env node
/**
 * Vitest 运行入口（报告输出到 tests/reports/）
 *
 * 用法（在 frontend 目录）:
 *   node tests/run.mjs                  # 默认跑全部
 *   node tests/run.mjs module login     # 只跑指定模块（p0+p1）
 *   node tests/run.mjs prio p0          # 跨模块跑指定优先级
 *   node tests/run.mjs file             # 只跑指定文件
 *   node tests/run.mjs verbose          # 终端详细输出
 *   node tests/run.mjs junit            # 生成 JUnit XML
 *   node tests/run.mjs json             # 生成 JSON 报告
 *   node tests/run.mjs all              # 终端 + JUnit + JSON
 *   node tests/run.mjs watch            # 监听模式
 *   node tests/run.mjs ui               # Vitest UI（需 @vitest/ui）
 *
 * 也可传文件路径：
 *   node tests/run.mjs junit tests/login-form.demo.spec.ts
 */
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { listProjects, scanModules } from './module-scan.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendRoot = join(__dirname, '..')
const reportsDir = join(__dirname, 'reports')

mkdirSync(reportsDir, { recursive: true })

const mode = process.argv[2] || 'default'
const extraArgs = process.argv.slice(3)

const presets = {
  default: ['run', ...extraArgs],
  file: ['run', ...extraArgs],
  verbose: ['run', '--reporter=verbose', ...extraArgs],
  junit: [
    'run',
    '--reporter=default',
    '--reporter=junit',
    `--outputFile.junit=${join(reportsDir, 'junit.xml')}`,
    ...extraArgs,
  ],
  json: [
    'run',
    '--reporter=default',
    '--reporter=json',
    `--outputFile.json=${join(reportsDir, 'report.json')}`,
    ...extraArgs,
  ],
  all: [
    'run',
    '--reporter=default',
    '--reporter=junit',
    '--reporter=json',
    `--outputFile.junit=${join(reportsDir, 'junit.xml')}`,
    `--outputFile.json=${join(reportsDir, 'report.json')}`,
    ...extraArgs,
  ],
  watch: [...extraArgs],
  ui: ['--ui', ...extraArgs],
}

function presetsFor(mode) {
  switch (mode) {
    case 'module': {
      const moduleName = extraArgs[0]
      const valid = scanModules().map((m) => m.name)
      if (!moduleName || !valid.includes(moduleName)) {
        console.error(`未知模块: ${moduleName}`)
        console.error(`可用: ${valid.join(', ')}`)
        process.exit(1)
      }
      return ['run', `tests/${moduleName}`, ...extraArgs.slice(1)]
    }
    case 'prio': {
      const prio = extraArgs[0]
      if (!['p0', 'p1'].includes(prio)) {
        console.error(`未知优先级: ${prio}（可用: p0, p1）`)
        process.exit(1)
      }
      const projects = listProjects().filter((p) => p.endsWith(`/${prio}`))
      return ['run', ...projects.flatMap((p) => ['--project', p]), ...extraArgs.slice(1)]
    }
    default:
      if (!(mode in presets)) {
        console.error(`未知模式: ${mode}`)
        console.error(`可用: ${Object.keys(presets).join(', ')}, module, prio`)
        process.exit(1)
      }
      return presets[mode]
  }
}

const args = presetsFor(mode)
console.log(`> vitest ${args.join(' ')}`)

const result = spawnSync('npx', ['vitest', ...args], {
  cwd: frontendRoot,
  stdio: 'inherit',
  shell: true,
})

if (['junit', 'json', 'all'].includes(mode)) {
  console.log(`\n报告目录: ${reportsDir}`)
}

process.exit(result.status ?? 1)
```

- [ ] **Step 2: 更新 package.json 三个 script**

`frontend/package.json` 的 scripts 中：

- `"test:p0": "vitest run --project P0"` → `"test:p0": "node tests/run.mjs prio p0"`
- `"test:p1": "vitest run --project P1"` → `"test:p1": "node tests/run.mjs prio p1"`
- 在 `test:p1` 下一行新增 `"test:module": "node tests/run.mjs module"`

- [ ] **Step 3: 验证 module 预设**

Run:
```bash
node tests/run.mjs module dashboard
```

Expected: 只跑 6 个 dashboard 文件（p0 2 + p1 4），全部通过；输出以 `> vitest run tests/dashboard` 开头。

Run:
```bash
node tests/run.mjs module nosuch
```

Expected: 打印 `未知模块: nosuch` 与 `可用: dashboard, login`，exit code 1。

- [ ] **Step 4: 验证 prio 预设与 npm scripts**

Run:
```bash
npm run test:p0
```

Expected: 只跑 p0 项目（10 个文件：login 8 + dashboard 2，共 69 条用例 = login 47 + dashboard 22），全部通过，输出中无任何 p1 文件（验收 §8.3）。

Run:
```bash
npm run test:module -- login
```

Expected: 只跑 11 个 login 文件，全部通过。

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/run.mjs frontend/package.json
git commit -m "test: run.mjs 新增 module/prio 预设，scripts 改走 run.mjs" -- frontend/tests/run.mjs frontend/package.json
```

---

### Task 4: generate-html-report.mjs — 静态 HTML 报告生成器

**Files:**
- Create: `frontend/tests/generate-html-report.mjs`

**Interfaces:**
- Produces: `parseReport(jsonPath): Object`（原样解析 JSON 文件）；`buildSummary(report): { kpi: {total, passed, failed, modules}, modules: [{name, p0: {files, total, passed, failed, duration}, p1: {...}}], unclassified: {files, total, passed, failed} }`；`renderHtml(summary): string`；`generateReport(inputPath, outputPath): void`
- Consumes: vitest 4.1.10 JSON reporter 结构（`testResults[].name` 绝对路径、`assertionResults[]` 含 `ancestorTitles/fullName/title/status/duration/failureMessages`）；Task 5 复用 `parseReport`/`buildSummary`/`generateReport`

- [ ] **Step 1: 阅读 html-report skill 规范（必做）**

按设计 §6.5，先执行 Skill `html-report`，读取 `references/PROMPT.md` 获取 animal-island-ui 的 design token（主色、背景、卡片、圆角、阴影、字体）。下面 Step 3 模板的 CSS 变量按该规范取值；若 skill 中 token 名与此处不同，只改 CSS 变量值，不改 HTML 结构。

- [ ] **Step 2: 编写生成器**

完整文件内容：

```js
#!/usr/bin/env node
/**
 * 静态 HTML 测试报告生成器 — 解析 vitest JSON reporter 输出，按模块分组渲染。
 * 纯 Node 无依赖，产物为自包含单文件 HTML（内联 CSS，可直接分发）。
 *
 * 用法（在 frontend 目录）:
 *   node tests/generate-html-report.mjs [input.json] [output.html]
 *   默认: input=tests/reports/report.json, output=tests/reports/html/index.html
 *
 * 注意: 必须用 fs.readFileSync(path, 'utf8') 读取；PowerShell Get-Content 默认编码会乱码。
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const __dirname = dirname(fileURLToPath(import.meta.url))
const DEFAULT_INPUT = join(__dirname, "reports", "report.json")
const DEFAULT_OUTPUT = join(__dirname, "reports", "html", "index.html")

const MODULE_RE = /tests[\\/]([^\\/]+)[\\/]p([01])[\\/]/
const STATUS_LABEL = { passed: "通过", failed: "失败", pending: "跳过", todo: "待办" }

export function parseReport(jsonPath) {
  return JSON.parse(readFileSync(jsonPath, "utf8"))
}

export function buildSummary(report) {
  const modules = new Map()
  let unclassified = { files: 0, total: 0, passed: 0, failed: 0 }

  for (const file of report.testResults ?? []) {
    const m = MODULE_RE.exec(file.name ?? "")
    const assertions = file.assertionResults ?? []
    const total = assertions.length
    const passed = assertions.filter((a) => a.status === "passed").length
    const failed = total - passed
    const duration = assertions.reduce((s, a) => s + (a.duration ?? 0), 0)

    let entry
    if (m) {
      const [_, name, prio] = m
      if (!modules.has(name)) {
        modules.set(name, { name, p0: { files: 0, total: 0, passed: 0, failed: 0, duration: 0 }, p1: { files: 0, total: 0, passed: 0, failed: 0, duration: 0 } })
      }
      entry = modules.get(name)[prio]
    } else {
      entry = unclassified
    }
    entry.files += 1
    entry.total += total
    entry.passed += passed
    entry.failed += failed
    entry.duration += duration
  }

  return {
    kpi: {
      total: report.numTotalTests ?? 0,
      passed: report.numPassedTests ?? 0,
      failed: report.numFailedTests ?? 0,
      modules: modules.size,
    },
    modules: [...modules.values()].sort((a, b) => a.name.localeCompare(b.name)),
    unclassified,
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]))
}

function prioSection(prio, stat, files) {
  if (!stat.files) return ""
  const rows = files
    .filter((f) => MODULE_RE.exec(f.name)?.[2] === prio)
    .flatMap((f) =>
      (f.assertionResults ?? []).map((a) => {
        const failed = a.status === "failed"
        const msg = failed ? (a.failureMessages?.[0] ?? "").split("\n").slice(0, 3).map(esc).join("<br>") : ""
        return `<tr class="${failed ? "row-failed" : ""}">
          <td class="td-name" title="${esc(a.fullName)}">${esc(a.title)}</td>
          <td class="td-file">${esc((f.name ?? "").split(/[\\/]/).pop())}</td>
          <td class="td-status status-${a.status}">${STATUS_LABEL[a.status] ?? a.status}</td>
          <td class="td-duration">${(a.duration ?? 0).toFixed(0)}ms</td>
          <td class="td-msg">${msg}</td>
        </tr>`
      }),
    )
    .join("")
  return `<section class="prio">
    <h4>${prio.toUpperCase()} — ${stat.files} 文件 · ${stat.total} 用例 · 通过 ${stat.passed} · 失败 ${stat.failed}</h4>
    <table><thead><tr><th>测试点（场景：预期）</th><th>文件</th><th>结果</th><th>耗时</th><th>失败详情</th></tr></thead>
    <tbody>${rows}</tbody></table>
  </section>`
}

export function renderHtml(summary) {
  const { kpi } = summary
  const passRate = kpi.total ? Math.round((kpi.passed / kpi.total) * 1000) / 10 : 100
  const moduleSections = summary.modules
    .map((m) => {
      const files = summaryFilesForModule(m.name)
      return `<section class="module">
        <h3>${esc(m.name)}</h3>
        ${prioSection("p0", m.p0, files)}
        ${prioSection("p1", m.p1, files)}
      </section>`
    })
    .join("")
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>前端测试报告</title>
<style>
:root{--bg:#faf7f2;--card:#fff;--ink:#1e1e24;--muted:#8a8a94;--ok:#2f9e6e;--fail:#d64545;--line:#e8e2d8;--accent:#4ecdc4}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:14px}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--muted);margin-bottom:16px}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.kpi{background:var(--card);border:1.5px solid var(--line);border-radius:8px;padding:10px 16px;min-width:110px}
.kpi b{display:block;font-size:22px}
.kpi span{color:var(--muted);font-size:12px}
.kpi.fail b{color:var(--fail)}
.module{background:var(--card);border:1.5px solid var(--line);border-radius:10px;padding:14px 18px;margin-bottom:16px}
.module h3{border-left:4px solid var(--accent);padding-left:8px;margin:0 0 10px}
.prio h4{color:var(--muted);margin:10px 0 6px;font-weight:600}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12px}
.td-file,.td-status,.td-duration{white-space:nowrap}
.status-passed{color:var(--ok);font-weight:700}
.status-failed{color:var(--fail);font-weight:700}
.row-failed td{background:#fdf0f0}
.td-msg{color:var(--fail);font-size:12px;word-break:break-all}
</style>
</head>
<body>
<h1>前端 Vitest 测试报告</h1>
<div class="sub">${new Date().toLocaleString("zh-CN")} · 模块 ${kpi.modules} 个</div>
<div class="kpis">
  <div class="kpi"><b>${kpi.total}</b><span>总用例</span></div>
  <div class="kpi"><b>${kpi.passed}</b><span>通过</span></div>
  <div class="kpi ${kpi.failed ? "fail" : ""}"><b>${kpi.failed}</b><span>失败</span></div>
  <div class="kpi"><b>${passRate}%</b><span>通过率</span></div>
</div>
${moduleSections}
</body>
</html>`
}

// 保留文件列表供分优先级渲染：模块名 → 该模块全部 testResults
function summaryFilesForModule(name) {
  const files = []
  for (const f of summary._files ?? []) {
    const m = MODULE_RE.exec(f.name ?? "")
    if (m && m[1] === name) files.push(f)
  }
  return files
}

export function generateReport(inputPath = DEFAULT_INPUT, outputPath = DEFAULT_OUTPUT) {
  const report = parseReport(inputPath)
  const summary = buildSummary(report)
  summary._files = report.testResults ?? []
  const html = renderHtml(summary)
  mkdirSync(dirname(outputPath), { recursive: true })
  writeFileSync(outputPath, html, "utf8")
  return summary
}

// 直接执行：node tests/generate-html-report.mjs [input] [output]
if (process.argv[1] && fileURLToPath(import.meta.url).replace(/\\/g, "/") === process.argv[1].replace(/\\/g, "/")) {
  const [input, output] = process.argv.slice(2)
  const summary = generateReport(
    input || DEFAULT_INPUT,
    output || DEFAULT_OUTPUT,
  )
  console.log(`模块 ${summary.kpi.modules} 个 · 用例 ${summary.kpi.total} · 通过 ${summary.kpi.passed} · 失败 ${summary.kpi.failed}`)
  console.log(`HTML 报告: ${output || DEFAULT_OUTPUT}`)
}
```

- [ ] **Step 3: 对照 html-report skill 微调 CSS 变量**

将 `:root` 中的色值替换为 html-report skill 的 animal-island-ui token 值（背景/卡片/主色/成功/失败/边框），其余结构不动。替换后重跑 Step 4 的验证确保功能不回退。

- [ ] **Step 4: 用 fixture 验证生成器（含失败渲染）**

先造一个含失败用例的临时 fixture：

```bash
node -e "const fs=require('fs');fs.writeFileSync(process.env.TEMP+'/fixture-report.json', JSON.stringify({numTotalTests:3,numPassedTests:2,numFailedTests:1,success:false,testResults:[{name:'D:/x/tests/devices/p0/d.spec.ts',status:'failed',assertionResults:[{ancestorTitles:['[P0] d'],fullName:'[P0] d 成功：ok',title:'成功：ok',status:'passed',duration:1.5,failureMessages:[]},{ancestorTitles:['[P0] d'],fullName:'[P0] d 失败：报错',title:'失败：报错',status:'failed',duration:2.5,failureMessages:['AssertionError: expected 1 to be 2']}]},{name:'D:/x/tests/devices/p1/e.spec.ts',status:'passed',assertionResults:[{ancestorTitles:['[P1] e'],fullName:'[P1] e 场景：预期',title:'场景：预期',status:'passed',duration:3,failureMessages:[]}]}]}))"
node tests/generate-html-report.mjs "$TEMP/fixture-report.json" "$TEMP/fixture-report.html"
```

Expected 输出: `模块 1 个 · 用例 3 · 通过 2 · 失败 1` + 报告路径。

Run（逐项独立断言，避免 grep -c 多匹配同行的误判）:
```bash
grep -c "devices" "$TEMP/fixture-report.html"
grep -c "失败：报错" "$TEMP/fixture-report.html"
grep -c "AssertionError" "$TEMP/fixture-report.html"
grep -c "P1 — 1 文件" "$TEMP/fixture-report.html"
```

Expected: 依次 `1` `1` `1` `1`（模块名、失败用例、失败详情、P1 分区标题都渲染）。再用浏览器打开该文件人工确认一次布局（表格、徽标、失败行红色底色）。

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/generate-html-report.mjs
git commit -m "test: 新增静态 HTML 报告生成器（按模块分组）" -- frontend/tests/generate-html-report.mjs
```

---

### Task 5: run.mjs 接入 html 预设与 all 模块汇总 + script

**Files:**
- Modify: `frontend/tests/run.mjs`
- Modify: `frontend/package.json`（新增 test:report:html）

**Interfaces:**
- Consumes: `parseReport` / `buildSummary` / `generateReport` from `./generate-html-report.mjs`（Task 4）
- Produces: `node tests/run.mjs html`、`node tests/run.mjs all` 的模块汇总打印、`npm run test:report:html`（验收 §8.5、§8.3 依赖）

- [ ] **Step 1: run.mjs 加 import 与 html 预设**

在 `frontend/tests/run.mjs` 的 import 区（module-scan import 之后）加：

```js
import { buildSummary, generateReport, parseReport } from './generate-html-report.mjs'
```

在 `presetsFor` 的 switch 中 `case 'prio'` 之前加：

```js
    case 'html':
      return [
        'run',
        '--reporter=json',
        `--outputFile.json=${join(reportsDir, 'report.json')}`,
        ...extraArgs,
      ]
```

在文件末尾 `process.exit(result.status ?? 1)` 之前加：

```js
if (mode === 'html' && result.status === 0) {
  const summary = generateReport(
    join(reportsDir, 'report.json'),
    join(reportsDir, 'html', 'index.html'),
  )
  console.log(`\n模块 ${summary.kpi.modules} 个 · 用例 ${summary.kpi.total} · 通过 ${summary.kpi.passed} · 失败 ${summary.kpi.failed}`)
  console.log(`HTML 报告: ${join(reportsDir, 'html', 'index.html')}`)
}

if (mode === 'all' && result.status === 0) {
  const summary = buildSummary(parseReport(join(reportsDir, 'report.json')))
  console.log('\n── 按模块汇总 ──')
  for (const m of summary.modules) {
    const line = [`${m.name}: P0 ${m.p0.passed}/${m.p0.total}`, `P1 ${m.p1.passed}/${m.p1.total}`, `失败 ${m.p0.failed + m.p1.failed}`]
    console.log(line.join(' · '))
  }
}
```

- [ ] **Step 2: package.json 新增 script**

在 `"test:report:json"` 下一行新增：`"test:report:html": "node tests/run.mjs html"`

- [ ] **Step 3: 验证 html 预设（真数据）**

Run:
```bash
npm run test:report:html
```

Expected: 107 用例全通过；随后打印 `模块 2 个 · 用例 107 · 通过 107 · 失败 0` 与 HTML 报告路径。

Run:
```bash
grep -c "dashboard\|login\|107" tests/reports/html/index.html
```

Expected: `≥3`（两个模块分区 + KPI 总数都渲染）。浏览器打开 `tests/reports/html/index.html` 人工确认：KPI 正确、模块分区正确、中文不乱码（验收 §8.5）。

- [ ] **Step 4: 验证 all 汇总打印**

Run:
```bash
node tests/run.mjs all
```

Expected: 用例全通过，末尾打印：

```
── 按模块汇总 ──
dashboard: P0 22/22 · P1 26/26 · 失败 0
login: P0 47/47 · P1 12/12 · 失败 0
```

（已实测：login P0 47 条、P1 12 条；dashboard P0 22 条、P1 26 条。结构必须为 `模块: P0 x/y · P1 x/y · 失败 z`。）

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/run.mjs frontend/package.json
git commit -m "test: run.mjs 接入 html 预设与 all 模块汇总" -- frontend/tests/run.mjs frontend/package.json
```

---

### Task 6: README 总注册表 + PRIORITY_TEMPLATE 更新

**Files:**
- Rewrite: `frontend/tests/README.md`
- Modify: `frontend/tests/PRIORITY_TEMPLATE.md`

**Interfaces:**
- Consumes: 无（纯文档）；模块清单以 `frontend/src/router.js` 为准（Step 1 校正）
- Produces: 总注册表（验收 §8.6 依赖）

- [ ] **Step 1: 对照 router.js 校正模块清单**

Run:
```bash
grep -n "path:" src/router.js
```

Expected: 得到平台全部路由模块清单（dashboard、login、devices、inspector、elements、cases、runner、reports、ai-assistant、workflow 等）。以下注册表若与实际路由有出入，以 router.js 为准增删行，说明列注明"待开测"。

- [ ] **Step 2: 重写 tests/README.md**

完整文件内容：

```markdown
# Frontend Vitest — 总注册表

优先级约定见 **[PRIORITY_TEMPLATE.md](./PRIORITY_TEMPLATE.md)**；分类设计见 **[DESIGN-module-classification.md](./DESIGN-module-classification.md)**。

目录按「模块 × 优先级」分类：

```
tests/<module>/
  p0/   # 必测 *.spec.ts
  p1/   # 建议测 *.spec.ts
  p2/   # 默认不测（仅 README 登记）
```

`helpers/`（挂载工具）与 `reports/`（报告产物）不是模块。Vitest UI 按 `<module>/<prio>` 分栏自动生成，新增模块只需建目录。

## 模块注册表

| 模块 | 目录 | 状态 | P0 文件 | P1 文件 | 说明 |
|------|------|------|---------|---------|------|
| dashboard | `tests/dashboard/` | ✅ P0+P1 | 2 | 4 | 数据编排 / 统计卡 / 导航 / 任务面板 / 活动线 |
| login | `tests/login/` | ✅ P0+P1 | 8 | 3 | 表单校验 / 账号池 / 认证流程 / 卡片 |
| devices | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| inspector | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| elements | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| cases | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| runner | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| reports | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| ai-assistant | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| workflow | — | ⬜ 未开始 | 0 | 0 | 待开测 |

> 新模块开测流程：按 `PRIORITY_TEMPLATE.md` 的 Checklist 建目录与用例 → 更新本表状态列。

## 用例命名规范

```ts
describe('[P0] <被测单元>')    // composable / 组件 / 编排器
it('<场景>：<预期>')            // 场景=操作或输入；预期=断言结果；多预期用「，」并列
```

模块名不写进命名（由文件路径 + UI 分栏承载）。反例：`it('测试登录')`（无场景无预期）、`it('登录成功, 写token')`（半角逗号）。

## 命令

```bash
cd frontend
npm test                          # 全部（所有模块 P0+P1）
npm run test:p0                   # 跨模块只跑 P0
npm run test:p1                   # 跨模块只跑 P1
npm run test:module -- login      # 只跑指定模块
npm run test:report               # 终端 + JUnit + JSON + 按模块汇总
npm run test:report:html          # 静态 HTML 报告（tests/reports/html/index.html）
npm run test:ui                   # Vitest UI：左侧按 模块/优先级 分栏
```

底层入口：`node tests/run.mjs [default|module|prio|file|verbose|junit|json|all|html|watch|ui]`。
```

- [ ] **Step 3: PRIORITY_TEMPLATE.md 补命名规范节与登记步骤**

在 `frontend/tests/PRIORITY_TEMPLATE.md` 的「用例写法要点」之前插入：

```markdown
## 用例命名规范

```ts
describe('[P0] <被测单元>')    // composable / 组件 / 编排器
it('<场景>：<预期>')            // 一条用例只测一个行为；多预期用「，」并列
```

- 场景=操作或输入，预期=断言结果，用全角「：」分隔
- 模块名不写进命名——由文件路径 + UI 分栏承载
- 反例：`it('测试登录')`（无场景无预期）、`it('登录成功, 写token, 跳转')`（半角逗号、无「：」）
```

在「新模块开测 Checklist」清单末尾（P2 分组之后）追加两行：

```markdown
- [ ] 用例名符合「场景：预期」命名规范（审计一遍）
- [ ] 更新 `tests/README.md` 模块注册表状态列
```

- [ ] **Step 4: 验证与 Commit**

Run（确认注册表数量与扫描一致）:
```bash
node -e "import('./tests/module-scan.mjs').then(m => console.log(m.listProjects().join(' ')))"
```

Expected: `dashboard/p0 dashboard/p1 login/p0 login/p1`。

```bash
git add frontend/tests/README.md frontend/tests/PRIORITY_TEMPLATE.md
git commit -m "test: README 重构为模块总注册表，PRIORITY_TEMPLATE 补命名规范" -- frontend/tests/README.md frontend/tests/PRIORITY_TEMPLATE.md
```

---

### Task 7: 现有用例命名审计与微调

**Files:**
- Modify: `frontend/tests/login/**/*.spec.ts`、`frontend/tests/dashboard/**/*.spec.ts` 中不合规的 `it(` 名称（仅名称，断言与结构不动）

**Interfaces:**
- Consumes: 命名规范（Task 6 Step 3）
- Produces: 全部用例名合规（验收 §8.7 依赖）

- [ ] **Step 1: 扫描不合规名称**

Run:
```bash
grep -rn "it(" tests/login tests/dashboard | grep -E "[,;]"
grep -rn "it(" tests/login tests/dashboard | grep -v "："
```

Expected 判断规则（按此执行，不扩大范围）：
1. 第一条命中（半角逗号/分号分隔）→ **必须修**：改为「场景：预期，预期」格式（半角逗号改全角「，」，场景与首个预期之间补全角「：」）。
2. 第二条命中（名称中无「：」）→ 逐条判断：名称 ≤ 12 字、且明确表达单一预期（如 `展示字段错误文案`）→ **保留不动**；名称无法看出测什么、或一个用例断言多个行为 → 补「场景：」结构。
3. 只改 `it('...')` 的字符串，**断言、expect 数量、describe 均不动**。

- [ ] **Step 2: 修改并跑回归**

改完跑（frontend 目录）:
```bash
npx vitest run
```

Expected: 17 文件 107 用例全部通过（用例数与改造前一致，验收 §8.1）。

- [ ] **Step 3: Commit（按文件列出改动）**

```bash
git add frontend/tests/login frontend/tests/dashboard
git commit -m "test: 用例命名对齐「场景：预期」规范" -- frontend/tests/login frontend/tests/dashboard
```

---

### Task 8: 终验 — 设计文档 §8 八条验收 + dev/build 冒烟

**Files:**
- 无新改动（如有遗漏问题修复后并入对应文件并随本任务提交）

- [ ] **Step 1: 全量回归**

Run:
```bash
npx vitest run
```

Expected: `17 passed (17)` / `107 passed (107)`（验收 §8.1）。

- [ ] **Step 2: UI 分栏等价验证**

Run:
```bash
npx vitest run --project login/p0 && npx vitest run --project login/p1 && npx vitest run --project dashboard/p0 && npx vitest run --project dashboard/p1
```

Expected: 四段各自通过，文件集互不重叠且并集 = 17 文件（验收 §8.2）。

- [ ] **Step 3: 命令矩阵**

Run:
```bash
npm run test:p0
npm run test:p1
npm run test:module -- login
npm run test:module -- dashboard
node tests/run.mjs prio p1
```

Expected: 均只跑对应范围且全部通过（验收 §8.3、§8.4）。

- [ ] **Step 4: HTML 报告终验**

Run:
```bash
npm run test:report:html
```

Expected: 生成 `tests/reports/html/index.html`；浏览器打开确认 KPI=107/107/0、dashboard 与 login 两个分区、中文无乱码、无「未分类」分区（验收 §8.5）。

- [ ] **Step 5: 注册表与命名**

人工核对：`tests/README.md` 注册表登记全部平台模块（与 `src/router.js` 一致）；抽查 3 个 spec 文件确认用例名符合规范（验收 §8.6、§8.7）。

- [ ] **Step 6: dev / build 冒烟**

Run:
```bash
npx vite build
```

Expected: 构建成功（vite.config 改动不影响 build，验收 §8.8）。

Run（后台起 dev server 后 200 即杀）:
```bash
npx vite --port 5199
# 另开终端: curl -s -o /dev/null -w "%{http_code}" http://localhost:5199 → 200
```

Expected: HTTP 200，随后 Ctrl+C 停掉（验收 §8.8）。

- [ ] **Step 7: 终验 Commit（如有修复）**

若前 6 步发现问题并修复了文件，则：
```bash
git add <修复的文件>
git commit -m "test: 终验收尾修复" -- <修复的文件>
```

无修复则跳过，不产生空提交。

---

## Self-Review 记录

- **Spec 覆盖**：设计 §1 目录约定→Task 1 扫描判据；§2 UI 分栏→Task 2；§3 命令→Task 3+5；§4 命名规范→Task 6+7；§5 注册表→Task 6；§6 HTML 报告→Task 4+5；§7 影响面→各任务 Files 列表；§8 验收→Task 8。
- **占位扫描**：无 TBD/TODO；所有代码块为完整内容。
- **类型一致性**：`scanModules()/listProjects()` 定义于 Task 1，Task 2/3/6 引用一致；`parseReport/buildSummary/renderHtml/generateReport` 定义于 Task 4，Task 5 引用签名一致；`summary._files` 仅在 generateReport 内部注入、renderHtml 经 summaryFilesForModule 消费，同文件闭环。
