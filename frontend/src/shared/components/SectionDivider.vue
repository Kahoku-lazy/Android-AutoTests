<script setup lang="ts">
/**
 * 页面分区虚线分隔线：只做视觉分区，不承载信息、不可点击。
 *
 * 虚线白名单落点之一（见 `.agents/skills/doodle-craft/SKILL.md` §线型规则）：
 * 页面需要在两段并列内容之间画一条虚线时用它，**不要**在页面里就地写 `dashed`。
 * 间距由使用方给根节点加 margin，组件本身不预设外边距。
 */
</script>

<template>
  <div class="section-divider" aria-hidden="true" />
</template>

<style scoped>
.section-divider {
  width: 100%;
  border-top: 1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent);
}
</style>
