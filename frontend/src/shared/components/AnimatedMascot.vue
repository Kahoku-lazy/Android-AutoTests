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
  animate(bodyRef.value, {
    translateY: [-1, 1],
    duration: 900,
    loop: true,
    direction: "alternate",
    ease: "easeInOutSine",
  })

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

      <rect x="16" y="17" width="16" height="12" rx="4" fill="var(--mascot-screen)" />

      <circle ref="leftEyeRef" cx="20" cy="22" r="2" fill="var(--mascot-ink)" />
      <circle ref="rightEyeRef" cx="28" cy="22" r="2" fill="var(--mascot-ink)" />

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
  --mascot-teal: var(--comp-mascot-teal);
  --mascot-teal-light: var(--comp-mascot-teal-light);
  --mascot-stroke: var(--comp-mascot-stroke);
  --mascot-antenna-tip: var(--comp-mascot-antenna-tip);
  --mascot-screen: var(--comp-mascot-screen);
  --mascot-ink: var(--comp-mascot-ink);

  display: block;
  transform-origin: center bottom;
}
.animated-mascot * {
  transform-origin: center;
  transform-box: fill-box;
}
</style>
