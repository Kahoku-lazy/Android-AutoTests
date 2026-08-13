import { animate, stagger, createTimeline } from "animejs"

export function countUpFormatted(
  el: HTMLElement,
  from: number,
  to: number,
  duration = 1500,
  prefix = "",
  suffix = "",
): void {
  const obj = { val: from }
  animate(obj, {
    val: to,
    duration,
    ease: "outExpo",
    onUpdate: () => {
      el.textContent = prefix + Math.round(obj.val).toLocaleString() + suffix
    },
  })
}

export function countUp(el: HTMLElement, from: number, to: number, duration = 1000): void {
  const obj = { val: from }
  animate(obj, {
    val: to,
    modifier: Math.round,
    duration,
    ease: "outExpo",
    onUpdate: () => { el.textContent = String(obj.val) },
  })
}

export function pulse(targets: string | HTMLElement | HTMLElement[]): ReturnType<typeof animate> {
  return animate(targets, {
    scale: [1, 1.05, 1],
    opacity: [1, 0.7, 1],
    duration: 1200,
    loop: true,
    ease: "inOutSine",
  })
}

export function buttonPress(el: HTMLElement): void {
  animate(el, { scale: [1, 0.95, 1], duration: 200, ease: "outCubic" })
}

export function hoverFloat(el: HTMLElement): void {
  el.addEventListener("mouseenter", () => {
    animate(el, { translateY: -3, duration: 300, ease: "outCubic" })
  })
  el.addEventListener("mouseleave", () => {
    animate(el, { translateY: 0, duration: 300, ease: "outCubic" })
  })
}

export function blobParallax(container: HTMLElement): void {
  const blobs = container.querySelectorAll(".blob")
  if (!blobs.length) return
  container.addEventListener("mousemove", (e) => {
    const { clientX: x, clientY: y } = e
    const { innerWidth: w, innerHeight: h } = window
    animate(".blob-1", { translateX: (x / w - 0.5) * 30 + "px", translateY: (y / h - 0.5) * 30 + "px", duration: 2000, ease: "outCubic" })
    animate(".blob-2", { translateX: (x / w - 0.5) * -40 + "px", translateY: (y / h - 0.5) * -40 + "px", duration: 2500, ease: "outCubic" })
    animate(".blob-3", { translateX: (x / w - 0.5) * 20 + "px", translateY: (y / h - 0.5) * -20 + "px", duration: 1800, ease: "outCubic" })
  })
}

export function sparkleIn(el: HTMLElement): ReturnType<typeof animate> {
  return animate(el, { opacity: [0, 1], scale: [0.92, 1], duration: 350, ease: "outBack" })
}

export function shake(el: HTMLElement): ReturnType<typeof animate> {
  return animate(el, { translateX: [0, -10, 10, -8, 8, -4, 4, 0], duration: 500, ease: "inOutSine" })
}

export function bounceItem(el: HTMLElement, delay = 0): ReturnType<typeof animate> {
  return animate(el, { translateX: [-16, 0], opacity: [0, 1], delay, duration: 500, ease: "outCubic" })
}

export function sidebarNavEnter(targets: string | HTMLElement | NodeList): ReturnType<typeof animate> {
  return animate(targets, { translateX: [-16, 0], opacity: [0, 1], delay: stagger(50), duration: 450, ease: "outCubic" })
}

export function rippleEffect(event: MouseEvent, color = "rgba(255,255,255,0.35)"): void {
  const btn = event.currentTarget as HTMLElement
  const circle = document.createElement("span")
  const d = Math.max(btn.clientWidth, btn.clientHeight)
  const rect = btn.getBoundingClientRect()
  circle.style.cssText = `
    position: absolute; border-radius: 50%;
    width: ${d}px; height: ${d}px;
    left: ${event.clientX - rect.left - d / 2}px;
    top: ${event.clientY - rect.top - d / 2}px;
    background: ${color}; pointer-events: none;
  `
  circle.classList.add("ripple")
  btn.appendChild(circle)
  animate(circle, {
    scale: [0, 2], opacity: [1, 0], duration: 600, ease: "outExpo",
    onComplete: () => circle.remove(),
  })
}

