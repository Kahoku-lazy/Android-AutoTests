<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(
  defineProps<{
    color?: string

    tone?: string

    tilt?: number

    pin?: boolean
  }>(),
  {
    color: "",
    tone: "",
    tilt: 0.3,
    pin: true,
  },
)

const COLOR_TONE: Record<string, string> = {
  blue: "var(--c-workflow)",
  green: "var(--c-device)",
  teal: "var(--c-case)",
  purple: "var(--c-element)",
  pink: "var(--c-runner)",
  yellow: "var(--c-dashboard)",
  brown: "var(--c-report)",
  red: "var(--c-runner)",
  orange: "var(--c-ai)",
  dashboard: "var(--c-dashboard)",
  device: "var(--c-device)",
  element: "var(--c-element)",
  case: "var(--c-case)",
  runner: "var(--c-runner)",
  report: "var(--c-report)",
  ai: "var(--c-ai)",
  workflow: "var(--c-workflow)",
}

const resolvedTone = computed(() => {
  if (props.tone) return props.tone
  const key = props.color.replace(/^app-/, "")
  return COLOR_TONE[key] || "var(--c-dashboard)"
})

const rootStyle = computed(() => ({
  "--ac-accent": resolvedTone.value,
  "--ac-tilt": `${props.tilt}deg`,
}))

const rootClass = computed(() => ["ac-card", props.pin ? "ac-card--pin" : ""])
</script>

<template>
  <el-card :class="rootClass" :style="rootStyle" shadow="never">
    <span v-if="pin" class="ac-card__pin" aria-hidden="true" />
    <template v-for="(_, slot) in $slots" :key="slot" #[slot]>
      <slot :name="slot" />
    </template>
  </el-card>
</template>
