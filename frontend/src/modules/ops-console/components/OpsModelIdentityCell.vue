<script setup lang="ts">
/** 模型表首列身份单元：首字母头像 + 模型名主行 + 「厂商 · 类型（· 音色）」副行。 */
import { computed } from "vue"
import { modelKindLabel, OPS_MODEL_KIND_OPTIONS } from "../constants"
import type { OpsModelConfig } from "../types"

const props = defineProps<{ config: OpsModelConfig }>()

/** 头像文字取模型名首字母（`qwen-max` → Q）。 */
const initial = computed(() => (props.config.model_name || "?").slice(0, 1).toUpperCase())

/** 副行：厂商 + 类型 + 音色，三段都为空时给占位符。 */
const subtitle = computed(() => {
  const parts = [props.config.provider, modelKindLabel(props.config.model_kind)].filter(
    (part): part is string => Boolean(part),
  )
  if (props.config.voice) parts.push(props.config.voice)
  return parts.length ? parts.join(" · ") : "—"
})

/** 头像底色随类型走，扫读时不同类型一眼可分。 */
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

/* 聊天 / 语音合成 / 实时语音三种类型各一支模块色 */
.ops-avatar--chat {
  background: color-mix(in srgb, var(--c-device) 28%, var(--app-bg-card));
}

.ops-avatar--tts {
  background: color-mix(in srgb, var(--c-runner) 45%, var(--app-bg-card));
}

.ops-avatar--realtime {
  background: color-mix(in srgb, var(--c-ai) 28%, var(--app-bg-card));
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
