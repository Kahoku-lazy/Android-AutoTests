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
