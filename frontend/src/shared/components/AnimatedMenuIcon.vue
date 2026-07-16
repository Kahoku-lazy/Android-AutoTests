<script setup>
import { ref, onMounted, watch } from 'vue'
import { animate, steps } from 'animejs'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
  active: { type: Boolean, default: false },
})

const svgRef = ref(null)

const ICONS = {
  dashboard: {
    svg: `
      <rect data-anim="a" x="3" y="14" width="4" height="7" rx="1" fill="currentColor"/>
      <rect data-anim="b" x="10" y="10" width="4" height="11" rx="1" fill="currentColor"/>
      <rect data-anim="c" x="17" y="6" width="4" height="15" rx="1" fill="currentColor"/>
    `,
  },
  devices: {
    svg: `
      <rect x="6" y="2" width="12" height="20" rx="3" stroke="currentColor" stroke-width="2" fill="none"/>
      <rect data-anim="a" x="9" y="5" width="6" height="11" rx="1" fill="currentColor" opacity="0.6"/>
      <circle cx="12" cy="19" r="1" fill="currentColor"/>
    `,
  },
  elements: {
    svg: `
      <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/>
      <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
      <circle data-anim="a" cx="12" cy="12" r="1.5" fill="currentColor"/>
      <line data-anim="b" x1="12" y1="1" x2="12" y2="4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <line data-anim="c" x1="12" y1="20" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    `,
  },
  'element-mgr': {
    svg: `
      <polygon data-anim="a" points="12,3 21,8 12,13 3,8" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
      <polygon data-anim="b" points="3,12 12,17 21,12" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
      <polygon data-anim="c" points="3,16 12,21 21,16" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
    `,
  },
  cases: {
    svg: `
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
      <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
      <polyline data-anim="a" points="9 14 7 16 9 18" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline data-anim="b" points="14 14 16 16 14 18" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    `,
  },
  workflow: {
    svg: `
      <circle data-anim="a" cx="6" cy="8" r="2.5" fill="currentColor"/>
      <circle data-anim="b" cx="18" cy="8" r="2.5" fill="currentColor"/>
      <circle data-anim="c" cx="12" cy="18" r="2.5" fill="currentColor"/>
      <path d="M8.2 9.2 L10.5 15.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
      <path d="M15.8 9.2 L13.5 15.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
      <path d="M8.5 8 H15.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    `,
  },
  runner: {
    svg: `
      <circle data-anim="a" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/>
      <polygon data-anim="b" points="10 8 16 12 10 16" fill="currentColor"/>
    `,
  },
  reports: {
    svg: `
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
      <rect data-anim="a" x="8" y="16" width="3" height="3" rx="0.5" fill="currentColor"/>
      <rect data-anim="b" x="12" y="13" width="3" height="6" rx="0.5" fill="currentColor"/>
      <polyline data-anim="c" points="7 13 10 10 13 12 16 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    `,
  },
  'ai-assistant': {
    svg: `
      <rect x="7" y="7" width="10" height="9" rx="2" stroke="currentColor" stroke-width="2" fill="none"/>
      <circle data-anim="a" cx="10" cy="11" r="1.2" fill="currentColor"/>
      <circle data-anim="b" cx="14" cy="11" r="1.2" fill="currentColor"/>
      <path data-anim="c" d="M10 14 Q12 15 14 14" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>
      <line x1="12" y1="4" x2="12" y2="7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <circle cx="12" cy="3" r="1.2" fill="currentColor"/>
      <line x1="5" y1="10" x2="7" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <line x1="17" y1="10" x2="19" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    `,
  },
}

function q(sel) {
  return svgRef.value?.querySelectorAll(`[data-anim="${sel}"]`) || []
}

const ANIMATIONS = {
  dashboard: () => {
    animate(q('a'), {
      scaleY: [1, 0.6, 1],
      duration: 1200,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('b'), {
      scaleY: [1, 0.5, 1],
      duration: 1200,
      delay: 120,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('c'), {
      scaleY: [1, 0.4, 1],
      duration: 1200,
      delay: 240,
      loop: true,
      ease: 'easeInOutSine',
    })
  },
  devices: () => {
    animate(q('a'), {
      opacity: [0.4, 0.9, 0.4],
      duration: 1500,
      loop: true,
      ease: 'easeInOutSine',
    })
  },
  elements: () => {
    animate(q('b'), {
      opacity: [0, 1, 0],
      duration: 1500,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('c'), {
      opacity: [0, 1, 0],
      duration: 1500,
      delay: 300,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('a'), {
      scale: [1, 1.4, 1],
      duration: 1500,
      loop: true,
      ease: 'easeInOutSine',
    })
  },
  'element-mgr': () => {
    animate(q('a'), {
      translateY: [0, -2, 0],
      duration: 1800,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('b'), {
      translateY: [0, -2, 0],
      duration: 1800,
      delay: 200,
      loop: true,
      ease: 'easeInOutSine',
    })
    animate(q('c'), {
      translateY: [0, -2, 0],
      duration: 1800,
      delay: 400,
      loop: true,
      ease: 'easeInOutSine',
    })
  },
  cases: () => {
    animate(q('a'), {
      opacity: [0.3, 1],
      duration: 800,
      loop: true,
      direction: 'alternate',
      ease: 'easeInOutSine',
    })
    animate(q('b'), {
      opacity: [1, 0.3],
      duration: 800,
      loop: true,
      direction: 'alternate',
      ease: 'easeInOutSine',
    })
  },
  runner: () => {
    animate(q('a'), {
      scale: [1, 1.08, 1],
      duration: 900,
      loop: true,
      ease: 'easeInOutSine',
    })
  },
  reports: () => {
    animate(q('a'), {
      scaleY: [0.5, 1],
      duration: 1200,
      loop: true,
      direction: 'alternate',
      ease: 'easeInOutSine',
    })
    animate(q('b'), {
      scaleY: [0.5, 1],
      duration: 1200,
      delay: 200,
      loop: true,
      direction: 'alternate',
      ease: 'easeInOutSine',
    })
  },
  'ai-assistant': () => {
    animate(q('a'), {
      scaleY: [1, 0.1],
      duration: 150,
      delay: 2200,
      loop: true,
      loopDelay: 2500,
      ease: steps(1),
    })
    animate(q('b'), {
      scaleY: [1, 0.1],
      duration: 150,
      delay: 2200,
      loop: true,
      loopDelay: 2500,
      ease: steps(1),
    })
  },
}

function startAnim() {
  const fn = ANIMATIONS[props.name]
  if (fn) fn()
}

onMounted(() => {
  setTimeout(startAnim, 100)
})
</script>

<template>
  <span class="menu-icon" :style="{ width: size + 'px', height: size + 'px' }">
    <svg ref="svgRef" :width="size" :height="size" viewBox="0 0 24 24" fill="none" v-html="ICONS[name]?.svg || ''"></svg>
  </span>
</template>

<style scoped>
.menu-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.menu-icon svg * {
  transform-origin: center;
  transform-box: fill-box;
}
</style>
