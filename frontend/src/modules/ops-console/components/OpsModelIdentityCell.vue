<script setup lang="ts">
import { computed } from "vue"
import { modelKindLabel, OPS_MODEL_KIND_OPTIONS } from "../constants"
import type { OpsModelConfig } from "../types"

const props = defineProps<{ config: OpsModelConfig }>()

const initial = computed(() => (props.config.model_name || "?").slice(0, 1).toUpperCase())

const subtitle = computed(() => {
  const parts = [props.config.provider, modelKindLabel(props.config.model_kind)].filter(
    (part): part is string => Boolean(part),
  )
  if (props.config.model_kind === "embedding" && props.config.dimensions) {
    parts.push(`${props.config.dimensions} 维`)
  } else if (props.config.voice) {
    parts.push(props.config.voice)
  }
  return parts.length ? parts.join(" · ") : "—"
})

const tone = computed(() => {
  const kind = props.config.model_kind || OPS_MODEL_KIND_OPTIONS[0].value
  return `ops-avatar--${kind}`
})
</script>

<template>
  <div class="ops-identity-cell">
    <span class="ops-avatar" :class="tone">{{ initial }}</span>
    <span class="ops-identity-cell__text">
      <code class="ops-identity-cell__name">{{ config.model_name }}</code>
      <span class="ops-identity-cell__sub">{{ subtitle }}</span>
    </span>
  </div>
</template>

<style scoped>
.ops-identity-cell {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  min-width: 0;
}

.ops-avatar {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border: 2px solid var(--ink);
  border-radius: 50%;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.ops-avatar--chat {
  background: color-mix(in srgb, var(--c-device) 28%, var(--app-bg-card));
}

.ops-avatar--tts {
  background: color-mix(in srgb, var(--c-runner) 45%, var(--app-bg-card));
}

.ops-avatar--realtime {
  background: color-mix(in srgb, var(--c-ai) 28%, var(--app-bg-card));
}

.ops-avatar--embedding {
  background: color-mix(in srgb, var(--c-element) 28%, var(--app-bg-card));
}

.ops-identity-cell__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.ops-identity-cell__name {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
  line-height: var(--app-line-height-tight);
}

.ops-identity-cell__sub {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
