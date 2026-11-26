import { animate, stagger } from "animejs"

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

type AnimateTarget = Parameters<typeof animate>[0]
type AnimateParams = Parameters<typeof animate>[1]

function runMotion(targets: AnimateTarget, params: AnimateParams): ReturnType<typeof animate> {
  if (!prefersReducedMotion()) {
    return animate(targets, params)
  }
  return animate(targets, { ...params, duration: 0, delay: 0, loop: false })
}

export function formatSignificant(value: number, digits = 3): string {
  if (!Number.isFinite(value) || value === 0) return "0"
  const negative = value < 0
  const abs = Math.abs(value)
  const exponent = Math.floor(Math.log10(abs))
  const scale = 10 ** (digits - 1 - exponent)
  const rounded = Math.round(abs * scale) / scale
  const roundedExponent = Math.floor(Math.log10(rounded))
  const fractionDigits = Math.max(0, digits - 1 - roundedExponent)
  const text = rounded.toLocaleString(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
    useGrouping: rounded >= 1000,
  })
  return negative ? `-${text}` : text
}

export function countUpFormatted(
  el: HTMLElement,
  from: number,
  to: number,
  duration = 1500,
  prefix = "",
  suffix = "",
  decimals = 0,
  significantDigits = 0,
): void {
  const render = (n: number) =>
    significantDigits > 0
      ? formatSignificant(n, significantDigits)
      : n.toLocaleString(undefined, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        })
  if (prefersReducedMotion()) {
    el.textContent = prefix + render(to) + suffix
    return
  }
  const obj = { val: from }
  runMotion(obj, {
    val: to,
    duration,
    ease: "outExpo",
    onUpdate: () => {
      el.textContent = prefix + render(obj.val) + suffix
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
