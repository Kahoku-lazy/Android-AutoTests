<script setup lang="ts">
/**
 * Agent 配置类型标签：chip 呈现 0..N 个类型，未分类显示占位文案。
 *
 * 业务：
 * - 列表与抽屉共用同一处皮肤，避免两处各写一套 chip
 * - 只认三种后端取值，未知值按未分类兜底
 */
import { computed } from "vue"
import { OPS_AGENT_KIND_LABELS, OPS_AGENT_KIND_UNSET } from "../constants"
import type { OpsAgentKind } from "../types"

const props = defineProps<{ kinds: OpsAgentKind[] }>()

/** 过滤掉后端未来可能新增、本端还不认识的取值，避免渲染成空白 */
const tags = computed(() =>
  (props.kinds || [])
    .filter((kind): kind is OpsAgentKind => kind in OPS_AGENT_KIND_LABELS)
    .map((kind) => ({ kind, label: OPS_AGENT_KIND_LABELS[kind] })),
)
</script>

<template>
  <span class="ops-kind">
    <span
      v-for="tag in tags"
      :key="tag.kind"
      class="ops-kind__tag"
      :class="`ops-kind__tag--${tag.kind}`"
    >
      {{ tag.label }}
    </span>
    <span v-if="!tags.length" class="ops-kind__unset">{{ OPS_AGENT_KIND_UNSET }}</span>
  </span>
</template>

<style scoped>
.ops-kind {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-xs);
  flex-wrap: nowrap;
}

/* 类型 chip：模块色只做描边与浅底（doodle-craft 的模块色用法），形状取令牌圆角 */
.ops-kind__tag {
  display: inline-flex;
  align-items: center;
  padding: 1px var(--app-space-sm);
  border: 1px solid color-mix(in srgb, var(--kind-color) 55%, var(--ink));
  border-radius: var(--app-radius-sm);
  background: color-mix(in srgb, var(--kind-color) 18%, var(--app-bg-card));
  color: var(--app-text-primary);
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-tight);
  white-space: nowrap;
}

.ops-kind__tag--executor {
  --kind-color: var(--c-device);
}

.ops-kind__tag--verifier {
  --kind-color: var(--c-workflow);
}

.ops-kind__tag--planner {
  --kind-color: var(--c-element);
}

.ops-kind__unset {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}
</style>
