<script setup lang="ts">
/**
 * 对话栏面板：纸卡 + 浅墨虚线框 + 该助手笔色的双波浪线。
 *
 * 对话页左栏专用：不做倾斜，虚线只属于这一个卡片（登记在
 * doodle-craft `references/components/assistant-marker-card.md`）。
 * 每个对话栏支持就地重命名与删除，具体接口由父组件调。
 */

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

/** 就地改名：把该行切成输入框并聚焦全选。 */
async function startRename(lane: AssistantThread): Promise<void> {
  renamingId.value = lane.thread_id
  draft.value = lane.title || ""
  await nextTick()
  renameInput.value?.focus()
  renameInput.value?.select()
}

/** 提交改名；空标题由父组件当作"恢复默认名"。 */
function commitRename(): void {
  if (!renamingId.value) return
  const id = renamingId.value
  renamingId.value = ""
  emit("rename", id, draft.value.trim())
}

/** Esc 取消：先清状态，再让随后的 blur 直接返回。 */
function cancelRename(): void {
  renamingId.value = ""
}

/** v-for 里的单例输入框：用函数 ref 取元素，避免模板 ref 退化成数组。 */
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

      <!-- 新建对话：Teal 键（参考 Sketched UI Kit 的 Teal 变体） -->
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

    <!-- 左栏附加内容（对话页的运行日志卡）：与对话栏同列堆叠 -->
    <slot />

    <!-- 两栏之间的纵向虚线分隔：拉满整列高度，只由本组件声明 -->
    <div class="lane-column__split" role="separator" aria-orientation="vertical" />
  </div>
</template>

<style scoped>
.lane-column {
  position: relative;
  height: 100%;
  /* 对话栏在上、日志卡在下：左栏自己是一列，分隔线是绝对定位、不参与这层排布 */
  display: flex;
  flex-direction: column;
  gap: var(--app-space-lg);
}

.lane-column__split {
  position: absolute;
  top: 0;
  /* 落在两栏 24px 间距的中线：与面板右边框留 12px，不贴着卡片 */
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
  /* 浅墨虚线：比颜料片轻一档，卡片本体不倾斜。
     四边闭合；两栏分隔线另算，落在右侧间距中线，不贴卡边 */
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

/* 对话栏条目：外层是卡片，内层按钮负责"选中/打开"，动作按钮浮在右端 */
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

/* 选中的对话栏：浅蓝色填充（需求方指定），描边仍用墨色 */
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

/* 动作按钮：悬停或键盘进入本行时浮出，底色跟随本行（白 / 浅蓝） */
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

/* 触屏没有 hover：动作常显 */
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

/* 就地改名：整行变成输入框，几何不变避免跳动 */
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
