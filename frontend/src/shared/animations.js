import { animate, stagger, createTimeline } from 'animejs'

// ── Page transitions ──
export function pageEnter(el, done) {
  animate(el, {
    opacity: [0, 1],
    translateY: [20, 0],
    duration: 400,
    ease: 'outCubic',
    onComplete: done,
  })
}

export function pageLeave(el, done) {
  animate(el, {
    opacity: [1, 0],
    translateY: [0, -15],
    duration: 250,
    ease: 'inCubic',
    onComplete: done,
  })
}

// ── Stagger entrance (for cards, list items) ──
export function staggerIn(targets, delay = 60) {
  return animate(targets, {
    opacity: [0, 1],
    translateY: [30, 0],
    delay: stagger(delay),
    duration: 500,
    ease: 'outCubic',
  })
}

// ── Number count-up ──
export function countUp(el, from, to, duration = 1000) {
  const obj = { val: from }
  animate(obj, {
    val: to,
    modifier: Math.round,
    duration,
    ease: 'outExpo',
    onUpdate: () => { el.textContent = obj.val },
  })
}

// ── Pulse (for loading indicators) ──
export function pulse(targets) {
  return animate(targets, {
    scale: [1, 1.05, 1],
    opacity: [1, 0.7, 1],
    duration: 1200,
    loop: true,
    ease: 'inOutSine',
  })
}

// ── Button ripple / press ──
export function buttonPress(el) {
  animate(el, { scale: [1, 0.95, 1], duration: 200, ease: 'outCubic' })
}

// ── Hover float ──
export function hoverFloat(el) {
  el.addEventListener('mouseenter', () => {
    animate(el, { translateY: -3, duration: 300, ease: 'outCubic' })
  })
  el.addEventListener('mouseleave', () => {
    animate(el, { translateY: 0, duration: 300, ease: 'outCubic' })
  })
}

// ── Blob parallax on mouse move ──
export function blobParallax(container) {
  const blobs = container.querySelectorAll('.blob')
  if (!blobs.length) return
  container.addEventListener('mousemove', (e) => {
    const { clientX: x, clientY: y } = e
    const { innerWidth: w, innerHeight: h } = window
    animate('.blob-1', {
      translateX: (x / w - 0.5) * 30 + 'px',
      translateY: (y / h - 0.5) * 30 + 'px',
      duration: 2000, ease: 'outCubic',
    })
    animate('.blob-2', {
      translateX: (x / w - 0.5) * -40 + 'px',
      translateY: (y / h - 0.5) * -40 + 'px',
      duration: 2500, ease: 'outCubic',
    })
    animate('.blob-3', {
      translateX: (x / w - 0.5) * 20 + 'px',
      translateY: (y / h - 0.5) * -20 + 'px',
      duration: 1800, ease: 'outCubic',
    })
  })
}

// ── Entrance sparkle (for dialogs/modals) ──
export function sparkleIn(el) {
  return animate(el, {
    opacity: [0, 1],
    scale: [0.92, 1],
    duration: 350,
    ease: 'outBack',
  })
}

// ── Shake (for error states) ──
export function shake(el) {
  return animate(el, {
    translateX: [0, -10, 10, -8, 8, -4, 4, 0],
    duration: 500,
    ease: 'inOutSine',
  })
}

// ── Sidebar item bounce (light slide-in, Glass style) ──
export function bounceItem(el, delay = 0) {
  return animate(el, {
    translateX: [-16, 0],
    opacity: [0, 1],
    delay,
    duration: 500,
    ease: 'outCubic',
  })
}

// ── Sidebar nav stagger entrance (Plan B) ──
export function sidebarNavEnter(targets) {
  return animate(targets, {
    translateX: [-16, 0],
    opacity: [0, 1],
    delay: stagger(50),
    duration: 450,
    ease: 'outCubic',
  })
}

// ═══════════════════════════════════════════
// ✨ Enhanced Animation Presets (v2)
// ═══════════════════════════════════════════

// ── Ripple effect on click ──
export function rippleEffect(event, color = 'rgba(255,255,255,0.35)') {
  const btn = event.currentTarget
  const circle = document.createElement('span')
  const d = Math.max(btn.clientWidth, btn.clientHeight)
  const rect = btn.getBoundingClientRect()
  circle.style.cssText = `
    position: absolute; border-radius: 50%;
    width: ${d}px; height: ${d}px;
    left: ${event.clientX - rect.left - d / 2}px;
    top: ${event.clientY - rect.top - d / 2}px;
    background: ${color}; pointer-events: none;
  `
  circle.classList.add('ripple')
  btn.appendChild(circle)
  animate(circle, {
    scale: [0, 2],
    opacity: [1, 0],
    duration: 600,
    ease: 'outExpo',
    onComplete: () => circle.remove(),
  })
}

