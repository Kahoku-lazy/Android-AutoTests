<script setup lang="ts">
/**
 * anime.js 三点彩色加载指示器
 */
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { loadingDots } from '@/shared/animations'

const root = ref<HTMLElement | null>(null)
let anim: ReturnType<typeof loadingDots> | null = null

onMounted(() => {
  const dots = root.value?.querySelectorAll('.dot')
  if (dots?.length) anim = loadingDots(dots)
})

onBeforeUnmount(() => {
  try { anim?.pause?.() } catch { /* noop */ }
  anim = null
})
</script>

<template>
  <div ref="root" class="wb-loader" role="status" aria-label="加载中">
    <span class="dot" />
    <span class="dot" />
    <span class="dot" />
  </div>
</template>
