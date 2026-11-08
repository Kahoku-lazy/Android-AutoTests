/*
 * 前端模块计数 + 依赖边（给 gen_board_data.py 调用，只读、只打印 JSON）
 *
 * 为什么用 TypeScript 编译器而不是正则：Vue 3 组合式写法大量使用箭头函数与
 * SFC 的 <script setup>，正则会把回调、模板属性一起数进去，得出无法解释的数字。
 * 这里用本地 frontend/node_modules/typescript 做语法树统计，不联网、不做类型检查。
 *
 * 口径：
 * - 文件数：模块目录下 .vue / .ts / .js（SFC 只算一个文件）
 * - 类数：ClassDeclaration
 * - 方法数：命名函数/方法定义——FunctionDeclaration + MethodDeclaration
 *           + 具名变量/属性赋值的箭头函数与函数表达式（不含匿名回调与内联 handler）
 * - 代码行数：整文件非空物理行（含 template / style）
 * - 功能数：routes.ts 里注册的路由条目数；routes 里同时给出 path/name/title 明细
 * - 依赖边：模块之间（含共享层）的 import 次数，只算 `@/` 别名与相对路径
 *
 * 用法：node tools/count_frontend.mjs <repo-root>
 */

import fs from "node:fs"
import path from "node:path"
import { pathToFileURL } from "node:url"

const repo = process.argv[2]
if (!repo) {
  console.error("usage: node count_frontend.mjs <repo-root>")
  process.exit(2)
}

const tsEntry = path.join(repo, "frontend", "node_modules", "typescript", "lib", "typescript.js")
if (!fs.existsSync(tsEntry)) {
  console.error(`typescript not found: ${tsEntry}`)
  process.exit(2)
}
const ts = (await import(pathToFileURL(tsEntry).href)).default

const SRC = path.join(repo, "frontend", "src")
const MODULES_DIR = path.join(SRC, "modules")
const SHARED_KEY = "共享层（shared/views/router）"
const CODE_EXT = new Set([".vue", ".ts", ".js"])
const SCRIPT_RE = /<script[^>]*>([\s\S]*?)<\/script>/g

function walk(dir) {
  if (!fs.existsSync(dir)) return []
  const out = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist") continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walk(full))
    else if (CODE_EXT.has(path.extname(entry.name))) out.push(full)
  }
  return out
}

/** 文件 → 所属模块 key（modules/<name> 为业务模块，其余归共享层） */
function moduleOf(absPath) {
  const rel = path.relative(SRC, absPath).split(path.sep).join("/")
  const parts = rel.split("/")
  if (parts[0] === "modules" && parts.length > 1) return parts[1]
  return SHARED_KEY
}

function parse(file) {
  const text = fs.readFileSync(file, "utf8")
  const ext = path.extname(file)
  const sources =
    ext === ".vue"
      ? [...text.matchAll(SCRIPT_RE)].map((match) => match[1]).join("\n")
      : text
  return {
    text,
    lines: text.split(/\r?\n/).filter((line) => line.trim() !== "").length,
    sourceFile: ts.createSourceFile(
      file,
      sources,
      ts.ScriptTarget.Latest,
      true,
      ext === ".ts" || ext === ".vue" ? ts.ScriptKind.TS : ts.ScriptKind.JS
    )
  }
}

function countSymbols(sourceFile) {
  let classes = 0
  let functions = 0
  const visit = (node) => {
    if (ts.isClassDeclaration(node)) classes += 1
    if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) functions += 1
    if (ts.isVariableDeclaration(node) && node.initializer) {
      const init = node.initializer
      if (ts.isArrowFunction(init) || ts.isFunctionExpression(init)) functions += 1
    }
    if (ts.isPropertyAssignment(node) && node.initializer) {
      const init = node.initializer
      if (ts.isArrowFunction(init) || ts.isFunctionExpression(init)) functions += 1
    }
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)
  return { classes, functions }
}

