<script setup lang="ts">
/** HitCard — 一条检索命中：实线条目卡，逐字展示原文，不改写不总结。 */
import type { KnowledgeHit } from "../types"
import { formatScore } from "../helpers/hits"

defineProps<{ hit: KnowledgeHit }>()
</script>

<template>
  <article class="ks-hit">
    <header class="ks-hit__head">
      <span class="ks-hit__base">{{ hit.base }}</span>
      <span class="ks-hit__source" :title="hit.source">{{ hit.source }}</span>
      <span class="ks-hit__chunk">片段 {{ hit.chunk_index + 1 }}</span>
      <span class="ks-hit__score">相似度 {{ formatScore(hit.score) }}</span>
    </header>
    <p class="ks-hit__text">{{ hit.text }}</p>
  </article>
</template>

<style scoped>
.ks-hit {
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  padding: var(--app-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-hit__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--app-space-sm);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ks-hit__base {
  border: 1px solid var(--c-case);
  border-radius: var(--app-radius-sm);
  color: var(--app-text-primary);
  font-weight: var(--app-font-weight-bold);
  padding: 0 var(--app-space-xs);
}

.ks-hit__source {
  font-family: var(--app-font-mono, monospace);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-hit__score {
  margin-left: auto;
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-primary);
}

.ks-hit__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--app-size-sm);
  line-height: var(--app-line-height-normal);
  color: var(--app-text-primary);
}
</style>
