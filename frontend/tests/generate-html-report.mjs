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

const MODULE_RE = /tests[\\/]([^\\/]+)[\\/](p[01])[\\/]/
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
      const files = summaryFilesForModule(summary, m.name)
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
:root{--bg:#f8f8f0;--card:#f7f3df;--ink:#794f27;--muted:#9f927d;--ok:#6fba2c;--fail:#e05a5a;--line:#c4b89e;--accent:#19c8b9}
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
function summaryFilesForModule(summary, name) {
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