/** 收集一个文件里引用到的本地模块（`@/…` 与相对路径），解析成真实文件路径 */
function collectLocalImports(file, sourceFile) {
  const specifiers = new Set()
  const visit = (node) => {
    if (ts.isImportDeclaration(node) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      specifiers.add(node.moduleSpecifier.text)
    }
    if (ts.isExportDeclaration(node) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      specifiers.add(node.moduleSpecifier.text)
    }
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      const arg = node.arguments[0]
      if (arg && ts.isStringLiteral(arg)) specifiers.add(arg.text)
    }
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)

  const resolved = new Set()
  for (const spec of specifiers) {
    let base
    if (spec.startsWith("@/")) base = path.join(SRC, spec.slice(2))
    else if (spec.startsWith("./") || spec.startsWith("../")) base = path.resolve(path.dirname(file), spec)
    else continue
    const candidates = [base, `${base}.ts`, `${base}.js`, `${base}.vue`, path.join(base, "index.ts"), path.join(base, "index.vue")]
    const hit = candidates.find((candidate) => fs.existsSync(candidate) && fs.statSync(candidate).isFile())
    if (hit) resolved.add(hit)
  }
  return resolved
}

/** routes.ts → [{path, name, title}]（轻量状态机，只认最常见的对象字面量写法） */
function routeEntries(file) {
  if (!fs.existsSync(file)) return []
  const text = fs.readFileSync(file, "utf8")
  const out = []
  let current = null
  for (const line of text.split(/\r?\n/)) {
    const pathMatch = line.match(/path\s*:\s*["']([^"']+)["']/)
    if (pathMatch) {
      if (current && current.path) out.push(current)
      current = { path: pathMatch[1], name: "", title: "" }
      continue
    }
    if (!current) continue
    const nameMatch = line.match(/name\s*:\s*["']([^"']+)["']/)
    if (nameMatch && !current.name) current.name = nameMatch[1]
    const titleMatch = line.match(/title\s*:\s*["']([^"']+)["']/)
    if (titleMatch && !current.title) current.title = titleMatch[1]
  }
  if (current && current.path) out.push(current)
  return out
}

const modules = []
const edges = new Map()
const routesByModule = {}

const countFiles = (files) => {
  const row = { files: files.length, classes: 0, functions: 0, loc: 0, routes: 0 }
  for (const file of files) {
    const parsed = parse(file)
    const counted = countSymbols(parsed.sourceFile)
    row.classes += counted.classes
    row.functions += counted.functions
    row.loc += parsed.lines
  }
  return row
}

const recordEdges = (fromKey, files) => {
  for (const file of files) {
    const parsed = parse(file)
    for (const target of collectLocalImports(file, parsed.sourceFile)) {
      const toKey = moduleOf(target)
      if (toKey === fromKey) continue
      const key = `${fromKey}->${toKey}`
      edges.set(key, (edges.get(key) || 0) + 1)
    }
  }
}

for (const entry of fs.readdirSync(MODULES_DIR, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue
  const dir = path.join(MODULES_DIR, entry.name)
  const files = walk(dir)
  const row = { name: entry.name, ...countFiles(files), routes: 0 }
  const routesFile = path.join(dir, "routes.ts")
  const routes = routeEntries(routesFile)
  row.routes = routes.length
  routesByModule[entry.name] = routes
  modules.push(row)
  recordEdges(entry.name, files)
}
modules.sort((a, b) => b.loc - a.loc)

/* 共享层：shared/ + views/ + router.ts 合一行，避免"合计"漏掉这部分代码 */
const sharedFiles = [
  ...walk(path.join(SRC, "shared")),
  ...walk(path.join(SRC, "views")),
  path.join(SRC, "router.ts")
].filter((file) => fs.existsSync(file))
const shared = sharedFiles.length
  ? [{ name: SHARED_KEY, ...countFiles(sharedFiles), routes: 0 }]
  : []
recordEdges(SHARED_KEY, sharedFiles)

process.stdout.write(
  JSON.stringify(
    {
      modules,
      shared,
      routesByModule,
      edges: [...edges.entries()].map(([key, count]) => {
        const [from, to] = key.split("->")
        return { from, to, count }
      })
    },
    null,
    2
  )
)
