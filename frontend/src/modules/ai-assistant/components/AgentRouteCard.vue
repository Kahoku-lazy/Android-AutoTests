<script setup lang="ts">
/** 助手线路卡片 — 左头像 + 右两行（名称 / 职责）；底栏仅配置 */
import { computed, onMounted, onUnmounted, ref } from "vue"
import type { RouteConfig } from "@/shared/types/ai"
import DoodleNote from "@/shared/components/DoodleNote.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { isImageAvatar } from "../constants"

/** 控制设备线路职责（看板唯一线路，写死） */
const DUTY_LABEL = "职责：UI自动化"
/** 测量前占位，避免首帧 0×0 */
const AVATAR_FALLBACK_PX = 64
/** 固定胶带/阴影强调色（校验下线后不再随连通状态变化） */
const NOTE_ACCENT = "var(--c-case)"

const props = defineProps<{
  agentName?: string
  agentAvatar?: string
  config?: RouteConfig
  canManage?: boolean
}>()
const emit = defineEmits<{ edit: [] }>()

const displayName = computed(() => props.config?.name || props.agentName || "未命名助手")
const displayAvatar = computed(() => props.config?.avatar || props.agentAvatar || "🤖")
const avatarIsImage = computed(() => isImageAvatar(displayAvatar.value))

/** 头像边长 = 右两行自然总高（含边框；flex+aspect-ratio 会压成 0 宽） */
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
</script>

<template>
  <DoodleNote
    class="route-card"
    variant="note"
    :accent="NOTE_ACCENT"
    :tape="true"
    :tape-color="NOTE_ACCENT"
  >
    <div class="route-identity">
      <div class="route-avatar" :style="avatarBoxStyle">
        <span v-if="!avatarIsImage">{{ displayAvatar }}</span>
      </div>
      <div ref="textRef" class="route-identity-text">
        <div class="route-agent-name">{{ displayName }}</div>
        <div class="route-duty">{{ DUTY_LABEL }}</div>
      </div>
    </div>

    <template v-if="canManage" #actions>
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
</style>
