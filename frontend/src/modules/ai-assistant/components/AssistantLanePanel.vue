<script setup lang="ts">
import { nextTick, ref } from "vue"
import type { ComponentPublicInstance } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { threadStatusLabel } from "../helpers/thread-status"
import type { AssistantThread } from "../types"

defineProps<{ lanes: AssistantThread[]; currentId: string }>()
const emit = defineEmits<{
  create: []
  open: [id: string]
  rename: [id: string, title: string]
  remove: [id: string]
}>()

const renamingId = ref("")
const draft = ref("")
const renameInput = ref<HTMLInputElement | null>(null)

async function startRename(lane: AssistantThread): Promise<void> {
  renamingId.value = lane.thread_id
  draft.value = lane.title || ""
  await nextTick()
  renameInput.value?.focus()
  renameInput.value?.select()
}

function commitRename(): void {
  if (!renamingId.value) return
  const id = renamingId.value
  renamingId.value = ""
  emit("rename", id, draft.value.trim())
}

function cancelRename(): void {
  renamingId.value = ""
}

function bindRenameInput(el: Element | ComponentPublicInstance | null): void {
  renameInput.value = el instanceof HTMLInputElement ? el : null
}
</script>

<template>
  <div class="lane-column">
    <aside class="lane-panel" aria-label="对话栏">
      <header class="lane-panel__head">
        <h2 class="lane-panel__title">对话栏</h2>
        <span class="lane-panel__count">{{ lanes.length }} 个</span>
      </header>

      <!-- 彩色双波浪线：上波该助手笔色、下波模块色，只做身份装饰（参考 Wavy Underline） -->
      <svg
        class="lane-panel__waves"
        viewBox="0 0 96 18"
        width="96"
        height="18"
        aria-hidden="true"
        focusable="false"
      >
        <path
          class="lane-panel__wave lane-panel__wave--top"
          d="M3 6q5-6 10 0t10 0t10 0t10 0t10 0t10 0t10 0t10 0"
        />
        <path
          class="lane-panel__wave lane-panel__wave--bottom"
          d="M3 13q5-6 10 0t10 0t10 0t10 0t10 0t10 0t10 0t10 0"
        />
      </svg>

      <DoodleBtn tone="teal" @click="emit('create')">新建对话</DoodleBtn>

      <template v-for="(lane, index) in lanes" :key="lane.thread_id">
        <div
          v-if="renamingId === lane.thread_id"
          class="lane-panel__lane lane-panel__lane--editing"
          :class="{ 'is-current': lane.thread_id === currentId }"
        >
          <input
            :ref="bindRenameInput"
            v-model="draft"
            class="lane-panel__rename"
            maxlength="80"
            aria-label="对话名称"
            @keydown.enter.prevent="commitRename"
            @keydown.esc.stop="cancelRename"
            @blur="commitRename"
          />
        </div>

        <div
          v-else
          class="lane-panel__lane"
          :class="{ 'is-current': lane.thread_id === currentId }"
        >
          <button type="button" class="lane-panel__open" @click="emit('open', lane.thread_id)">
            <span class="lane-panel__lane-name">{{ lane.title || `对话 ${index + 1}` }}</span>
            <span class="lane-panel__lane-state">{{ threadStatusLabel(lane.status) }}</span>
          </button>
          <div class="lane-panel__actions">
            <button
              type="button"
              class="lane-panel__act"
              aria-label="重命名"
              title="重命名"
              @click.stop="startRename(lane)"
            >
              ✎
            </button>
            <button
              type="button"
              class="lane-panel__act lane-panel__act--danger"
              aria-label="删除"
              title="删除"
              @click.stop="emit('remove', lane.thread_id)"
            >
              ✕
            </button>
          </div>
        </div>
      </template>
    </aside>

    <slot />

    <div class="lane-column__split" role="separator" aria-orientation="vertical" />
  </div>
</template>

<style scoped>
.lane-column {
  position: relative;
  height: 100%;

  display: flex;
  flex-direction: column;
  gap: var(--app-space-lg);
}

.lane-column__split {
  position: absolute;
  top: 0;

  right: calc(var(--app-space-lg) / -2);
  bottom: 0;
  width: 0;
  border-left: 1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent);
}

.lane-panel {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding: var(--app-space-md);
  background: var(--paper);

  border: 1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent);
  border-radius: var(--app-radius-md);
}

.lane-panel__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.lane-panel__title {
  margin: 0;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
}

.lane-panel__count {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.lane-panel__waves {
  display: block;
  margin-bottom: var(--app-space-xs);
}

.lane-panel__wave {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.5;
}

.lane-panel__wave--top {
  stroke: var(--assistant-marker);
}

.lane-panel__wave--bottom {
  stroke: var(--c-ai);
}

.lane-panel__lane {
  position: relative;
  display: flex;
  align-items: stretch;
  min-height: 40px;
  padding: 0 var(--app-space-sm);
  border: 1px solid var(--app-border-strong);
  border-radius: 2px;
  background: var(--app-bg-card);
}

.lane-panel__lane:hover {
  border-color: var(--ink);
}

.lane-panel__lane.is-current {
  background: color-mix(in srgb, var(--c-workflow) 40%, var(--app-bg-card));
  border: 2px solid var(--ink);
}

.lane-panel__open {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-size: var(--app-size-sm);
  text-align: left;
  cursor: pointer;
}

.lane-panel__lane:focus-within {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

.lane-panel__lane-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lane-panel__lane-state {
  flex: none;
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.lane-panel__actions {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 2px;
  padding-right: var(--app-space-xs);
  background: inherit;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--app-duration-fast) var(--app-ease);
}

.lane-panel__lane:hover .lane-panel__actions,
.lane-panel__lane:focus-within .lane-panel__actions {
  opacity: 1;
  pointer-events: auto;
}

@media (hover: none) {
  .lane-panel__actions {
    opacity: 1;
    pointer-events: auto;
  }
}

.lane-panel__act {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 2px;
  background: transparent;
  color: var(--app-text-secondary);
  font-family: inherit;
  font-size: var(--app-size-sm);
  line-height: 1;
  cursor: pointer;
}

.lane-panel__act:hover {
  background: var(--app-highlight);
  color: var(--ink);
}

.lane-panel__act--danger:hover {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}

.lane-panel__act:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

.lane-panel__rename {
  width: 100%;
  min-height: 38px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-size: var(--app-size-sm);
}

.lane-panel__rename:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .lane-panel__actions {
    transition: none;
  }
}
</style>
