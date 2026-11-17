<script setup lang="ts">
/**
 * 区块标题条：标题 + 计数 + 右侧动作。
 *
 * 助手区与工作流区共用这一份，保证两个区块的标题、计数与按钮在同一基线上：
 * 标题 20px 粗墨、计数 14px 次要色、中间弹性空白把动作推到最右。
 */
defineProps<{
  /** 区块标题，如「AI 助手」「工作流」。 */
  title: string
  /** 右侧计数的完整文案，如「共 3 位助手」「共 1 条」。 */
  count: string
}>()
</script>

<template>
  <div class="section-bar">
    <h2 class="section-bar__title">{{ title }}</h2>
    <span class="section-bar__count">{{ count }}</span>
    <span class="section-bar__spacer" />
    <slot name="action" />
  </div>
</template>

<style scoped>
.section-bar {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}

.section-bar__title {
  margin: 0;
  color: var(--ink);
  font-size: var(--app-size-lg);
  font-weight: var(--app-font-weight-heavy);
}

.section-bar__count {
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
}

.section-bar__spacer {
  flex: 1;
}
</style>
