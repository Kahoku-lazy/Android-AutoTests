import { readdirSync, readFileSync, statSync } from "node:fs"
import { dirname, join, relative } from "node:path"
import { fileURLToPath } from "node:url"

const FRONTEND = join(dirname(fileURLToPath(import.meta.url)), "..")
const SRC = join(FRONTEND, "src")

const FONT_FLOOR = 12

const EXTS = [".vue", ".css"]

const CARRIER_EXTS = [".vue", ".css", ".ts", ".js"]

const FONT_SIZE_RE = /font-size:\s*([0-9.]+)px/g

const FONT_SIZE_CAMEL_RE = /\bfontSize:\s*([0-9.]+)/g

const CANVAS_FONT_BASELINE = 18

const CANVAS_FONT_SUBFLOOR = 7

const RADIUS_FIGURE = new Set([
  "0",
  "0 !important",
  "0!important",
  "1px",
  "2px",
  "2px !important",
  "3px",
  "5px",
  "50%",
  "50% !important",
])

const RADIUS_SHAPE = new Set([
  "0 3px 3px 0",
  "0 4px 0 0",
  "3px 5px",
  "8px 16px 6px 14px",
  "14px 20px",
  "18px 26px",
])

const DURATION_EXCEPTION = new Set(["1.4s", "1.5s"])

const TOKENS = join(SRC, "shared/styles/tokens.css")

const MODULE_PREFIX_RE = /^--(ai|case|rg|di|wf|views)-/

const PALETTE = new Set([
  "--color-blue-27",
  "--color-blue-42",
  "--color-blue-53",
  "--color-blue-60",
  "--color-blue-62",
  "--color-blue-64",
  "--color-blue-68",
  "--color-blue-68-s64",
  "--color-blue-68-s64-a18",
  "--color-blue-82",
  "--color-blue-82-a10",
  "--color-blue-82-a18",
  "--color-blue-82-a30",
  "--color-blue-82-a60",
  "--color-blue-89",
  "--color-cyan-40",
  "--color-cyan-74",
  "--color-cyan-74-a10",
  "--color-cyan-74-a18",
  "--color-cyan-74-a30",
  "--color-green-23",
  "--color-green-33",
  "--color-green-49",
  "--color-green-60-a60",
  "--color-green-61",
  "--color-green-87",
  "--color-indigo-13",
  "--color-indigo-13-a18",
  "--color-indigo-13-a30",
  "--color-indigo-35-a10",
  "--color-indigo-35-a30",
  "--color-indigo-46",
  "--color-indigo-76",
  "--color-indigo-76-a18",
  "--color-indigo-84",
  "--color-ink-05-a05",
  "--color-ink-05-a10",
  "--color-ink-05-a18",
  "--color-ink-05-a30",
  "--color-ink-34",
  "--color-ink-42",
  "--color-ink-46",
  "--color-ink-47",
  "--color-ink-57",
  "--color-ink-79",
  "--color-lime-45",
  "--color-lime-45-a10",
  "--color-lime-94",
  "--color-orange-26",
  "--color-orange-32",
  "--color-orange-32-a05",
  "--color-orange-37",
  "--color-orange-44",
  "--color-orange-53",
  "--color-orange-55-a10",
  "--color-orange-55-a18",
  "--color-orange-55-a60",
  "--color-orange-63",
  "--color-orange-64",
  "--color-orange-76",
  "--color-orange-77",
  "--color-purple-47",
  "--color-purple-56",
  "--color-purple-73",
  "--color-purple-74",
  "--color-purple-87",
  "--color-red-29",
  "--color-red-46",
  "--color-red-49",
  "--color-red-69",
  "--color-red-69-a05",
  "--color-red-69-a10",
  "--color-red-69-a30",
  "--color-red-73",
  "--color-red-83",
  "--color-red-85",
  "--color-red-95",
  "--color-teal-29",
  "--color-teal-30",
  "--color-teal-38",
  "--color-teal-49",
  "--color-teal-49-a30",
  "--color-teal-67",
  "--color-violet-75",
  "--color-violet-89",
  "--color-violet-96",
  "--color-white",
  "--color-white-a30",
  "--color-white-a60",
  "--color-yellow-24",
  "--color-yellow-27",
  "--color-yellow-35",
  "--color-yellow-53",
  "--color-yellow-62",
  "--color-yellow-63",
  "--color-yellow-70",
  "--color-yellow-79",
  "--color-yellow-87",
  "--color-yellow-94",
])

