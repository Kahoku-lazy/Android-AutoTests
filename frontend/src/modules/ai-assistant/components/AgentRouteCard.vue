<script setup lang="ts">
/** 助手线路卡片 — 左头像 + 右三行（名称 / 职责 / 状态）；底栏校验与配置 */
import { computed, onMounted, onUnmounted, ref } from "vue"
import type { RouteConfig, RouteConnStatus } from "@/shared/types/ai"
import DoodleNote from "@/shared/components/DoodleNote.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { isImageAvatar } from "../constants"

/** 控制设备线路职责（看板唯一线路，写死） */
const DUTY_LABEL = "职责：UI自动化"
/** 测量前占位，避免首帧 0×0 */
const AVATAR_FALLBACK_PX = 64

const props = defineProps<{
  agentName?: string
  agentAvatar?: string
  config?: RouteConfig
  canManage?: boolean
  testing?: boolean
  /** 线路三态；优先于 config.health.status */
  routeStatus?: RouteConnStatus | null
}>()
const emit = defineEmits<{ edit: []; test: [] }>()

const displayName = computed(() => props.config?.name || props.agentName || "未命名助手")
const displayAvatar = computed(() => props.config?.avatar || props.agentAvatar || "🤖")
const avatarIsImage = computed(() => isImageAvatar(displayAvatar.value))

/** 头像边长 = 右三行自然总高（含边框；flex+aspect-ratio 会压成 0 宽） */
const textRef = ref<HTMLElement | null>(null)
const avatarPx = ref(AVATAR_FALLBACK_PX)
let textRo: ResizeObserver | null = null

function syncAvatarSize() {
  const el = textRef.value
  if (!el) return
  // offsetHeight = 边框盒，与 border-box 头像外沿对齐
  const h = el.offsetHeight
  if (h > 0) avatarPx.value = h
}

onMounted(() => {
  const el = textRef.value
  if (!el) return
  syncAvatarSize()
  if (typeof ResizeObserver === "undefined") return
  textRo = new ResizeObserver(() => syncAvatarSize())
  textRo.observe(el)
})
onUnmounted(() => {
  textRo?.disconnect()
  textRo = null
})

const avatarBoxStyle = computed(() => {
  const size = `${avatarPx.value}px`
  const style: Record<string, string> = {
    width: size,
    height: size,
    boxSizing: "border-box",
  }
  if (avatarIsImage.value) style.backgroundImage = `url(${displayAvatar.value})`
  return style
})

/** 业务三态；探测中不算第四业务态 */
const routeConnState = computed<"ready" | "unusable" | "offline" | "checking">(() => {
  if (props.testing) return "checking"
  const status = props.routeStatus ?? props.config?.health?.status ?? null
  if (status === "ready" || status === "unusable" || status === "offline") return status
  // 进页 health 尚未返回：过程态
  return "checking"
})

/** 胶带/阴影强调色：ready 青绿、unusable 暖黄、offline 红、探测中暖黄 */
const noteAccent = computed(() => {
  if (routeConnState.value === "ready") return "var(--c-case)"
  if (routeConnState.value === "offline") return "var(--app-marker-red)"
  return "var(--c-dashboard)"
})

const badgeClass = computed(() => {
  if (routeConnState.value === "ready") return "is-ready"
  if (routeConnState.value === "unusable") return "is-unusable"
  if (routeConnState.value === "offline") return "is-offline"
  return "is-checking"
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
    <div class="route-identity">
      <div class="route-avatar" :style="avatarBoxStyle">
        <span v-if="!avatarIsImage">{{ displayAvatar }}</span>
      </div>
      <div ref="textRef" class="route-identity-text">
        <div class="route-agent-name">{{ displayName }}</div>
        <div class="route-duty">{{ DUTY_LABEL }}</div>
        <span class="route-conn-badge" :class="badgeClass">
          <template v-if="routeConnState === 'ready'">已连通，可执行任务</template>
          <template v-else-if="routeConnState === 'unusable'">秘钥已连接，但无法使用</template>
          <template v-else-if="routeConnState === 'offline'">连接失败，小助手断线</template>
          <template v-else>校验中…</template>
        </span>
      </div>
    </div>

    <template v-if="canManage" #actions>
      <DoodleBtn tone="teal" :disabled="testing" @click="emit('test')">
        {{ testing ? "校验中…" : "校验" }}
      </DoodleBtn>
      <DoodleBtn tone="yellow" @click="emit('edit')">配置</DoodleBtn>
    </template>
  </DoodleNote>
</template>

<style scoped>
.route-card {
  width: fit-content;
  max-width: 100%;
}
.route-identity {
  display: flex;
  align-items: flex-start;
  gap: var(--app-space-sm);
}
.route-avatar {
  flex-shrink: 0;
  box-sizing: border-box;
  border-radius: 2px;
  border: 2px solid var(--ink);
  background-color: var(--ai-warm-bg);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--app-size-xl);
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--ink) 12%, transparent);
  overflow: hidden;
}
.route-identity-text {
  min-width: 0;
  flex: 0 1 auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
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
.route-duty {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ai-ink-muted);
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
  white-space: normal;
  max-width: 100%;
}
.route-conn-badge.is-ready {
  background: var(--app-status-success-bg);
  color: var(--app-status-success-text);
  border-color: var(--app-status-success);
}
.route-conn-badge.is-unusable {
  background: var(--ai-bg-neutral);
  color: var(--ai-ink-muted);
  border-color: var(--c-dashboard);
}
.route-conn-badge.is-offline {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
}
.route-conn-badge.is-checking {
  background: var(--ai-bg-neutral);
  color: var(--ai-ink-muted);
  border-color: var(--app-offline);
}
</style>
