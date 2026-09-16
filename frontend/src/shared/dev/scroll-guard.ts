/**
 * L0 滚动自检（仅开发环境）
 *
 * 背景：html / body / #app 都是 overflow: hidden（见 src/style.css 顶部），
 * 平台用「视口固定 + 内层滚动」策略：滚动只能发生在策略① .main-content__body 或
 * 策略② .doc-page--fixed 的 .doc-body 里。
 *
 * 破约的后果是静默的：页面根（或中间某层）撑破了容器、自身又不能滚时，
 * 超出一屏的部分既看不到、也滚不到，界面上没有任何提示。
 *
 * 本模块在开发环境做一次自检：从页面根往 body 走，找到第一个「溢出且自身不可滚」
 * 的祖先，就 console.warn 报出来。生产构建不加载（main.ts 里按 import.meta.env.DEV 动态 import）。
 */

import type { Router } from 'vue-router'

/** 能滚动的 overflow 取值（overlay 为老 WebKit 写法，一并认下） */
const SCROLLABLE_OVERFLOW = new Set(['auto', 'scroll', 'overlay'])

/** 会把溢出内容裁掉且自身不可滚的取值：到了这一层，内容就够不着了 */
const CLIPPING_OVERFLOW = new Set(['hidden', 'clip'])

/** 亚像素误差容忍：scrollHeight 与 clientHeight 常有 1px 内的取整差 */
const PIXEL_TOLERANCE = 1

export interface ScrollGuardDeps {
  /** 取页面根元素，默认 .main-content__body > * */
  getPageRoot?: () => HTMLElement | null
  /** 读元素纵向 overflow，默认 getComputedStyle（可注入，单测时绕开 jsdom 的样式实现差异） */
  getOverflowY?: (element: HTMLElement) => string
  /** 告警出口，默认 console.warn */
  warn?: (message: string) => void
}

export interface ScrollGuardOptions extends ScrollGuardDeps {
  /** 传入路由实例后，每次路由切换（含异步取数渲染）再自检一次 */
  router?: Router
}

/** 被裁切的一层：内容超出自身高度，且自身没有滚动能力 */
export interface ScrollIssue {
  element: HTMLElement
  /** 命中的这一层是否就是页面根（否则是被某层中间容器裁掉的） */
  isPageRoot: boolean
  overflowY: string
  scrollHeight: number
  clientHeight: number
}

function defaultGetPageRoot(): HTMLElement | null {
  // App.vue：.main-content 内是涂鸦层 + .main-content__body（策略①滚动容器），
  // 页面根是滚动容器的第一个子元素
  return document.querySelector<HTMLElement>('.main-content__body > *')
}

function defaultGetOverflowY(element: HTMLElement): string {
  return getComputedStyle(element).overflowY
}

/** 元素自身内容是否被撑破（overflow: visible 时 scrollHeight 同样包含溢出内容） */
function overflows(element: HTMLElement): boolean {
  return element.scrollHeight > element.clientHeight + PIXEL_TOLERANCE
}

/** 把元素写成 <div#id.a.b> 便于在控制台里一眼认出 */
function describe(element: HTMLElement): string {
  const id = element.id ? '#' + element.id : ''
  const classes = Array.from(element.classList)
    .slice(0, 3)
    .map((name) => '.' + name)
    .join('')
  return '<' + element.tagName.toLowerCase() + id + classes + '>'
}

/**
 * 从页面根往上走，判定页面的溢出内容还够不够得着：
 *  - 先遇到能滚的一层 → 合法（内容滚得到）；
 *  - 先遇到 hidden / clip 且自身不可滚的一层 → 就是它把内容裁掉了，返回它；
 *  - overflow: visible 的溢出会继续往上冒，不在这里下结论；
 *  - 一直冒到 body / html 还没有滚动容器接手 → body / html 就是裁切点，返回首个溢出的那一层。
 */
export function detectClippedChain(
  pageRoot: HTMLElement,
  deps: Pick<ScrollGuardDeps, 'getOverflowY'> = {},
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

  // body / html 是视口本身，作为链尾兜底
  while (node && node !== document.body && node !== document.documentElement) {
    if (overflows(node)) {
      const overflowY = getOverflowY(node)
      if (SCROLLABLE_OVERFLOW.has(overflowY)) return null // 这一层能滚，内容够得着
      if (CLIPPING_OVERFLOW.has(overflowY)) return describeAt(node) // 这一层把内容裁死了
      spilled = spilled ?? describeAt(node) // visible：溢出继续往上冒
    }
    node = node.parentElement
  }
  // 冒到 html / body（两者都是 overflow: hidden）仍没有滚动容器接手
  return spilled
}

function formatIssue(issue: ScrollIssue): string {
  const whose = issue.isPageRoot ? '页面根' : '中间容器'
  return (
    '[scroll-guard] L0 契约被破：' + whose + ' ' + describe(issue.element) +
    ' 内容高 ' + issue.scrollHeight + 'px，超出可视区 ' + issue.clientHeight + 'px，' +
    '而 overflow-y 是 ' + issue.overflowY + '（不可滚）；祖先链上也没有滚动容器' +
    '（html / body / #app 均为 overflow: hidden），超出一屏的部分会被静默裁掉。' +
    '修法：让页面落在 .main-content__body（策略①）或 .doc-page--fixed 的 .doc-body（策略②）内，' +
    '并给链上每个 flex:1 补 min-height:0。'
  )
}

let installed = false

/**
 * 装一次自检：首屏、路由切换后、窗口尺寸变化时各跑一遍。
 * 同一层重复命中只告警一次，避免刷屏。
 */
export function installScrollGuard(options: ScrollGuardOptions = {}): void {
  if (!import.meta.env.DEV || typeof window === 'undefined') return
  if (installed) return // HMR 下 main.ts 会重复执行，装一次就够
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

  // 首屏要等一帧，否则拿到的是挂载前的空容器
  requestAnimationFrame(run)

  if (options.router) {
    // 路由切换后数据是异步回来的，等一拍再查，避免漏报
    options.router.afterEach(() => setTimeout(run, 400))
  }

  let resizeTimer: ReturnType<typeof setTimeout> | undefined
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(run, 300)
  })
}
