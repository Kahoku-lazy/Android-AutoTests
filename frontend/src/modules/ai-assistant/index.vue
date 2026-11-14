<script setup lang="ts">
import { computed } from "vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { useSingleAgentBoard } from "./index.logic"
import { newestWorkflowKey, releasedLabel } from "./helpers/workflow-cards"

const {
  workflows,
  selectedKey,
  serial,
  devices,
  draft,
  view,
  events,
  eventsLoading,
  currentReply,
  loading,
  sending,
  errorText,
  canSend,
  sendHint,
  load,
  loadEvents,
  send,
  toggleView,
} = useSingleAgentBoard()

/** 上线日期最新的编排键：用于在卡片上标「最新」；只有一张时不标，也不改变默认选中。 */
const newestKey = computed(() => {
  if (workflows.value.length < 2) return ""
  return newestWorkflowKey(workflows.value)
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench">
    <WorkbenchHeader title="平台小助手" subtitle="左侧选编排，右侧对话" icon="bot" />
    <div class="doc-body">
      <ErrorState v-if="errorText && !workflows.length" :message="errorText" @retry="load" />
      <div v-else class="board">
        <aside class="board__rail" aria-label="编排">
          <h2 class="board__title">编排</h2>
          <div class="rail-list" v-loading="loading">
            <button
              v-for="card in workflows"
              :key="card.key"
              type="button"
              class="rail-item"
              :class="{ 'is-selected': card.key === selectedKey }"
              @click="selectedKey = card.key"
            >
              <span class="rail-item__name">{{ card.name }}</span>
              <span class="rail-item__summary">{{ card.summary }}</span>
              <span class="rail-item__meta">
                {{ releasedLabel(card) }}
                <em v-if="card.key === newestKey" class="rail-item__badge">最新</em>
              </span>
            </button>
            <EmptyState v-if="!workflows.length && !loading" icon="🤖" text="还没有编排" />
          </div>
        </aside>

        <section class="panel" aria-label="对话">
          <header class="panel__bar">
            <label class="field">
              编排
              <select v-model="selectedKey">
                <option value="" disabled>请选择编排</option>
                <option v-for="card in workflows" :key="card.key" :value="card.key">
                  {{ card.name }}
                </option>
              </select>
            </label>
            <label class="field">
              设备
              <select v-model="serial">
                <option value="">请选择设备</option>
                <option v-for="item in devices" :key="item.serial" :value="item.serial">
                  {{ item.model }}
                </option>
              </select>
            </label>
            <DoodleBtn tone="teal" class="panel__toggle" @click="toggleView">
              {{ view === "events" ? "返回对话" : "模型事件" }}
            </DoodleBtn>
          </header>

          <div v-if="view === 'chat'" class="panel__body">
            <p v-if="sendHint" class="hint">{{ sendHint }}</p>
            <div class="reply">{{ currentReply || "回复会显示在这里" }}</div>
            <textarea v-model="draft" class="compose" rows="3" placeholder="描述要做的界面操作" />
            <DoodleBtn tone="yellow" :disabled="!canSend" @click="send">
              {{ sending ? "发送中" : "发送" }}
            </DoodleBtn>
          </div>

          <div v-else class="panel__body">
            <div class="events-head">
              <span class="hint">来自本地事件日志，共 {{ events.length }} 条</span>
              <DoodleBtn tone="teal" :disabled="eventsLoading" @click="loadEvents">刷新</DoodleBtn>
            </div>
            <ol class="events">
              <li v-for="(line, index) in events" :key="index" class="events__row">{{ line }}</li>
            </ol>
            <EmptyState v-if="!events.length && !eventsLoading" icon="📜" text="还没有事件" />
          </div>

          <p v-if="errorText && workflows.length" class="hint">{{ errorText }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.board {
  display: grid;
  grid-template-columns: 268px minmax(0, 1fr);
  gap: var(--app-space-lg);
  align-items: start;
  min-height: 0;
}
.board__rail {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  min-width: 0;
}
.board__title {
  margin: 0;
  font-size: var(--app-size-lg);
  color: var(--ai-ink-soft);
}
.rail-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}
.rail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--app-space-sm) var(--app-space-md);
  text-align: left;
  cursor: pointer;
  background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
  border-radius: var(--app-radius-md);
  transition: border-color var(--duration-fast) ease;
}
.rail-item:hover {
  border-color: var(--c-ai);
}
.rail-item.is-selected {
  border-color: var(--c-ai);
  box-shadow: inset 3px 0 0 var(--c-ai);
}
.rail-item__name {
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
}
.rail-item__summary {
  font-size: var(--app-size-sm);
  color: var(--ai-ink-muted);
}
.rail-item__meta {
  display: flex;
  align-items: center;
  gap: var(--app-space-xs);
  font-size: var(--app-size-sm);
  color: var(--ai-ink-muted);
}
.rail-item__badge {
  padding: 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  font-style: normal;
  color: var(--paper);
  background: var(--c-ai);
  border-radius: var(--app-radius-sm);
}
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  min-width: 0;
  padding: var(--app-space-md);
  background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 14%, transparent);
  border-radius: var(--app-radius-lg);
  box-shadow: var(--shadow-md);
}
.panel__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--app-space-sm);
}
.panel__toggle {
  margin-left: auto;
}
.field {
  display: flex;
  align-items: center;
  gap: var(--app-space-xs);
  font-size: var(--app-size-sm);
}
.panel__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  min-height: 0;
}
.reply {
  min-height: 160px;
  max-height: 420px;
  overflow-y: auto;
  padding: var(--app-space-md);
  white-space: pre-wrap;
  font-size: var(--app-size-md);
  background: var(--app-bg-card);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
}
.compose {
  width: 100%;
  padding: var(--app-space-sm);
  font-family: var(--app-font);
  font-size: var(--app-size-md);
  background: var(--app-bg-card);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
  resize: vertical;
}
.events-head {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}
.events {
  margin: 0;
  padding: var(--app-space-sm);
  max-height: 420px;
  overflow-y: auto;
  list-style: none;
  font-family: var(--font-mono);
  font-size: var(--app-size-xs);
  background: var(--app-bg-card);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
}
.events__row {
  padding: 2px 0;
  white-space: pre-wrap;
  word-break: break-word;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 8%, transparent);
}
.events__row:last-child {
  border-bottom: 0;
}
.hint {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--ai-ink-muted);
}
@media (max-width: 960px) {
  .board {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
