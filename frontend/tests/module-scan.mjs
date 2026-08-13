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
