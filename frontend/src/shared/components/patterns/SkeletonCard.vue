<script setup>
/**
 * SkeletonCard — 卡片骨架屏
 *
 * 替代各模块手写的 shimmer 动画。垂直排列 N 条占位条。
 */
defineProps({
  lines: { type: Number, default: 4 },
})
</script>

<template>
  <div class="skeleton-card" role="status" aria-label="加载中">
    <div
      v-for="i in lines"
      :key="i"
      class="skeleton-card__bar"
      :class="`skeleton-card__bar--${i}`"
    />
  </div>
</template>

<style scoped>
.skeleton-card {
  display: flex; flex-direction: column; gap: 10px;
  padding: var(--app-space-xs) 0;
}
.skeleton-card__bar {
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.03) 25%,
    rgba(0, 0, 0, 0.06) 50%,
    rgba(0, 0, 0, 0.03) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s linear infinite;
  border-radius: 4px;
}
/* 4 条标准布局：图标区 / 数值 / 标签 / 底栏 */
.skeleton-card__bar--1 { height: 60px; border-radius: 3px 5px 3px 5px; }
.skeleton-card__bar--2 { width: 55%; height: 24px; }
.skeleton-card__bar--3 { width: 80%; height: 12px; }
.skeleton-card__bar--4 { height: 24px; margin-top: 2px; }

@keyframes skeleton-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-card__bar { animation: none; }
}
</style>
