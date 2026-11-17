<script setup lang="ts">
/**
 * 用例表 chip：优先级 / 系统 / 业务类型 / 步骤共用的读态标签。
 *
 * 视觉口径沿用 bug-manager 的 .bug-badge（1.5px 墨描边 + --app-radius-sm + 14px 700）；
 * 实线——虚线白名单只给助手卡与 .sketch-kit 控件，chip 不在其中。
 */
withDefaults(
  defineProps<{
    /** p0 / p1 / p2 / system / business / steps */
    tone: string
    text: string
    /** 悬停提示（如 IOS 的「暂不支持执行」、时间列的绝对时间） */
    hint?: string
  }>(),
  { hint: "" },
)
</script>

<template>
  <span class="case-chip" :class="`case-chip--${tone}`" :title="hint || undefined">{{ text }}</span>
</template>

<style scoped>
.case-chip {
  display: inline-flex;
  align-items: center;
  padding: 1px var(--app-space-xs);
  border: 1.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  line-height: 1.4;
  white-space: nowrap;
}

.case-chip--p0 {
  background: var(--c-runner);
}

.case-chip--p1 {
  background: var(--c-dashboard);
}

.case-chip--p2 {
  background: color-mix(in srgb, var(--c-case) 32%, var(--color-white));
}

.case-chip--system {
  background: color-mix(in srgb, var(--c-workflow) 30%, var(--color-white));
}

.case-chip--business {
  background: color-mix(in srgb, var(--c-element) 24%, var(--color-white));
}

.case-chip--steps {
  background: var(--app-bg-card);
}

.case-chip--dirty {
  background: var(--c-dashboard);
}
</style>