const PALETTE_NAME_RE = /^--color-([a-z]+-\d{2}(-s\d{2})?(-a\d{2})?|white(-a\d{2})?)$/

const SERIAL_NAME_RE = /-[0-9]$/

const COLOR_RE = /^(#[0-9a-f]{3,8}|rgba?\([^)]*\))$/i

const EMBEDDED_COLOR_RE = /(#[0-9a-f]{3,8}|rgba?\()/i

function walk(dir, exts = EXTS) {
  const out = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) out.push(...walk(full, exts))
    else if (exts.some((ext) => name.endsWith(ext))) out.push(full)
  }
  return out
}

function relOf(file) {
  return relative(SRC, file).split(/[\\/]/).join("/")
}

function boundaryOf(rel) {
  const parts = rel.split("/")
  if (parts[0] === "modules") return parts[1]
  return parts[0] === "views" || parts[0] === "shared" ? parts[0] : "root"
}

function isT0File(rel) {
  return rel.startsWith("shared/styles/") || rel === "style.css"
}

function styleBlocks(text) {
  const out = []
  for (const m of text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)) {
    out.push({ css: m[1], startLine: text.slice(0, m.index).split(/\r?\n/).length })
  }
  return out
}

function injectedNames(text) {
  const out = new Set()
  for (const m of text.matchAll(/(['"])(--[a-zA-Z0-9-]+)\1\s*:/g)) out.add(m[2])
  for (const line of text.split(/\r?\n/)) {
    if (!/\bstyle\s*=/.test(line)) continue
    for (const m of line.matchAll(/(--[a-zA-Z0-9-]+)\s*:/g)) out.add(m[1])
  }
  return out
}

function isCommentLine(line) {
  const t = line.trim()
  return (
    t.startsWith("*") ||
    t.startsWith("//") ||
    t.startsWith("/*") ||
    t.startsWith("<!--") ||
    t.startsWith("*/")
  )
}

function carrierRefs(text) {
  const out = []
  text.split(/\r?\n/).forEach((line, index) => {
    if (isCommentLine(line)) return
    for (const m of line.matchAll(/var\((--[a-zA-Z0-9-]+)/g))
      out.push({ name: m[1], line: index + 1 })
  })
  return out
}

function consumptionLiterals(rel, text) {
  const out = []
  const blocks = rel.endsWith(".css") ? [{ css: text, startLine: 1 }] : styleBlocks(text)
  for (const b of blocks) {
    b.css.split(/\r?\n/).forEach((raw, i) => {
      const line = raw.replace(/\/\*[\s\S]*?\*\//g, "")
      if (isCommentLine(line)) return
      for (const m of line.matchAll(/#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)/g)) {
        const head = line.slice(0, m.index)
        const cut = Math.max(head.lastIndexOf(";"), head.lastIndexOf("{"))
        const decl = head.slice(cut + 1).trim()
        if (/^--[a-zA-Z0-9-]+\s*:/.test(decl)) continue
        out.push(rel + ":" + (b.startLine + i) + "  " + m[0])
      }
    })
  }
  return out
}

function scanDeclarations(css) {
  const out = []
  const re = /(--[a-zA-Z0-9-]+)\s*:\s*([^;}]+)/g
  const logical = []
  let buffer = ""
  let startLine = 0
  css.split(/\r?\n/).forEach((line, index) => {
    if (buffer === "") startLine = index + 1
    buffer = buffer === "" ? line : buffer + " " + line.trim()

    if (/(;|\{|\})\s*$/.test(buffer) || /\*\/\s*$/.test(buffer)) {
      logical.push({ text: buffer, line: startLine })
      buffer = ""
    }
  })
  if (buffer !== "") logical.push({ text: buffer, line: startLine })

  for (const entry of logical) {
    re.lastIndex = 0
    let match
    while ((match = re.exec(entry.text)) !== null) {
      const prefix = entry.text.slice(0, match.index)
      if (prefix.trim() !== "") {
        const last = prefix.replace(/\s+$/, "").slice(-1)
        if (last !== "{" && last !== ";") continue
      }
      out.push({ line: entry.line, name: match[1], value: match[2].trim() })
    }
  }
  return out
}

function normalizeColor(value) {
  const s = value.replace(/\s+/g, "").toLowerCase()
  if (/^#[0-9a-f]{3,8}$/.test(s)) {
    let hex = s.slice(1)
    if (hex.length === 3)
      hex = hex
        .split("")
        .map((c) => c + c)
        .join("")
    const channel = (i) => parseInt(hex.slice(i, i + 2), 16)
    const alpha = hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1
    return `rgba(${channel(0)},${channel(2)},${channel(4)},${Number(alpha.toFixed(3))})`
  }
  const m = s.match(/^rgba?\(([\d.]+),([\d.]+),([\d.]+)(?:,([\d.]+))?\)$/)
  if (m)
    return `rgba(${Number(m[1])},${Number(m[2])},${Number(m[3])},${m[4] !== undefined ? Number(m[4]) : 1})`
  return null
}

const violations = []
const canvasFonts = []
for (const file of walk(SRC, CARRIER_EXTS)) {
  const rel = relOf(file)
  const lines = readFileSync(file, "utf8").split(/\r?\n/)
  lines.forEach((text, index) => {
    for (const match of text.matchAll(FONT_SIZE_RE)) {
      const size = Number(match[1])
      if (size < FONT_FLOOR) {
        violations.push({
          file: relative(FRONTEND, file),
          line: index + 1,
          size,
          text: text.trim(),
        })
      }
    }
    for (const match of text.matchAll(FONT_SIZE_CAMEL_RE)) {
      canvasFonts.push({ at: rel + ":" + (index + 1), size: Number(match[1]) })
    }
  })
}

const tokensCss = readFileSync(TOKENS, "utf8")
const tokenDecls = scanDeclarations(tokensCss)
const declared = new Set(tokenDecls.map((d) => d.name))
const hard = []
const composites = []
const colorSeen = new Map()

for (const d of tokenDecls) {
  if (d.name.startsWith("--color-")) {
    if (!COLOR_RE.test(d.value)) {
      hard.push(`G1 ${d.name} 不是色值：${d.value}（第 ${d.line} 行）`)
      continue
    }
    const key = normalizeColor(d.value)
    if (colorSeen.has(key))
      hard.push(`G1 同值重复：${d.name} 与 ${colorSeen.get(key)} 都是 ${d.value}`)
    else colorSeen.set(key, d.name)

    if (!PALETTE.has(d.name))
      hard.push(`G8 颜色原子不在调色板白名单：${d.name} → 复用调色板内最接近的原子，或先修订调色板`)
    if (!PALETTE_NAME_RE.test(d.name)) hard.push(`G9 颜色原子命名不合调色板形状：${d.name}`)
    if (SERIAL_NAME_RE.test(d.name)) hard.push(`G10 颜色原子命中序号兜底名：${d.name}`)
    continue
  }

  if (COLOR_RE.test(d.value)) {
    hard.push(`G2 ${d.name} 直接写了色值 ${d.value}（第 ${d.line} 行）→ 应引用 var(--color-*)`)
    continue
  }

  if (EMBEDDED_COLOR_RE.test(d.value)) composites.push(`${d.name} = ${d.value}（第 ${d.line} 行）`)

  if (MODULE_PREFIX_RE.test(d.name) && !d.value.startsWith("var(")) {
    hard.push(`G3 ${d.name} 应引用主 token 原子，实际=${d.value}`)
  }
}

if (colorSeen.size > PALETTE.size)
  hard.push(`G11 颜色原子 ${colorSeen.size} 个，超过调色板上限 ${PALETTE.size} 个`)
if (colorSeen.size < PALETTE.size)
  console.log(
    "[style-gates] 调色板：在用 " +
      colorSeen.size +
      " / 上限 " +
      PALETTE.size +
      "（可继续下调上限）",
  )

const refRe = /var\((--[a-zA-Z0-9-]+)/g
let refMatch
while ((refMatch = refRe.exec(tokensCss)) !== null) {
  if (!declared.has(refMatch[1])) hard.push(`G4 引用了未声明的令牌 ${refMatch[1]} → 静默回退风险`)
}

const hard3 = []

const declSites = new Map()

const moduleLiteralDecls = []
for (const file of walk(SRC)) {
  const rel = relOf(file)
  const text = readFileSync(file, "utf8")
  const blocks = rel.endsWith(".css") ? [{ css: text, startLine: 1 }] : styleBlocks(text)
  for (const b of blocks) {
    for (const d of scanDeclarations(b.css)) {
      const where = isT0File(rel) ? "t0" : boundaryOf(rel)
      if (!declSites.has(d.name)) declSites.set(d.name, new Set())
      declSites.get(d.name).add(where)
      if (MODULE_PREFIX_RE.test(d.name) && !d.value.startsWith("var(")) {
        moduleLiteralDecls.push(
          rel +
            ":" +
            (b.startLine + d.line - 1) +
            "  " +
            d.name +
            " = " +
            d.value +
            " → 应引用 var(--color-*)",
        )
      }
    }
  }
}

const carrierFiles = walk(SRC, CARRIER_EXTS).map((file) => ({
  rel: relOf(file),
  text: readFileSync(file, "utf8"),
}))

const injectedByBoundary = new Map()
for (const { rel, text } of carrierFiles) {
  const boundary = boundaryOf(rel)
  if (!injectedByBoundary.has(boundary)) injectedByBoundary.set(boundary, new Set())
  for (const name of injectedNames(text)) injectedByBoundary.get(boundary).add(name)
}

const danglingRefs = []
const crossBoundaryRefs = []
let carrierTotal = 0
for (const { rel, text } of carrierFiles) {
  const boundary = boundaryOf(rel)
  const injected = injectedByBoundary.get(boundary)
  for (const ref of carrierRefs(text)) {
    carrierTotal++

    if (injected.has(ref.name)) continue
    const sites = declSites.get(ref.name)
    if (!sites || sites.size === 0) {
      danglingRefs.push(rel + ":" + ref.line + "  var(" + ref.name + ") → 全仓无声明")
      continue
    }
    if (!sites.has("t0") && !sites.has(boundary)) {
      crossBoundaryRefs.push(
        rel +
          ":" +
          ref.line +
          "  var(" +
          ref.name +
          ") → 仅声明于 [" +
          [...sites].join(", ") +
          "]，越界借用",
      )
    }
  }
}
if (danglingRefs.length) hard3.push(...danglingRefs.map((r) => "G5 悬空引用 " + r))
if (crossBoundaryRefs.length) hard3.push(...crossBoundaryRefs.map((r) => "G6 跨边界借用 " + r))
if (moduleLiteralDecls.length)
  hard3.push(...moduleLiteralDecls.map((r) => "G7 模块声明持字面量 " + r))

const consumption = []
for (const file of walk(SRC))
  consumption.push(...consumptionLiterals(relOf(file), readFileSync(file, "utf8")))

const geom = []
for (const file of walk(SRC)) {
  const rel = relOf(file)
  const text = readFileSync(file, "utf8")
  const blocks = rel.endsWith(".css") ? [{ css: text, startLine: 1 }] : styleBlocks(text)
  for (const b of blocks) {
    b.css.split(/\r?\n/).forEach((raw, i) => {
      const line = raw.replace(/\/\*[\s\S]*?\*\//g, "")
      if (isCommentLine(line)) return
      const at = rel + ":" + (b.startLine + i)

      for (const m of line.matchAll(/box-shadow\s*:\s*([^;}]+)/g)) {
        for (const layer of m[1].split(",")) {
          const lens = []
          for (const tok of layer
            .trim()
            .replace(/^inset\s+/, "")
            .split(/\s+/)) {
            if (/^-?[\d.]+px$/.test(tok)) {
              lens.push(parseFloat(tok))
              continue
            }
            if (tok === "0") {
              lens.push(0)
              continue
            }
            break
          }
          if (lens.length >= 3 && lens[2] !== 0) {
            geom.push("G12 模糊阴影 " + at + "  " + m[1].trim() + " → 模糊半径必须为 0")
          }
        }
      }

      for (const m of line.matchAll(/border-radius\s*:\s*([^;}]+)/g)) {
        const v = m[1].trim()
        if (/var\(/.test(v) || RADIUS_FIGURE.has(v) || RADIUS_SHAPE.has(v)) continue
        const p = v.split(/\s+/)
        const redundant = p.length === 4 && p[0] === p[2] && p[1] === p[3]
        geom.push(
          "G13 " +
            (redundant ? "等价四值圆角 " : "未登记圆角 ") +
            at +
            "  " +
            v +
            (redundant ? " → 折叠为两值 A B" : " → 改用 --app-radius-* 或登记例外"),
        )
      }

      for (const m of line.matchAll(/(?:transition|animation)\s*:\s*([^;}]+)/g)) {
        const v = m[1].trim()
        if (v === "none") continue
        for (const d of v.matchAll(/\b[\d.]+m?s\b/g)) {
          if (!DURATION_EXCEPTION.has(d[0])) {
            geom.push("G14 动效裸时长 " + at + "  " + v + "（" + d[0] + "）→ 改用 --app-duration-*")
          }
        }
        if (/(?<![\w-])ease(?![\w-])/.test(v)) {
          geom.push("G14 动效裸缓动 " + at + "  " + v + " → 改用 var(--app-ease)")
        }
      }
    })
  }
}

console.log(
  `[style-gates] 批 2 · T0 主 token：声明 ${tokenDecls.length} 条 · 颜色原子 ${colorSeen.size} 个 · 复合值登记 ${composites.length} 条`,
)
if (composites.length) {
  console.log("[style-gates] 复合值（内嵌颜色，本期保留字面量并登记）：")
  for (const c of composites) console.log("  " + c)
}
if (hard.length) {
  console.error(`[style-gates] 批 2 硬门禁失败：${hard.length} 处`)
  for (const h of hard.slice(0, 40)) console.error("  " + h)
  process.exit(1)
}

const legacyRe =
  /^--(c-|app-(status|pass|fail|pending|live|offline|error|bg|btn|page|icon|footer|queue|warning|nav|stat|timeline|pushpin|overlay|highlight))/
const legacy = tokenDecls.filter((d) => legacyRe.test(d.name)).length
console.log(
  "[style-gates] 存量清单：场景名/模块名别名 " + legacy + " 条（变更 B 归位目标，只降不增）",
)
console.log(
  "[style-gates] 批 2 通过：颜色原子唯一 + 调色板白名单（上限 " +
    PALETTE.size +
    "）+ 非原子声明无纯色字面量 + 引用完整",
)
console.log(
  "[style-gates] 批 3 · 非样式表载体 " +
    carrierTotal +
    " 处：悬空引用 " +
    danglingRefs.length +
    " · 跨边界借用 " +
    crossBoundaryRefs.length +
    " · 模块声明持字面量 " +
    moduleLiteralDecls.length,
)
if (consumption.length) {
  console.log(
    "[style-gates] 存量清单：消费位置裸色字面量 " +
      consumption.length +
      " 处（只降不增、未阻断；应改用 var(--color-*)）",
  )
  for (const c of consumption.slice(0, 10)) console.log("  " + c)
  if (consumption.length > 10) console.log("  … 其余 " + (consumption.length - 10) + " 处")
}
if (hard3.length) {
  console.error("[style-gates] 批 3 硬门禁失败：" + hard3.length + " 处")
  for (const h of hard3.slice(0, 40)) console.error("  " + h)
  process.exit(1)
}
console.log("[style-gates] 批 3 通过：非样式表载体均按边界可解析 + 模块前缀声明值来源于 T0")

console.log(
  "[style-gates] 批 4 · 几何尺度：阴影模糊半径恒为 0 · 圆角取刻度或已登记例外 · 动效时长取令牌",
)
if (geom.length) {
  console.error("[style-gates] 批 4 硬门禁失败：" + geom.length + " 处")
  for (const g of geom.slice(0, 40)) console.error("  " + g)
  process.exit(1)
}
console.log("[style-gates] 批 4 通过：阴影无模糊 + 圆角无未登记字面量 + 动效无未登记裸时长")

const canvasSub = canvasFonts.filter((f) => f.size < FONT_FLOOR)
console.log(
  "[style-gates] 批 1b · 画布字号 " +
    canvasFonts.length +
    " 处（上限 " +
    CANVAS_FONT_BASELINE +
    "；其中 < " +
    FONT_FLOOR +
    "px " +
    canvasSub.length +
    " 处，上限 " +
    CANVAS_FONT_SUBFLOOR +
    "）→ ECharts/VueFlow 图形参数，只降不增、不阻断",
)
if (canvasFonts.length > CANVAS_FONT_BASELINE || canvasSub.length > CANVAS_FONT_SUBFLOOR) {
  console.error("[style-gates] 批 1b 画布字号超上限（只降不增）")
  process.exit(1)
}

if (violations.length === 0) {
  console.log(`[style-gates] 批 1 通过：无 font-size < ${FONT_FLOOR}px 的硬编码`)
  process.exit(0)
}

console.error(`[style-gates] 批 1 硬门禁失败：${violations.length} 处 font-size < ${FONT_FLOOR}px`)
for (const v of violations) {
  console.error("  " + v.file + ":" + v.line + "  " + v.size + "px  → 改用 var(--font-size-xs)")
}
process.exit(1)
