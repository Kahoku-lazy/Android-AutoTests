<script setup lang="ts">
import { formatBugTime } from "../constants"
import type { BugTicket } from "../types"

defineProps<{
  bug: BugTicket
}>()
</script>

<template>
  <div class="bug-id">
    <span class="bug-id__badge" aria-hidden="true">🐞</span>
    <div class="bug-id__text">
      <code class="bug-id__no" :title="bug.bug_no">{{ bug.bug_no }}</code>
      <span class="bug-id__time">{{ formatBugTime(bug.created_at) }}</span>
    </div>
  </div>
</template>

<style scoped>
.bug-id {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  text-align: left;
}

.bug-id__badge {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border: 2px solid var(--ink);
  border-radius: 50%;
  font-size: var(--app-size-sm);
  background: color-mix(in srgb, var(--c-runner) 30%, var(--app-bg-card));
}

.bug-id__text {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.bug-id__no {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bug-id__time {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-secondary);
  white-space: nowrap;
}
</style>
