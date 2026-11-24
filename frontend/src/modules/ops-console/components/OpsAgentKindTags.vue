<script setup lang="ts">
import { computed } from "vue"
import { OPS_AGENT_KIND_LABELS, OPS_AGENT_KIND_UNSET } from "../constants"
import type { OpsAgentKind } from "../types"

const props = defineProps<{ kinds: OpsAgentKind[] }>()

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