// ── Glow pulse (subtle breathing glow) ──
export function glowPulse(targets, color = '#ffafcc') {
  return animate(targets, {
    boxShadow: [
      `0 0 0 0 ${color}00`,
      `0 0 20px 4px ${color}40`,
      `0 0 0 0 ${color}00`,
    ],
    duration: 2000,
    loop: true,
    ease: 'inOutSine',
  })
}

// ── 3D Card tilt on hover ──
export function cardTilt(el, intensity = 8) {
  const onMove = (e) => {
    const rect = el.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    animate(el, {
      rotateY: x * intensity,
      rotateX: -y * intensity,
      translateZ: 10,
      duration: 400,
      ease: 'outCubic',
    })
  }
  const onLeave = () => {
    animate(el, {
      rotateY: 0, rotateX: 0, translateZ: 0,
      duration: 600, ease: 'outElastic(1, 0.5)',
    })
  }
  el.addEventListener('mousemove', onMove)
  el.addEventListener('mouseleave', onLeave)
  return () => {
    el.removeEventListener('mousemove', onMove)
    el.removeEventListener('mouseleave', onLeave)
  }
}

// ── Animated number with comma formatting ──
export function countUpFormatted(el, from, to, duration = 1500, prefix = '', suffix = '') {
  const obj = { val: from }
  animate(obj, {
    val: to,
    duration,
    ease: 'outExpo',
    onUpdate: () => {
      el.textContent = prefix + Math.round(obj.val).toLocaleString() + suffix
    },
  })
}

// ── Stagger reveal with scale + fade ──
export function staggerReveal(targets, delay = 80, fromScale = 0.85) {
  return animate(targets, {
    opacity: [0, 1],
    scale: [fromScale, 1],
    translateY: [24, 0],
    delay: stagger(delay),
    duration: 600,
    ease: 'outBack(1.5)',
  })
}

// ── Progress bar fill ──
export function progressFill(el, from = 0, to = 100, duration = 1200) {
  const obj = { val: from }
  animate(obj, {
    val: to,
    duration,
    ease: 'outExpo',
    onUpdate: () => {
      el.style.width = obj.val + '%'
    },
  })
}

// ── Circular progress ring ──
export function ringProgress(el, from = 0, to = 100, duration = 1500) {
  const circumference = 2 * Math.PI * 45 // r=45
  el.style.strokeDasharray = circumference
  el.style.strokeDashoffset = circumference
  const obj = { val: from }
  animate(obj, {
    val: to,
    duration,
    ease: 'outExpo',
    onUpdate: () => {
      const offset = circumference - (obj.val / 100) * circumference
      el.style.strokeDashoffset = offset
    },
  })
}

// ── Float-in notification banner ──
export function bannerSlideIn(el) {
  return animate(el, {
    translateY: [-40, 0],
    opacity: [0, 1],
    duration: 500,
    ease: 'outBack(1.3)',
  })
}

// ── Particle burst on action ──
export function particleBurst(x, y, container, count = 12) {
  const colors = ['#ffafcc', '#a2d2ff', '#bde0fe', '#cdb4db', '#ffc8dd']
  for (let i = 0; i < count; i++) {
    const dot = document.createElement('div')
    const angle = (Math.PI * 2 * i) / count
    const distance = 40 + Math.random() * 40
    dot.style.cssText = `
      position: fixed; left: ${x}px; top: ${y}px;
      width: 6px; height: 6px; border-radius: 50%;
      background: ${colors[i % colors.length]};
      pointer-events: none; z-index: 9999;
    `
    document.body.appendChild(dot)
    animate(dot, {
      translateX: Math.cos(angle) * distance,
      translateY: Math.sin(angle) * distance,
      opacity: [1, 0],
      scale: [1, 0],
      duration: 600 + Math.random() * 300,
      ease: 'outExpo',
      onComplete: () => dot.remove(),
    })
  }
}

// ── Typewriter text effect ──
export function typewriter(el, text, speed = 40) {
  el.textContent = ''
  let i = 0
  const interval = setInterval(() => {
    el.textContent += text[i]
    i++
    if (i >= text.length) clearInterval(interval)
  }, speed)
  return () => clearInterval(interval)
}

// ── Sequential highlight (staggered border glow) ──
export function sequentialHighlight(targets, color = '#a2d2ff', interval = 300) {
  return createTimeline()
    .add(staggerReveal(targets, interval))
    .add(animate(targets, {
      boxShadow: [
        'none',
        `0 0 0 2px ${color}40`,
        'none',
      ],
      delay: stagger(interval),
      duration: 600,
      ease: 'inOutSine',
    }), '+=200')
}

