<script setup lang="ts">
/**
 * AnimalFace — 动物岛小动物脸（自绘 SVG，LoginView 贴纸板用）
 * 纯装饰组件：给定 variant 渲染对应的动物头像。
 * 颜色全部走 CSS 变量（--af-* 由父级注入），不硬编码色值。
 */
import { computed } from 'vue'

export type AnimalVariant = 'robot' | 'owl' | 'fox' | 'rabbit' | 'squirrel'

const props = withDefaults(
  defineProps<{
    variant?: AnimalVariant
    size?: number
    /** 主题色（body / 主色） */
    color?: string
  }>(),
  {
    variant: 'robot',
    size: 48,
    color: 'var(--c-ai)',
  },
)
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    class="animal-face"
    :style="{ '--af-color': color }"
    :data-variant="variant"
    aria-hidden="true"
  >
    <!-- ═══ 机器人（AI 助手）═══ -->
    <g v-if="variant === 'robot'">
      <line x1="32" y1="9" x2="32" y2="17" stroke="var(--af-ink)" stroke-width="3" stroke-linecap="round" />
      <circle cx="32" cy="7" r="3.5" fill="var(--af-color)" />
      <rect x="13" y="15" width="38" height="38" rx="12" fill="var(--af-color)" />
      <rect x="17" y="15" width="34" height="30" rx="9" fill="var(--af-color)" />
      <rect x="20" y="22" width="24" height="18" rx="6" fill="var(--af-face)" stroke="var(--af-ink)" stroke-width="2" />
      <circle cx="27" cy="29" r="2.8" fill="var(--af-ink)" />
      <circle cx="37" cy="29" r="2.8" fill="var(--af-ink)" />
      <path d="M28 35 Q32 38 36 35" stroke="var(--af-ink)" stroke-width="2" stroke-linecap="round" fill="none" />
      <circle cx="22" cy="33" r="2" fill="var(--af-blush)" opacity="0.6" />
      <circle cx="42" cy="33" r="2" fill="var(--af-blush)" opacity="0.6" />
    </g>

    <!-- ═══ 猫头鹰（设备管理）═══ -->
    <g v-else-if="variant === 'owl'">
      <path d="M20 20 L15 9 L28 16 Z" fill="var(--af-color)" />
      <path d="M44 20 L49 9 L36 16 Z" fill="var(--af-color)" />
      <ellipse cx="32" cy="38" rx="20" ry="22" fill="var(--af-color)" />
      <ellipse cx="32" cy="44" rx="12" ry="14" fill="var(--af-face)" opacity="0.85" />
      <path d="M14 38 Q10 46 16 52" stroke="var(--af-color)" stroke-width="6" stroke-linecap="round" fill="none" />
      <path d="M50 38 Q54 46 48 52" stroke="var(--af-color)" stroke-width="6" stroke-linecap="round" fill="none" />
      <circle cx="25" cy="31" r="7" stroke="var(--af-ink)" stroke-width="2" />
      <circle cx="39" cy="31" r="7" stroke="var(--af-ink)" stroke-width="2" />
      <circle cx="25" cy="31" r="3" fill="var(--af-ink)" />
      <circle cx="39" cy="31" r="3" fill="var(--af-ink)" />
      <circle cx="26.5" cy="29.5" r="1" fill="var(--af-face)" />
      <circle cx="40.5" cy="29.5" r="1" fill="var(--af-face)" />
      <path d="M32 38 L29 42 L35 42 Z" fill="var(--af-color)" stroke="var(--af-ink)" stroke-width="1.5" stroke-linejoin="round" />
    </g>

    <!-- ═══ 狐狸（用例编排）═══ -->
    <g v-else-if="variant === 'fox'">
      <path d="M22 22 L16 9 L30 17 Z" fill="var(--af-color)" />
      <path d="M42 22 L48 9 L34 17 Z" fill="var(--af-color)" />
      <path d="M24 20 L20 13 L28 17 Z" fill="var(--af-face)" opacity="0.55" />
      <path d="M40 20 L44 13 L36 17 Z" fill="var(--af-face)" opacity="0.55" />
      <path d="M32 13 C44 13 50 22 50 32 C50 42 42 50 32 50 C22 50 14 42 14 32 C14 22 20 13 32 13 Z" fill="var(--af-color)" />
      <path d="M32 32 C26 32 22 30 20 34 C22 38 26 40 32 40 C38 40 42 38 44 34 C42 30 38 32 32 32 Z" fill="var(--af-face)" opacity="0.9" />
      <circle cx="25" cy="27" r="2.6" fill="var(--af-ink)" />
      <circle cx="39" cy="27" r="2.6" fill="var(--af-ink)" />
      <path d="M32 33 L29 35 L32 37 L35 35 Z" fill="var(--af-ink)" />
      <path d="M32 37 L32 40" stroke="var(--af-ink)" stroke-width="1.8" stroke-linecap="round" />
      <circle cx="18" cy="32" r="2.2" fill="var(--af-blush)" opacity="0.5" />
      <circle cx="46" cy="32" r="2.2" fill="var(--af-blush)" opacity="0.5" />
    </g>

    <!-- ═══ 兔子（用例执行）═══ -->
    <g v-else-if="variant === 'rabbit'">
      <path d="M24 20 C20 6 18 4 20 16 C21 24 22 24 24 20 Z" fill="var(--af-color)" />
      <path d="M40 20 C44 6 46 4 44 16 C43 24 42 24 40 20 Z" fill="var(--af-color)" />
      <path d="M24 18 C22 9 21 8 22 16 C23 20 23 20 24 18 Z" fill="var(--af-face)" opacity="0.6" />
      <path d="M40 18 C42 9 43 8 42 16 C41 20 41 20 40 18 Z" fill="var(--af-face)" opacity="0.6" />
      <circle cx="32" cy="33" r="19" fill="var(--af-color)" />
      <path d="M32 33 C25 33 21 31 19 36 C21 41 26 44 32 44 C38 44 43 41 45 36 C43 31 39 33 32 33 Z" fill="var(--af-face)" opacity="0.9" />
      <circle cx="25" cy="28" r="2.4" fill="var(--af-ink)" />
      <circle cx="39" cy="28" r="2.4" fill="var(--af-ink)" />
      <circle cx="26" cy="27" r="0.8" fill="var(--af-face)" />
      <circle cx="40" cy="27" r="0.8" fill="var(--af-face)" />
      <path d="M32 33 L30 35 L32 36 L34 35 Z" fill="var(--af-ink)" />
      <path d="M32 36 L32 38 M32 38 Q30 40 28 39 M32 38 Q34 40 36 39" stroke="var(--af-ink)" stroke-width="1.5" stroke-linecap="round" />
      <circle cx="21" cy="33" r="2.4" fill="var(--af-blush)" opacity="0.55" />
      <circle cx="43" cy="33" r="2.4" fill="var(--af-blush)" opacity="0.55" />
    </g>

    <!-- ═══ 松鼠（报告生成）═══ -->
    <g v-else-if="variant === 'squirrel'">
      <path d="M23 22 L21 12 L29 18 Z" fill="var(--af-color)" />
      <path d="M41 22 L43 12 L35 18 Z" fill="var(--af-color)" />
      <circle cx="32" cy="34" r="18" fill="var(--af-color)" />
      <path d="M32 34 C25 34 21 32 19 37 C21 42 26 44 32 44 C38 44 43 42 45 37 C43 32 39 34 32 34 Z" fill="var(--af-face)" opacity="0.9" />
      <circle cx="25" cy="30" r="2.6" fill="var(--af-ink)" />
      <circle cx="39" cy="30" r="2.6" fill="var(--af-ink)" />
      <circle cx="26" cy="29" r="0.9" fill="var(--af-face)" />
      <circle cx="40" cy="29" r="0.9" fill="var(--af-face)" />
      <circle cx="32" cy="35" r="1.8" fill="var(--af-ink)" />
      <path d="M32 36 Q32 39 30 39 M32 36 Q32 39 34 39" stroke="var(--af-ink)" stroke-width="1.5" stroke-linecap="round" />
      <circle cx="20" cy="33" r="2.2" fill="var(--af-blush)" opacity="0.5" />
      <circle cx="44" cy="33" r="2.2" fill="var(--af-blush)" opacity="0.5" />
    </g>
  </svg>
</template>

<style scoped>
.animal-face {
  /* 让父级可覆盖的面部/腮红色；与动物岛 paper/danger 一致 */
  --af-face: var(--app-bg-card);
  --af-ink: var(--app-stat-text);
  --af-blush: var(--app-status-danger);
  display: block;
  overflow: visible;
}
</style>