export function glowPulse(targets: string, color = "#a2d2ff"): ReturnType<typeof animate> {
  return animate(targets, {
    boxShadow: [`0 0 0 0 ${color}00`, `0 0 20px 4px ${color}40`, `0 0 0 0 ${color}00`],
    duration: 2000, loop: true, ease: "inOutSine",
  })
}

export function cardTilt(el: HTMLElement, intensity = 8): () => void {
  const onMove = (e: MouseEvent) => {
    const rect = el.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    animate(el, { rotateY: x * intensity, rotateX: -y * intensity, translateZ: 10, duration: 400, ease: "outCubic" })
  }
  const onLeave = () => {
    animate(el, { rotateY: 0, rotateX: 0, translateZ: 0, duration: 600, ease: "outElastic(1, 0.5)" })
  }
  el.addEventListener("mousemove", onMove)
  el.addEventListener("mouseleave", onLeave)
  return () => { el.removeEventListener("mousemove", onMove); el.removeEventListener("mouseleave", onLeave) }
}

export function staggerReveal(targets: string | HTMLElement | HTMLElement[] | NodeList, delay = 80, fromScale = 0.85): ReturnType<typeof animate> {
  return animate(targets, { opacity: [0, 1], scale: [fromScale, 1], translateY: [24, 0], delay: stagger(delay), duration: 600, ease: "outBack(1.5)" })
}

export function progressFill(el: HTMLElement, from = 0, to = 100, duration = 1200): void {
  const obj = { val: from }
  animate(obj, { val: to, duration, ease: "outExpo", onUpdate: () => { el.style.width = obj.val + "%" } })
}

export function ringProgress(el: SVGElement, from = 0, to = 100, duration = 1500): void {
  const circumference = 2 * Math.PI * 45
  el.style.strokeDasharray = String(circumference)
  el.style.strokeDashoffset = String(circumference)
  const obj = { val: from }
  animate(obj, { val: to, duration, ease: "outExpo", onUpdate: () => { el.style.strokeDashoffset = String(circumference - (obj.val / 100) * circumference) } })
}

export function bannerSlideIn(el: HTMLElement): ReturnType<typeof animate> {
  return animate(el, { translateY: [-40, 0], opacity: [0, 1], duration: 500, ease: "outBack(1.3)" })
}

export function particleBurst(x: number, y: number, _container: unknown, count = 12): void {
  const colors = ["#a2d2ff", "#bde0fe", "#d4eaff", "#e2ece9", "#eef7ff"]
  for (let i = 0; i < count; i++) {
    const dot = document.createElement("div")
    const angle = (Math.PI * 2 * i) / count
    const distance = 40 + Math.random() * 40
    dot.style.cssText = `position:fixed;left:${x}px;top:${y}px;width:6px;height:6px;border-radius:50%;background:${colors[i % colors.length]};pointer-events:none;z-index:9999`
    document.body.appendChild(dot)
    animate(dot, { translateX: Math.cos(angle) * distance, translateY: Math.sin(angle) * distance, opacity: [1, 0], scale: [1, 0], duration: 600 + Math.random() * 300, ease: "outExpo", onComplete: () => dot.remove() })
  }
}

export function typewriter(el: HTMLElement, text: string, speed = 40): () => void {
  el.textContent = ""
  let i = 0
  const interval = setInterval(() => { el.textContent += text[i]; i++; if (i >= text.length) clearInterval(interval) }, speed)
  return () => clearInterval(interval)
}

export function sequentialHighlight(targets: string | HTMLElement, color = "#a2d2ff", interval = 300): ReturnType<typeof createTimeline> {
  return createTimeline()
    .add(staggerReveal(targets, interval) as unknown as Parameters<ReturnType<typeof createTimeline>["add"]>[0])
    .add(animate(targets, { boxShadow: ["none", `0 0 0 2px ${color}40`, "none"], delay: stagger(interval), duration: 600, ease: "inOutSine" }) as unknown as Parameters<ReturnType<typeof createTimeline>["add"]>[0], "+=200")
}