// ── Skeleton shimmer ──
export function skeletonShimmer(targets) {
  return animate(targets, {
    backgroundPosition: ['200% 0', '-200% 0'],
    duration: 1600,
    loop: true,
    ease: 'linear',
  })
}

// ── Elastic scale on hover ──
export function elasticHover(el) {
  el.addEventListener('mouseenter', () => {
    animate(el, { scale: 1.04, duration: 300, ease: 'outBack(1.7)' })
  })
  el.addEventListener('mouseleave', () => {
    animate(el, { scale: 1, duration: 300, ease: 'outBack(1.7)' })
  })
}

// ── SVG path draw animation ──
export function svgDraw(targets, duration = 1200) {
  // Get total length of each target
  const els = typeof targets === 'string' ? document.querySelectorAll(targets) : targets
  const elements = Array.from(els || [])
  elements.forEach(el => {
    const len = el.getTotalLength()
    el.style.strokeDasharray = len
    el.style.strokeDashoffset = len
  })
  return animate(targets, {
    strokeDashoffset: [anime.setDashoffset, 0],
    duration,
    delay: stagger(100),
    ease: 'inOutSine',
  })
}

// ── Fade swap (for tab/content switching) ──
export function fadeSwap(leaveEl, enterEl, duration = 300) {
  return createTimeline()
    .add(animate(leaveEl, { opacity: [1, 0], duration, ease: 'inCubic' }))
    .add(animate(enterEl, { opacity: [0, 1], duration, ease: 'outCubic' }), `-=${duration * 0.6}`)
}

// ── Bounce badge notification ──
export function bounceBadge(el) {
  return animate(el, {
    translateY: [0, -6, 0, -3, 0],
    scale: [1, 1.2, 1, 1.1, 1],
    duration: 600,
    ease: 'inOutSine',
  })
}

// ── Slide-in from direction ──
export function slideIn(el, direction = 'left', distance = 40, duration = 500) {
  const dirMap = {
    left: { translateX: [-distance, 0] },
    right: { translateX: [distance, 0] },
    top: { translateY: [-distance, 0] },
    bottom: { translateY: [distance, 0] },
  }
  return animate(el, {
    ...dirMap[direction],
    opacity: [0, 1],
    duration,
    ease: 'outCubic',
  })
}

// ═══════════════════════════════════════════
// ✨ Motion System v3 — 加载 / 选中 / 图标
// ═══════════════════════════════════════════

/** 选择特效：短暂放大 + 描边闪烁 */
export function selectPop(el) {
  if (!el) return
  el.classList.add('wb-select-ring')
  return animate(el, {
    scale: [1, 1.03, 1],
    duration: 380,
    ease: 'outBack(1.6)',
    onComplete: () => {
      setTimeout(() => el.classList.remove('wb-select-ring'), 280)
    },
  })
}

/** 图标弹跳（顶栏 brand-mark / 侧栏图标） */
export function iconBounce(el) {
  if (!el) return
  return animate(el, {
    scale: [1, 1.18, 0.92, 1.06, 1],
    rotate: [0, -8, 6, -3, 0],
    duration: 520,
    ease: 'outCubic',
  })
}

/** 图标持续微动（悬停装饰） */
export function iconWiggle(el) {
  if (!el) return
  return animate(el, {
    rotate: [-6, 6, -4, 4, 0],
    duration: 700,
    ease: 'inOutSine',
  })
}

/**
 * 三点加载跳动；返回动画实例
 * @param {NodeList|Element[]|string} targets
 */
export function loadingDots(targets) {
  return animate(targets, {
    scale: [1, 1.35, 1],
    opacity: [0.55, 1, 0.55],
    delay: stagger(120),
    duration: 720,
    loop: true,
    ease: 'inOutSine',
  })
}

/** 旋转环加载 */
export function loadingSpin(el) {
  if (!el) return
  return animate(el, {
    rotate: '1turn',
    duration: 900,
    loop: true,
    ease: 'linear',
  })
}

/** Tab / 内容切换淡入 */
export function contentSwap(el) {
  if (!el) return
  return animate(el, {
    opacity: [0, 1],
    translateY: [10, 0],
    duration: 320,
    ease: 'outCubic',
  })
}

/** 按键点击回馈 + 可选彩色粒子 */
export function pressFeedback(el, event) {
  if (!el) return
  buttonPress(el)
  if (event?.clientX != null) {
    particleBurst(event.clientX, event.clientY, null, 8)
  }
}
