/**
 * 前端样式门禁（批 1：字号下限 12px）
 *
 * 用法：
 *   node tests/check-style-gates.mjs            仅告警，exit 0
 *   node tests/check-style-gates.mjs --strict   违规即 exit 1（CI 用）
 *
 * 规则来源：tokens.css「字号刻度（6 档，最小 12px，禁止硬编码 font-size 字面量）」
 *          与 vue-frontend-check checklist 第 1 条（< 12px → 🟠）
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const FRONTEND = join(dirname(fileURLToPath(import.meta.url)), '..')
const SRC = join(FRONTEND, 'src')
const STRICT = process.argv.includes('--strict')

/** 字号下限（px）—— 与 tokens.css 的 --app-size-xs 对齐 */
const FONT_FLOOR = 12
/** 只扫可能承载样式的文件类型 */
const EXTS = ['.vue', '.css']
/** 只匹配字面量 px，命中 var(--app-size-*) 的写法不受影响 */
const FONT_SIZE_RE = /font-size:\s*([0-9.]+)px/g

function walk(dir) {
  const out = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) out.push(...walk(full))
    else if (EXTS.some((ext) => name.endsWith(ext))) out.push(full)
  }
  return out
}

const violations = []
for (const file of walk(SRC)) {
  const lines = readFileSync(file, 'utf8').split(/\r?\n/)
  lines.forEach((text, index) => {
    for (const match of text.matchAll(FONT_SIZE_RE)) {
      const size = Number(match[1])
      if (size < FONT_FLOOR) {
        violations.push({ file: relative(FRONTEND, file), line: index + 1, size, text: text.trim() })
      }
    }
  })
}

if (violations.length === 0) {
  console.log('[style-gates] 通过：无 font-size < ' + FONT_FLOOR + 'px 的硬编码')
  process.exit(0)
}

console.log('[style-gates] 发现 ' + violations.length + ' 处 font-size < ' + FONT_FLOOR + 'px：')
for (const v of violations) {
  console.log('  ' + v.file + ':' + v.line + '  ' + v.size + 'px  → 改用 var(--app-size-xs)')
}
if (STRICT) {
  console.error('[style-gates] --strict 模式：门禁失败')
  process.exit(1)
}
console.log('[style-gates] 当前为告警模式（未阻断）；清零后可在 CI 换成 --strict')
