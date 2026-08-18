<script setup lang="ts">
/**
 * ChatSidebar — 对话侧边栏（Agent卡片 + 对话列表 + 重命名/删除）
 * 从 ChatView.vue 拆分，确保父组件 ≤ 500 行。
 */
import { useRouter } from "vue-router"
import { IconArrowLeft, IconPlus, IconSearch, IconMessageCircle } from "@/shared/icons/index"
import { isImageAvatar, ROUTE_AI_ASSISTANT } from "../constants"
import type { Conversation } from "@/shared/types/ai"

const router = useRouter()

const props = defineProps<{
  agent: Record<string, any> | null
  conversations: Conversation[]
  activeConv: number | null
  editingConvId: number | null
  editingTitle: string
}>()

const emit = defineEmits<{
  "new-chat": [ev: Event]
  "select-chat": [id: number]
  "start-rename": [conv: Conversation]
  "update:editing-title": [value: string]
  "finish-rename": []
  "cancel-rename": []
  "delete-conversation": [conv: Conversation]
}>()

function avatarStyle(avatar: string | undefined): Record<string, string> {
  return isImageAvatar(avatar)
    ? { backgroundImage: `url(${avatar})`, backgroundSize: "cover", backgroundPosition: "center" }
    : {}
}

function avatarText(avatar: string | undefined): string {
  return isImageAvatar(avatar) ? "" : avatar || ""
}
</script>

<template>
  <section class="doc-section chat-sidebar">
    <button class="back-btn" @click="router.push(ROUTE_AI_ASSISTANT)">
      <IconArrowLeft :size="18" /><span>返回智能体列表</span>
    </button>
    <button class="new-chat-btn" @click="emit('new-chat', $event)">
      <IconPlus :size="18" /><span>开启新对话</span>
    </button>

    <!-- Agent card -->
    <div class="agent-card" v-if="agent">
      <div class="agent-avatar" :style="avatarStyle(agent.avatar)">
        <span v-if="avatarText(agent.avatar)">{{ avatarText(agent.avatar) }}</span>
      </div>
      <div class="agent-info">
        <div class="agent-name">{{ agent.name }}</div>
        <div class="agent-provider">
          {{ agent.model_provider }} / {{ agent.model_name }}
        </div>
      </div>
    </div>

    <!-- Conversation list -->
    <div class="conv-list">
      <div class="conv-list-title">
        <IconMessageCircle :size="15" /><span>对话历史</span
        ><span class="conv-count">{{ conversations.length }}</span>
      </div>
      <div
        v-for="c in conversations"
        :key="c.id"
        :class="['conv-item', { active: activeConv === c.id }]"
        role="button"
        tabindex="0"
        @click="emit('select-chat', c.id)"
        @keydown.enter.prevent="emit('select-chat', c.id)"
        @keydown.space.prevent="emit('select-chat', c.id)"
      >
        <span class="conv-indicator" :class="{ active: activeConv === c.id }" />
        <span v-if="editingConvId === c.id" class="conv-title" @click.stop>
          <input
            class="conv-rename-input"
            :value="editingTitle"
            @input="emit('update:editing-title', ($event.target as HTMLInputElement).value)"
            @keydown.enter="emit('finish-rename')"
            @keydown.escape="emit('cancel-rename')"
            @blur="emit('finish-rename')"
          />
        </span>
        <span
          v-else
          class="conv-title"
          @dblclick.stop="emit('start-rename', c)"
          :title="'双击修改名称'"
        >{{ c.title }}</span>
        <span class="conv-status" :class="c.status" />
        <button
          class="conv-delete-btn"
          @click.stop="emit('delete-conversation', c)"
          title="删除对话"
        >✕</button>
      </div>
      <div v-if="!conversations.length" class="conv-empty">
        <IconSearch :size="36" /><span>暂无对话记录</span
        ><span class="conv-empty-hint">点击上方「开启新对话」</span>
      </div>
    </div>

  </section>
</template>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  min-height: 0;
  gap: 12px;
  height: 100%;
}
.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--app-accent-purple, #b39ef3);
  border-radius: 12px;
  background: #e6f9f6;
  color: #158a80;
  font-size:var(--app-size-md);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.back-btn:hover {
  background: var(--app-accent-purple, #b39ef3);
  color: var(--app-bg-card);
  box-shadow: 0 4px 14px rgba(25, 200, 185, 0.35);
  transform: translateY(-1px);
}
.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #f7a8c4 0%, #e88a5f 100%);
  color: var(--app-bg-card);
  font-size:var(--app-size-md);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(232, 138, 95, 0.3);
}
.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(232, 138, 95, 0.45);
}
.agent-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #faf9f4 0%, #f5f3ed 100%);
  border: 1px solid var(--doodle-bg, #faf5ee);
  flex-shrink: 0;
}
.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(139, 115, 85, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size:var(--app-size-2xl);
  flex-shrink: 0;
  overflow: hidden;
}
.agent-info {
  min-width: 0;
  flex: 1;
}
.agent-name {
  font-size:var(--app-size-md);
  font-weight: 700;
  color: var(--doodle-ink, #2d2d2d);
  line-height: 1.3;
}
.agent-provider {
  font-size:var(--app-size-sm);
  color: #988b7a;
  margin-top: 3px;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}
.conv-list-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size:var(--app-size-sm);
  font-weight: 700;
  color: var(--app-ink-muted, #999);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 6px 6px;
  border-bottom: 1px solid #f0ebe0;
  margin-bottom: 4px;
}
.conv-count {
  font-size:var(--app-size-sm);
  padding: 1px 8px;
  border-radius: 10px;
  background: #f0e8d8;
  color: #8a7b66;
  font-weight: 700;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-size:var(--app-size-md);
  color: #5c4b38;
  transition: all 0.18s ease;
  border: 1px solid transparent;
}
.conv-item:hover {
  background: #f5f3ed;
  border-color: var(--doodle-bg, #faf5ee);
}
.conv-item.active {
  background: #e6f9f6;
  border-color: var(--app-accent-purple, #b39ef3);
  color: #158a80;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(25, 200, 185, 0.12);
}
.conv-indicator {
  width: 4px;
  height: 24px;
  border-radius: 4px;
  background: #d0c8b8;
  flex-shrink: 0;
  transition: all 0.18s ease;
}
.conv-indicator.active {
  background: var(--app-accent-purple, #b39ef3);
  height: 32px;
  box-shadow: 0 0 8px rgba(25, 200, 185, 0.4);
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}
.conv-rename-input {
  width: 100%;
  border: 1.5px solid var(--app-accent-purple, #b39ef3);
  border-radius: 6px;
  padding: 4px 8px;
  font-size:var(--app-size-sm);
  font-family: inherit;
  color: var(--doodle-ink, #2d2d2d);
  background: var(--app-bg-card);
  outline: none;
}
.conv-delete-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 6px;
  background: none;
  color: #c4b89e;
  font-size:var(--app-size-sm);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.conv-item:hover .conv-delete-btn {
  display: flex;
}
.conv-delete-btn:hover {
  background: rgba(232, 95, 95, 0.12);
  color: #e85f5f;
}
.conv-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.conv-status.active {
  background: #6fba2c;
}
.conv-status.paused {
  background: #e8a735;
}
.conv-status.error {
  background: #e85f5f;
}
.conv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 16px;
  color: var(--app-ink-muted, #999);
  font-size:var(--app-size-sm);
  text-align: center;
}
.conv-empty-hint {
  font-size:var(--app-size-sm);
  color: #c4b89e;
}
</style>
