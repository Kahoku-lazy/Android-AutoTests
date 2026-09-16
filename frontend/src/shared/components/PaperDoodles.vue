<script setup lang="ts">
/**
 * PaperDoodles — 主内容区稀疏手绘涂鸦层（纸面水印）
 * 图形来自 temps/hand-drawn-doodle-sidebar.html 的 .bg-doodles；不拦截指针事件。
 */
</script>

<template>
  <div class="paper-doodles" aria-hidden="true">
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" class="paper-doodles__item" style="top:48px;left:40px;opacity:.3">
      <path
        d="M16 16 Q16 10 22 10 Q28 10 28 16 Q28 24 20 24 Q10 24 10 14 Q10 6 20 6 Q30 6 30 16"
        stroke="var(--color-indigo-13)"
        stroke-width="2"
        stroke-linecap="round"
      />
    </svg>
    <svg width="56" height="56" viewBox="0 0 60 60" fill="none" class="paper-doodles__item" style="top:120px;left:8%;opacity:.1">
      <circle cx="30" cy="30" r="28" stroke="var(--paper-mark-brown)" stroke-width="6" fill="none" />
      <circle cx="30" cy="30" r="22" stroke="var(--paper-mark-brown)" stroke-width="1.5" fill="none" />
    </svg>
    <svg width="48" height="48" viewBox="0 0 40 40" fill="none" class="paper-doodles__item" style="top:38%;left:24px;opacity:.45">
      <path d="M20 4 Q36 4 36 20 Q36 36 20 36 Q4 36 4 20 Q4 8 20 4" stroke="var(--paper-mark-yellow)" stroke-width="2.5" stroke-linecap="round" />
    </svg>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" class="paper-doodles__item" style="top:36px;right:12%;transform:rotate(15deg);opacity:.7">
      <path
        d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
        fill="var(--paper-mark-yellow)"
        stroke="var(--paper-mark-yellow)"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" class="paper-doodles__item" style="top:72px;right:18%;opacity:.6">
      <path
        d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
        fill="var(--paper-mark-yellow)"
        stroke="var(--paper-mark-yellow)"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" class="paper-doodles__item" style="top:58px;right:24%;transform:rotate(30deg);opacity:.65">
      <path
        d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
        fill="var(--paper-mark-red)"
        stroke="var(--paper-mark-red)"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
    <svg width="48" height="32" viewBox="0 0 48 32" fill="none" class="paper-doodles__item" style="top:28%;right:40px;opacity:.4">
      <path d="M4 16 Q12 10 22 16 Q30 22 40 16" stroke="var(--paper-mark-red)" stroke-width="2.5" stroke-linecap="round" />
      <path d="M34 10 L42 16 L34 22" stroke="var(--paper-mark-red)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <svg width="100" height="100" viewBox="0 0 60 60" fill="none" class="paper-doodles__item" style="top:52%;right:6%;opacity:.09">
      <circle cx="30" cy="30" r="28" stroke="var(--paper-mark-brown)" stroke-width="6" fill="none" />
      <circle cx="30" cy="30" r="22" stroke="var(--paper-mark-brown)" stroke-width="1.5" fill="none" />
    </svg>
    <svg width="80" height="16" viewBox="0 0 80 16" fill="none" class="paper-doodles__item" style="top:68%;right:14%;opacity:.5">
      <path
        d="M2 8 Q10 2 18 8 Q26 14 34 8 Q42 2 50 8 Q58 14 66 8 Q74 2 78 8"
        stroke="var(--paper-mark-teal)"
        stroke-width="2.5"
        stroke-linecap="round"
      />
    </svg>
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none" class="paper-doodles__item" style="top:78%;left:8%;opacity:.42">
      <path d="M20 4 Q36 4 36 20 Q36 36 20 36 Q4 36 4 20 Q4 8 20 4" stroke="var(--paper-mark-yellow)" stroke-width="2.5" stroke-linecap="round" />
    </svg>
    <svg width="80" height="16" viewBox="0 0 80 16" fill="none" class="paper-doodles__item" style="top:86%;left:22%;opacity:.38">
      <path
        d="M2 8 Q10 2 18 8 Q26 14 34 8 Q42 2 50 8 Q58 14 66 8 Q74 2 78 8"
        stroke="var(--paper-mark-red)"
        stroke-width="2.5"
        stroke-linecap="round"
      />
    </svg>
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" class="paper-doodles__item" style="top:44%;right:30%;transform:rotate(20deg);opacity:.5">
      <path
        d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
        fill="var(--paper-mark-yellow)"
        stroke="var(--paper-mark-yellow)"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" class="paper-doodles__item" style="top:48%;right:28%;opacity:.45">
      <path
        d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
        fill="var(--paper-mark-red)"
        stroke="var(--paper-mark-red)"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
    <svg width="70" height="70" viewBox="0 0 60 60" fill="none" class="paper-doodles__item" style="top:18%;right:36%;opacity:.07">
      <circle cx="30" cy="30" r="28" stroke="var(--paper-mark-brown)" stroke-width="6" fill="none" />
      <circle cx="30" cy="30" r="22" stroke="var(--paper-mark-brown)" stroke-width="1.5" fill="none" />
    </svg>
  </div>
</template>

<style scoped>
.paper-doodles {
  /* 涂鸦笔触色（SVG 图形绘制色，登记例外：色相固定、保留字面量） */
  --paper-mark-brown: var(--comp-paper-mark-brown);   /* 圆圈 / 圆环 */
  --paper-mark-yellow: var(--comp-paper-mark-yellow);  /* 星形 / 螺旋 */
  --paper-mark-red: var(--comp-paper-mark-red);     /* 箭头 / 波浪 */
  --paper-mark-teal: var(--comp-paper-mark-teal);    /* 波浪 */

  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.paper-doodles__item {
  position: absolute;
}
</style>
