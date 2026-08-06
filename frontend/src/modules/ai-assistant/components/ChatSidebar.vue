<script setup lang="ts">
/**
 * ChatSidebar — 对话侧边栏（Agent卡片 + 对话列表 + 重命名/删除）
 * 从 ChatView.vue 拆分，确保父组件 ≤ 500 行。
 */
import { useRouter } from "vue-router"
import { IconArrowLeft, IconPlus, IconSearch, IconMessageCircle } from "@/shared/icons/index"
import { AVATAR_PATH_PREFIX, ROUTE_AI_ASSISTANT } from "../constants"
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
  return avatar?.startsWith(AVATAR_PATH_PREFIX)
    ? { backgroundImage: `url(${avatar})`, backgroundSize: "cover", backgroundPosition: "center" }
    : {}
}

function avatarText(avatar: string | undefined): string {
  return avatar?.startsWith(AVATAR_PATH_PREFIX) ? "" : avatar || ""
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
        @click="emit('select-chat', c.id)"
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

    <button class="wb-tasks-link" @click="router.push(ROUTE_AI_ASSISTANT)">
      📋 在工作台查看任务看板
    </button>
  </section>
</template>
