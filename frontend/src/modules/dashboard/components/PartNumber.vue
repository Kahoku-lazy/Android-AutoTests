<script setup lang="ts">
/**
 * 零件卡编号徽标：SVG 数字图标（圆角方框 + 数字），颜色取卡片 accent。
 * 替代纯文本的 00 / 01 / 02，放在卡片标题前。
 */
defineProps<{ value: string }>()
</script>

<template>
  <svg class="part-no" viewBox="0 0 22 22" role="img" :aria-label="`编号 ${value}`">
    <rect
      x="1"
      y="1"
      width="20"
      height="20"
      rx="3.5"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
    />
    <text x="11" y="15.2" text-anchor="middle" font-size="10" font-weight="800" fill="currentColor">
      {{ value }}
    </text>
  </svg>
</template>

<style scoped>
.part-no {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  color: var(--part-accent, var(--c-ai));
  font-family: var(--app-font);
}
</style>
