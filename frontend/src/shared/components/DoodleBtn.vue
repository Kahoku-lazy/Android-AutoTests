<script setup lang="ts">
/**
 * DoodleBtn — 涂鸦操作按钮
 *
 * tone:
 * - danger：删除（马克笔红）
 * - teal：校验 / 详情（青绿，非冷蓝）
 * - yellow：配置（柠黄）
 * - paper：中性纸色（可选）
 *
 * 视觉 DNA：墨色描边 / 近直角 / 硬偏移阴影；对齐 hand-drawn-doodle `#comp-buttons`
 */
const props = withDefaults(
  defineProps<{
    tone?: "danger" | "teal" | "yellow" | "paper"
    disabled?: boolean
    type?: "button" | "submit" | "reset"
  }>(),
  {
    tone: "paper",
    disabled: false,
    type: "button",
  },
)

const emit = defineEmits<{
  click: [e: MouseEvent]
}>()

function onClick(e: MouseEvent) {
  if (props.disabled || e.defaultPrevented) return
  emit("click", e)
}
</script>

<template>
  <button
    class="doodle-btn"
    :class="[`doodle-btn--${tone}`, { 'is-disabled': disabled }]"
    :type="type"
    :disabled="disabled"
    @click="onClick"
  >
    <slot />
  </button>
</template>

<style scoped>
.doodle-btn {
  /* 禁用态灰阶（本组件专用色值登记处；tokens.css 无同值令牌） */
  --dbtn-disabled-bg: var(--comp-dbtn-disabled-bg);
  --dbtn-disabled-ink: var(--comp-dbtn-disabled-ink);

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 14px;
  border: 2.5px solid var(--ink);
  border-radius: 2px;
  background: var(--paper);
  color: var(--ink);
  font-family: inherit;
  font-size: var(--app-size-sm, 13px);
  font-weight: 800;
  line-height: 1.2;
  box-shadow: 3px 3px 0 0 var(--ink);
  cursor: pointer;
  transition:
    transform var(--app-duration, 0.12s) var(--app-ease, ease),
    box-shadow var(--app-duration, 0.12s) var(--app-ease, ease);
}

.doodle-btn--danger {
  background: var(--app-marker-red);
  color: #fff;
}

.doodle-btn--teal {
  background: var(--c-case);
  color: var(--ink);
}

.doodle-btn--yellow {
  background: var(--c-dashboard);
  color: var(--ink);
}

.doodle-btn--paper {
  background: var(--paper);
  color: var(--ink);
}

.doodle-btn:hover:not(:disabled):not(.is-disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 4px 4px 0 0 var(--ink);
}

.doodle-btn:active:not(:disabled):not(.is-disabled) {
  transform: translate(2px, 2px);
  box-shadow: 1px 1px 0 0 var(--ink);
}

.doodle-btn:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

.doodle-btn.is-disabled,
.doodle-btn:disabled {
  background: var(--dbtn-disabled-bg);
  color: var(--dbtn-disabled-ink);
  cursor: not-allowed;
  box-shadow: 3px 3px 0 0 #bbb;
}

.doodle-btn.is-disabled:hover,
.doodle-btn:disabled:hover {
  transform: none;
  box-shadow: 3px 3px 0 0 #bbb;
}

@media (prefers-reduced-motion: reduce) {
  .doodle-btn {
    transition: none;
  }
  .doodle-btn:hover:not(:disabled):not(.is-disabled),
  .doodle-btn:active:not(:disabled):not(.is-disabled) {
    transform: none;
  }
}
</style>
