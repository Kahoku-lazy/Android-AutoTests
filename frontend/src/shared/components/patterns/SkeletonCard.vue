<script setup>
/**
 * SkeletonCard — 共享骨架屏（三态之「加载态」的唯一实现）
 *
 * variant:
 * - card（默认）：面向 KPI / 数据卡 —— 4 条固定布局占位（图标区 / 数值 / 标签 / 底栏）
 * - list：面向列表 / 区块首屏 —— N 条等高占位条
 */
defineProps({
  lines: { type: Number, default: 4 },
  variant: { type: String, default: "card" },
})
</script>

<template>
  <div class="skeleton-card" :class="'skeleton-card--' + variant" role="status" aria-label="加载中">
    <div
      v-for="i in lines"
      :key="i"
      class="skeleton-card__bar"
      :class="variant === 'card' ? 'skeleton-card__bar--' + i : 'skeleton-card__bar--row'"
    />
  </div>
</template>

<style scoped>
.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--app-space-xs) 0;
}
.skeleton-card__bar {
  /* 骨架屏 shimmer 灰阶（rgba 装饰绘制色登记处） */
  --skeleton-shimmer-faint: var(--comp-skeleton-shimmer-faint);
  --skeleton-shimmer-base: var(--comp-skeleton-shimmer-base);
  background: linear-gradient(
    90deg,
    var(--skeleton-shimmer-faint) 25%,
    var(--skeleton-shimmer-base) 50%,
    var(--skeleton-shimmer-faint) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s linear infinite;
  border-radius: var(--app-radius-sm);
}
/* 4 条标准布局：图标区 / 数值 / 标签 / 底栏 */
.skeleton-card__bar--1 {
  height: 60px;
  border-radius: 3px 5px;
}
.skeleton-card__bar--2 {
  width: 55%;
  height: 24px;
}
.skeleton-card__bar--3 {
  width: 80%;
  height: 12px;
}
.skeleton-card__bar--4 {
  height: 24px;
  margin-top: 2px;
}

/* list 档：N 条等高占位（列表 / 区块首屏），间距取刻度 */
.skeleton-card--list {
  gap: var(--app-space-sm);
}
.skeleton-card__bar--row {
  height: 20px;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-card__bar {
    animation: none;
  }
}
</style>