export function skeletonShimmer(targets: string | HTMLElement): ReturnType<typeof animate> {
  return animate(targets, { backgroundPosition: ["200% 0", "-200% 0"], duration: 1600, loop: true, ease: "linear" })
}

export function svgDraw(targets: string | SVGElement | NodeList, duration = 1200): ReturnType<typeof animate> {
  const els = typeof targets === "string" ? document.querySelectorAll(targets) : targets
  const elements = Array.from(els as NodeListOf<SVGGeometryElement> || [])
  elements.forEach((el: SVGGeometryElement) => {
    const len = el.getTotalLength()
    el.style.strokeDasharray = String(len)
    el.style.strokeDashoffset = String(len)
  })
  return animate(targets, { strokeDashoffset: [animeSetDashoffset, 0], duration, delay: stagger(100), ease: "inOutSine" })
}

function animeSetDashoffset(el: SVGGeometryElement): number {
  return el.getTotalLength()
}

export function fadeSwap(leaveEl: HTMLElement, enterEl: HTMLElement, duration = 300): ReturnType<typeof createTimeline> {
  return createTimeline()
    .add(animate(leaveEl, { opacity: [1, 0], duration, ease: "inCubic" }) as unknown as Parameters<ReturnType<typeof createTimeline>["add"]>[0])
    .add(animate(enterEl, { opacity: [0, 1], duration, ease: "outCubic" }) as unknown as Parameters<ReturnType<typeof createTimeline>["add"]>[0], `-=${duration * 0.6}`)
}

export function bounceBadge(el: HTMLElement): ReturnType<typeof animate> {
  return animate(el, { translateY: [0, -6, 0, -3, 0], scale: [1, 1.2, 1, 1.1, 1], duration: 600, ease: "inOutSine" })
}

export function slideIn(el: HTMLElement, direction: "left" | "right" | "top" | "bottom" = "left", distance = 40, duration = 500): ReturnType<typeof animate> {
  const dirMap = {
    left: { translateX: [-distance, 0] },
    right: { translateX: [distance, 0] },
    top: { translateY: [-distance, 0] },
    bottom: { translateY: [distance, 0] },
  }
  return animate(el, { ...dirMap[direction], opacity: [0, 1], duration, ease: "outCubic" })
}

export function selectPop(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  el.classList.add("wb-select-ring")
  return animate(el, {
    scale: [1, 1.03, 1], duration: 380, ease: "outBack(1.6)",
    onComplete: () => { setTimeout(() => el.classList.remove("wb-select-ring"), 280) },
  })
}

export function iconBounce(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  return animate(el, { scale: [1, 1.18, 0.92, 1.06, 1], rotate: [0, -8, 6, -3, 0], duration: 520, ease: "outCubic" })
}

export function iconWiggle(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  return animate(el, { rotate: [-6, 6, -4, 4, 0], duration: 700, ease: "inOutSine" })
}

export function loadingDots(targets: string | HTMLElement | NodeList): ReturnType<typeof animate> {
  return animate(targets, { scale: [1, 1.35, 1], opacity: [0.55, 1, 0.55], delay: stagger(120), duration: 720, loop: true, ease: "inOutSine" })
}

export function loadingSpin(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  return animate(el, { rotate: "1turn", duration: 900, loop: true, ease: "linear" })
}

export function contentSwap(el: HTMLElement): ReturnType<typeof animate> | undefined {
  if (!el) return
  return animate(el, { opacity: [0, 1], translateY: [10, 0], duration: 320, ease: "outCubic" })
}

export function pressFeedback(el: HTMLElement, event?: MouseEvent): void {
  if (!el) return
  buttonPress(el)
  if (event?.clientX != null) particleBurst(event.clientX, event.clientY, null, 8)
}
