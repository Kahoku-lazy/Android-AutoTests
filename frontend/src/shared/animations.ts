import { animate, stagger } from "animejs"

/** 用户启用「减少动效」时短路 JS 编排；无 window 时视为不降级 */
function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

type AnimateTarget = Parameters<typeof animate>[0]
type AnimateParams = Parameters<typeof animate>[1]

/** 降级时以 duration: 0 落到终态，保持 animejs 返回类型 */
function runMotion(targets: AnimateTarget, params: AnimateParams): ReturnType<typeof animate> {
  if (!prefersReducedMotion()) {
    return animate(targets, params)
  }
  return animate(targets, { ...params, duration: 0, delay: 0, loop: false })
}

export function countUpFormatted(
  el: HTMLElement,
  from: number,
  to: number,
  duration = 1500,
  prefix = "",
  suffix = "",
  decimals = 0,
): void {
  if (prefersReducedMotion()) {
    el.textContent =
      prefix +
      to.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }) +
      suffix
    return
  }
  const obj = { val: from }
  runMotion(obj, {
    val: to,
    duration,
    ease: "outExpo",
    onUpdate: () => {
      el.textContent =
        prefix +
        obj.val.toLocaleString(undefined, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        }) +
        suffix
    },
  })
}

export function sidebarNavEnter(
  targets: string | HTMLElement | NodeList,
): ReturnType<typeof animate> {
  return runMotion(targets, {
    translateX: [-16, 0],
    opacity: [0, 1],
    delay: stagger(50),
    duration: 450,
    ease: "outCubic",
  })
}

export function staggerReveal(
  targets: string | HTMLElement | HTMLElement[] | NodeList,
  delay = 80,
  fromScale = 0.85,
): ReturnType<typeof animate> {
  return runMotion(targets, {
    opacity: [0, 1],
    scale: [fromScale, 1],
    translateY: [24, 0],
    delay: stagger(delay),
    duration: 600,
    ease: "outBack(1.5)",
  })
}

export function selectPop(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  el.classList.add("wb-select-ring")
  return runMotion(el, {
    scale: [1, 1.03, 1],
    duration: 380,
    ease: "outBack(1.6)",
    onComplete: () => {
      setTimeout(() => el.classList.remove("wb-select-ring"), 280)
    },
  })
}

export function iconBounce(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  return runMotion(el, {
    scale: [1, 1.18, 0.92, 1.06, 1],
    rotate: [0, -8, 6, -3, 0],
    duration: 520,
    ease: "outCubic",
  })
}

export function loadingDots(targets: string | HTMLElement | NodeList): ReturnType<typeof animate> {
  return runMotion(targets, {
    scale: [1, 1.35, 1],
    opacity: [0.55, 1, 0.55],
    delay: stagger(120),
    duration: 720,
    loop: true,
    ease: "inOutSine",
  })
}
