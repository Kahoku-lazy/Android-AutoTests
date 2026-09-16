<script setup lang="ts">
/**
 * AppCard — L3 可复用数据块（钉板壳）
 *
 * 对齐 hand-drawn #page-typography .panel：虚线近直角、马克笔硬阴影、可选图钉、微倾。
 * accent / tilt 由父级注入（同排 cycle 用 sketchToneAt / sketchTiltAt）。
 * ECharts 画布内配色独立，不由本组件约束。
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 兼容旧调用：模块色名或 app-*；优先用 tone */
    color?: string
    type?: 'default' | 'dashed'
    /** CSS 色或 var(--c-*)，驱动图钉与硬阴影 */
    tone?: string
    /** 微倾角度（deg） */
    tilt?: number
    /** 是否显示居中图钉 */
    pin?: boolean
  }>(),
  {
    color: '',
    type: 'default',
    tone: '',
    tilt: 0.3,
    pin: true,
  },
)

/** 旧 color 名 → 模块令牌（无 tone 时回退） */
const COLOR_TONE: Record<string, string> = {
  blue: 'var(--c-workflow)',
  green: 'var(--c-device)',
  teal: 'var(--c-case)',
  purple: 'var(--c-element)',
  pink: 'var(--c-runner)',
  yellow: 'var(--c-dashboard)',
  brown: 'var(--c-report)',
  red: 'var(--c-runner)',
  orange: 'var(--c-ai)',
  dashboard: 'var(--c-dashboard)',
  device: 'var(--c-device)',
  element: 'var(--c-element)',
  case: 'var(--c-case)',
  runner: 'var(--c-runner)',
  report: 'var(--c-report)',
  ai: 'var(--c-ai)',
  workflow: 'var(--c-workflow)',
}

const resolvedTone = computed(() => {
  if (props.tone) return props.tone
  const key = props.color.replace(/^app-/, '')
  return COLOR_TONE[key] || 'var(--c-dashboard)'
})

const rootStyle = computed(() => ({
  '--ac-accent': resolvedTone.value,
  '--ac-tilt': `${props.tilt}deg`,
}))

const rootClass = computed(() => [
  'ac-card',
  props.type === 'dashed' ? 'ac-card--dashed' : '',
  props.pin ? 'ac-card--pin' : '',
])
</script>

<template>
  <el-card :class="rootClass" :style="rootStyle" shadow="never">
    <span v-if="pin" class="ac-card__pin" aria-hidden="true" />
    <template v-for="(_, slot) in $slots" :key="slot" #[slot]>
      <slot :name="slot" />
    </template>
  </el-card>
</template>
