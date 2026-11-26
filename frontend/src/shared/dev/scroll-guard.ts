import type { Router } from "vue-router"

const SCROLLABLE_OVERFLOW = new Set(["auto", "scroll", "overlay"])

const CLIPPING_OVERFLOW = new Set(["hidden", "clip"])

const PIXEL_TOLERANCE = 1

export interface ScrollGuardDeps {
  getPageRoot?: () => HTMLElement | null

  getOverflowY?: (element: HTMLElement) => string

  warn?: (message: string) => void
}

export interface ScrollGuardOptions extends ScrollGuardDeps {
  router?: Router
}

export interface ScrollIssue {
  element: HTMLElement

  isPageRoot: boolean
  overflowY: string
  scrollHeight: number
  clientHeight: number
}

function defaultGetPageRoot(): HTMLElement | null {
  return document.querySelector<HTMLElement>(".main-content__body > *")
}

function defaultGetOverflowY(element: HTMLElement): string {
  return getComputedStyle(element).overflowY
}

function overflows(element: HTMLElement): boolean {
  return element.scrollHeight > element.clientHeight + PIXEL_TOLERANCE
}

function describe(element: HTMLElement): string {
  const id = element.id ? "#" + element.id : ""
  const classes = Array.from(element.classList)
    .slice(0, 3)
    .map((name) => "." + name)
    .join("")
  return "<" + element.tagName.toLowerCase() + id + classes + ">"
}

export function detectClippedChain(
  pageRoot: HTMLElement,
  deps: Pick<ScrollGuardDeps, "getOverflowY"> = {},
): ScrollIssue | null {
  const getOverflowY = deps.getOverflowY ?? defaultGetOverflowY
  const describeAt = (element: HTMLElement): ScrollIssue => ({
    element,
    isPageRoot: element === pageRoot,
    overflowY: getOverflowY(element),
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight,
  })

  let spilled: ScrollIssue | null = null
  let node: HTMLElement | null = pageRoot

  while (node && node !== document.body && node !== document.documentElement) {
    if (overflows(node)) {
      const overflowY = getOverflowY(node)
      if (SCROLLABLE_OVERFLOW.has(overflowY)) return null
      if (CLIPPING_OVERFLOW.has(overflowY)) return describeAt(node)
      spilled = spilled ?? describeAt(node)
    }
    node = node.parentElement
  }

  return spilled
}

function formatIssue(issue: ScrollIssue): string {
  const whose = issue.isPageRoot ? "页面根" : "中间容器"
  return (
    "[scroll-guard] L0 契约被破：" +
    whose +
    " " +
    describe(issue.element) +
    " 内容高 " +
    issue.scrollHeight +
    "px，超出可视区 " +
    issue.clientHeight +
    "px，" +
    "而 overflow-y 是 " +
    issue.overflowY +
    "（不可滚）；祖先链上也没有滚动容器" +
    "（html / body / #app 均为 overflow: hidden），超出一屏的部分会被静默裁掉。" +
    "修法：让页面落在 .main-content__body（策略①）或 .doc-page--fixed 的 .doc-body（策略②）内，" +
    "并给链上每个 flex:1 补 min-height:0。"
  )
}

let installed = false

export function installScrollGuard(options: ScrollGuardOptions = {}): void {
  if (!import.meta.env.DEV || typeof window === "undefined") return
  if (installed) return
  installed = true

  const getPageRoot = options.getPageRoot ?? defaultGetPageRoot
  const warn = options.warn ?? ((message: string) => console.warn(message))
  const warned = new WeakMap<HTMLElement, string>()

  const run = () => {
    const pageRoot = getPageRoot()
    if (!pageRoot) return

    const issue = detectClippedChain(pageRoot, options)
    if (!issue) return

    const message = formatIssue(issue)
    if (warned.get(issue.element) === message) return
    warned.set(issue.element, message)
    warn(message)
  }

  requestAnimationFrame(run)

  if (options.router) {
    options.router.afterEach(() => setTimeout(run, 400))
  }

  let resizeTimer: ReturnType<typeof setTimeout> | undefined
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(run, 300)
  })
}
