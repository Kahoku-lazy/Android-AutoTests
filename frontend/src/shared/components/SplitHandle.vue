<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

const props = withDefaults(
  defineProps<{
    modelValue: number

    min?: number

    max?: number

    defaultWidth?: number

    minRightWidth?: number
    label?: string
  }>(),
  {
    min: 220,
    max: 560,
    defaultWidth: 280,
    minRightWidth: 360,
    label: "调整左栏宽度",
  },
)

const emit = defineEmits<{
  "update:modelValue": [value: number]

  "commit": [value: number]
}>()

const isDragging = ref(false)
const handleRef = ref<HTMLElement | null>(null)

const upperBound = computed(() => {
  const container = handleRef.value?.parentElement
  const containerWidth = container ? container.getBoundingClientRect().width : 0
  if (!containerWidth) return props.max
  return Math.max(props.min, Math.min(props.max, containerWidth - props.minRightWidth))
})

function clamp(width: number): number {
  return Math.round(Math.min(upperBound.value, Math.max(props.min, width)))
}

function apply(width: number, commit = false) {
  const next = clamp(width)
  emit("update:modelValue", next)
  if (commit) emit("commit", next)
}

function onMouseDown(event: MouseEvent) {
  if (event.button !== 0) return
  event.preventDefault()
  isDragging.value = true
  document.body.style.cursor = "col-resize"
  document.body.style.userSelect = "none"
}

function onMouseMove(event: MouseEvent) {
  if (!isDragging.value) return
  const container = handleRef.value?.parentElement
  if (!container) return
  apply(event.clientX - container.getBoundingClientRect().left)
}

function onMouseUp() {
  if (!isDragging.value) return
  isDragging.value = false
  document.body.style.cursor = ""
  document.body.style.userSelect = ""
  apply(props.modelValue, true)
}

function onKeydown(event: KeyboardEvent) {
  const step = event.shiftKey ? 48 : 16
  if (event.key === "ArrowLeft") apply(props.modelValue - step, true)
  else if (event.key === "ArrowRight") apply(props.modelValue + step, true)
  else if (event.key === "Home") apply(props.min, true)
  else if (event.key === "End") apply(props.max, true)
  else return
  event.preventDefault()
}

function onDoubleClick() {
  apply(props.defaultWidth, true)
}

onMounted(() => {
  window.addEventListener("mousemove", onMouseMove)
  window.addEventListener("mouseup", onMouseUp)

  if (props.modelValue > 0) emit("update:modelValue", clamp(props.modelValue))
})

onBeforeUnmount(() => {
  window.removeEventListener("mousemove", onMouseMove)
  window.removeEventListener("mouseup", onMouseUp)
  document.body.style.cursor = ""
  document.body.style.userSelect = ""
})
</script>

<template>
  <div
    ref="handleRef"
    class="split-handle"
    :class="{ 'split-handle--dragging': isDragging }"
    role="separator"
    aria-orientation="vertical"
    :aria-label="label"
    :aria-valuenow="Math.round(modelValue)"
    :aria-valuemin="min"
    :aria-valuemax="Math.round(upperBound)"
    tabindex="0"
    @mousedown="onMouseDown"
    @keydown="onKeydown"
    @dblclick="onDoubleClick"
  />
</template>

<style scoped>
.split-handle {
  position: relative;
  width: 8px;
  flex-shrink: 0;
  cursor: col-resize;
  touch-action: none;
  background: transparent;
}
.split-handle::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 3px;
  width: 2px;

  background: var(--color-orange-76);
  transition: background var(--app-duration-fast) var(--app-ease);
}
.split-handle:hover::before,
.split-handle--dragging::before {
  background: var(--ink);
}
.split-handle:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: -2px;
}

@media (prefers-reduced-motion: reduce) {
  .split-handle::before {
    transition: none;
  }
}
</style>
