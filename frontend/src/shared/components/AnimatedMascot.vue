<script setup>
import { ref, onMounted } from "vue"
import { animate, steps } from "animejs"

const props = defineProps({
  size: { type: [Number, String], default: 28 },
})

const bodyRef = ref(null)
const leftArmRef = ref(null)
const rightArmRef = ref(null)
const leftEyeRef = ref(null)
const rightEyeRef = ref(null)
const leftLegRef = ref(null)
const rightLegRef = ref(null)

onMounted(() => {
  // Body gentle bounce
  animate(bodyRef.value, {
    translateY: [-1, 1],
    duration: 900,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })

  // Arms wave
  animate(leftArmRef.value, {
    rotate: [-10, 10],
    duration: 700,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })
  animate(rightArmRef.value, {
    rotate: [10, -10],
    duration: 700,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })

  // Legs swing
  animate(leftLegRef.value, {
    rotate: [-6, 6],
    duration: 800,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })
  animate(rightLegRef.value, {
    rotate: [6, -6],
    duration: 800,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })

  // Eyes blink
  animate([leftEyeRef.value, rightEyeRef.value], {
    scaleY: [1, 0.1],
    duration: 150,
    delay: 2000,
    loop: true,
    loopDelay: 2300,
    ease: steps(1),
  })
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 48 48" fill="none" class="animated-mascot">
    <!-- Antenna -->
    <line
      x1="24"
      y1="6"
      x2="24"
      y2="12"
      stroke="var(--mascot-stroke)"
      stroke-width="2"
      stroke-linecap="round"
    />
    <circle cx="24" cy="4" r="2" fill="var(--mascot-antenna-tip)" />

    <!-- Legs -->
    <path
      ref="leftLegRef"
      d="M20 34 L18 44"
      stroke="var(--mascot-stroke)"
      stroke-width="3"
      stroke-linecap="round"
    />
    <path
      ref="rightLegRef"
      d="M28 34 L30 44"
      stroke="var(--mascot-stroke)"
      stroke-width="3"
      stroke-linecap="round"
    />

    <!-- Arms -->
    <path
      ref="leftArmRef"
      d="M12 22 Q8 28 12 34"
      stroke="var(--mascot-stroke)"
      stroke-width="3"
      stroke-linecap="round"
    />
    <path
      ref="rightArmRef"
      d="M36 22 Q40 28 36 34"
      stroke="var(--mascot-stroke)"
      stroke-width="3"
      stroke-linecap="round"
    />

    <!-- Body -->
    <g ref="bodyRef">
      <rect x="12" y="12" width="24" height="24" rx="8" fill="var(--mascot-teal)" />
      <rect
        x="12"
        y="12"
        width="24"
        height="24"
        rx="8"
        fill="url(#mascotGradient)"
        opacity="0.85"
      />
      <!-- Screen face -->
      <rect x="16" y="17" width="16" height="12" rx="4" fill="var(--mascot-screen)" />
      <!-- Eyes -->
      <circle ref="leftEyeRef" cx="20" cy="22" r="2" fill="var(--mascot-ink)" />
      <circle ref="rightEyeRef" cx="28" cy="22" r="2" fill="var(--mascot-ink)" />
      <!-- Mouth -->
      <path
        d="M21 25 Q24 27 27 25"
        stroke="var(--mascot-ink)"
        stroke-width="1.5"
        stroke-linecap="round"
        fill="none"
      />
    </g>

    <defs>
      <linearGradient
        id="mascotGradient"
        x1="12"
        y1="12"
        x2="36"
        y2="36"
        gradientUnits="userSpaceOnUse"
      >
        <stop offset="0%" stop-color="var(--mascot-teal-light)" />
        <stop offset="100%" stop-color="var(--mascot-teal)" />
      </linearGradient>
    </defs>
  </svg>
</template>

<style scoped>
.animated-mascot {
  /* SVG 小人配色（图形绘制色，登记例外：色相固定、保留字面量） */
  --mascot-teal: var(--comp-mascot-teal); /* 机身主色 */
  --mascot-teal-light: var(--comp-mascot-teal-light); /* 机身渐变亮端 */
  --mascot-stroke: var(--comp-mascot-stroke); /* 触角 / 四肢描边 */
  --mascot-antenna-tip: var(--comp-mascot-antenna-tip); /* 触角顶端 */
  --mascot-screen: var(--comp-mascot-screen); /* 屏幕面板 */
  --mascot-ink: var(--comp-mascot-ink); /* 眼睛 / 嘴 */

  display: block;
  transform-origin: center bottom;
}
.animated-mascot * {
  transform-origin: center;
  transform-box: fill-box;
}
</style>
