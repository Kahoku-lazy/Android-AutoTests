<script setup lang="ts">
/** 助手线路卡片 — 功能标题 + 头像/名称 + 连通状态；模型明细在配置弹层 */
import { computed } from 'vue'
import type { RouteConfig } from '@/shared/types/ai'
import DoodleNote from '@/shared/components/DoodleNote.vue'
import DoodleBtn from '@/shared/components/DoodleBtn.vue'
import { isImageAvatar } from '../constants'

const props = defineProps<{
  label: string
  agentName?: string
  agentAvatar?: string
  config?: RouteConfig
  canManage?: boolean
  testing?: boolean
  testResults?: Record<string, { connected?: boolean }>
}>()
const emit = defineEmits<{ edit: []; test: [] }>()

const ROLES = ['planner', 'executor', 'verifier'] as const

const results = computed(() => props.testResults || props.config?.health?.results)

const displayName = computed(() => props.config?.name || props.agentName || '未命名助手')
const displayAvatar = computed(() => props.config?.avatar || props.agentAvatar || '🤖')
const avatarIsImage = computed(() => isImageAvatar(displayAvatar.value))

/** 线路级连通：未检测 / 已连通 / 已断开 */
const routeConnState = computed(() => {
  const current = results.value
  if (!current) return 'unknown'
  const tested = ROLES.filter((r) => current[r] != null)
  if (!tested.length) return 'unknown'
  return tested.every((r) => current[r]?.connected) ? 'connected' : 'disconnected'
})

/** 胶带/阴影强调色：连通青绿、断开红、未知暖黄 */
const noteAccent = computed(() => {
  if (routeConnState.value === 'connected') return 'var(--c-case)'
  if (routeConnState.value === 'disconnected') return 'var(--app-marker-red)'
  return 'var(--c-dashboard)'
})
</script>

<template>
  <DoodleNote
    class="route-card"
    variant="note"
    :accent="noteAccent"
    :tape="true"
    :tape-color="noteAccent"
  >
    <template #header>
      <div class="route-func">
        <h4 class="route-func-title">{{ label }}</h4>
      </div>
    </template>

    <div class="route-identity">
      <div
        class="route-avatar"
        :style="avatarIsImage ? { backgroundImage: `url(${displayAvatar})` } : {}"
      >
        <span v-if="!avatarIsImage">{{ displayAvatar }}</span>
      </div>
      <div class="route-identity-text">
        <div class="route-agent-name">{{ displayName }}</div>
        <span
          class="route-conn-badge"
          :class="`is-${routeConnState}`"
        >
          <template v-if="routeConnState === 'connected'">✅ 已连通</template>
          <template v-else-if="routeConnState === 'disconnected'">❌ 已断开</template>
          <template v-else>🔍 未检测</template>
        </span>
      </div>
    </div>

    <template v-if="canManage" #actions>
      <DoodleBtn tone="teal" :disabled="testing" @click="emit('test')">
        {{ testing ? '校验中…' : '校验' }}
      </DoodleBtn>
      <DoodleBtn tone="yellow" @click="emit('edit')">配置</DoodleBtn>
    </template>
  </DoodleNote>
</template>

<style scoped>
.route-func {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: var(--app-space-sm);
  border-bottom: 2px dashed color-mix(in srgb, var(--ink) 22%, transparent);
}
.route-func-title {
  margin: 0;
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ai-ink-soft);
  text-align: center;
  width: 100%;
}

.route-identity {
  display: flex;
  align-items: center;
  gap: 12px;
}
.route-avatar {
  width: 48px;
  height: 48px;
  border-radius: 2px;
  border: 2px solid var(--ink);
  background-color: var(--ai-warm-bg);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--app-size-xl);
  flex-shrink: 0;
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--ink) 12%, transparent);
}
.route-identity-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}
.route-agent-name {
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--ai-ink-soft);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.route-conn-badge {
  display: inline-flex;
  align-self: flex-start;
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 2px;
  border: 1.5px solid var(--ink);
}
.route-conn-badge.is-connected {
  background: var(--app-status-success-bg);
  color: var(--app-status-success-text);
  border-color: var(--app-status-success);
}
.route-conn-badge.is-disconnected {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
}
.route-conn-badge.is-unknown {
  background: var(--ai-bg-neutral);
  color: var(--ai-ink-muted);
  border-color: var(--app-offline);
}
</style>
