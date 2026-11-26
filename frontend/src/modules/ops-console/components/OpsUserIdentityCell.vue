<script setup lang="ts">
import { computed } from "vue"
import type { OpsUser } from "../types"

const props = defineProps<{ user: OpsUser }>()

const initial = computed(() => (props.user.username || "?").slice(0, 1).toUpperCase())
</script>

<template>
  <div class="ops-identity-cell">
    <span class="ops-avatar" :class="`ops-avatar--${user.identity}`">{{ initial }}</span>
    <span class="ops-identity-cell__text">
      <code class="ops-identity-cell__name">{{ user.username }}</code>
      <span class="ops-identity-cell__sub">{{ user.email || "—" }}</span>
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

.ops-avatar--superuser {
  background: color-mix(in srgb, var(--c-element) 32%, var(--app-bg-card));
}

.ops-avatar--operator {
  background: color-mix(in srgb, var(--c-ops) 30%, var(--app-bg-card));
}

.ops-avatar--user {
  background: color-mix(in srgb, var(--paper) 55%, var(--app-bg-card));
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
