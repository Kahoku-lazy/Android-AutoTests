<script setup lang="ts">
/**
 * 本栏运行日志面板：一轮一张手绘虚线卡（顶部胶带），纯渲染，取数与打开由 chat.vue 负责。
 *
 * 进行中的一轮只显示「还在写」，不打开半份文件，也不伪造时间。
 * 面板本身不描边、不滚；卡片在本面板内堆叠，滚动交给 `.doc-body`。
 */
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { logCardTime } from "../helpers/time-label"
import type { ThreadLog } from "../types"

defineProps<{ logs: ThreadLog[]; loading: boolean; error: string }>()
const emit = defineEmits<{
  open: [item: ThreadLog]
  retry: []
  close: []
}>()

/** 卡片上的时间：有消息时间用消息时间，老数据回落编号；进行中给占位符。 */
function cardTime(item: ThreadLog): string {
  return logCardTime(item.created_at, item.report_id) || "—"
}

/** 卡片正文：进行中的一轮不重复后端那句「还在写」。 */
function cardSummary(item: ThreadLog): string {
  if (item.writing) return "这一轮还在跑"
  return item.summary || "无摘要"
}
</script>

<template>
  <section class="thread-log" aria-label="运行日志">
    <header class="thread-log__head">
      <h2 class="thread-log__title">运行日志</h2>
      <span class="thread-log__count">{{ logs.length }} 轮</span>
      <button type="button" class="thread-log__close" @click="emit('close')">收起</button>
    </header>

    <SkeletonCard v-if="loading" variant="list" :lines="3" />
    <ErrorState v-else-if="error" :message="error" @retry="emit('retry')" />
    <EmptyState
      v-else-if="!logs.length"
      text="这一栏还没有运行日志"
      hint="跑完一轮，就能回看那时候发生了什么。"
    />
    <ul v-else class="thread-log__list">
      <li v-for="(item, index) in logs" :key="item.report_id || index" class="thread-log__item">
        <button
          type="button"
          class="thread-log__card"
          :disabled="item.writing"
          @click="emit('open', item)"
        >
          <span class="thread-log__tape" aria-hidden="true" />
          <span class="thread-log__meta">
            <time class="thread-log__time" :datetime="item.created_at || item.report_id">
              {{ cardTime(item) }}
            </time>
            <span class="thread-log__state">{{ item.writing ? "还在写" : "查看" }}</span>
          </span>
          <span class="thread-log__summary">{{ cardSummary(item) }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.thread-log {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  min-width: 0;
}

.thread-log__head {
  display: flex;
  align-items: baseline;
  gap: var(--app-space-sm);
}

.thread-log__title {
  margin: 0;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
}

.thread-log__count {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.thread-log__close {
  margin-left: auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--app-text-secondary);
  font-family: inherit;
  font-size: var(--app-size-xs);
  cursor: pointer;
}

.thread-log__close:hover {
  color: var(--ink);
}

.thread-log__close:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

/* 卡片列表：卡片顶部胶带外挑 8px，间距留给它 */
.thread-log__list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  margin: var(--app-space-sm) 0 0;
  padding: 0;
  list-style: none;
}

.thread-log__item {
  position: relative;
}

/* 一轮一张手绘虚线卡：虚线框 + 顶部胶带 + 硬影；按需求不倾斜 */
.thread-log__card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  width: 100%;
  padding: var(--app-space-md);
  border: 1.5px dashed color-mix(in srgb, var(--assistant-marker) 70%, var(--paper));
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--assistant-marker) 24%, transparent);
  color: var(--ink);
  font-family: inherit;
  font-size: var(--app-size-sm);
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

.thread-log__card:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 5px 5px 0 0 color-mix(in srgb, var(--assistant-marker) 32%, transparent);
}

.thread-log__card:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

/* 进行中：虚线框转浅墨、去硬影，卡片不可点 */
.thread-log__card:disabled {
  border-color: color-mix(in srgb, var(--ink) 22%, transparent);
  background: var(--app-bg-subtle);
  box-shadow: none;
  color: var(--app-text-secondary);
  cursor: not-allowed;
}

/* 顶部居中胶带：卡片的装饰，不拦点击 */
.thread-log__tape {
  position: absolute;
  top: -8px;
  left: 50%;
  width: 56px;
  height: 14px;
  transform: translateX(-50%);
  border: 1px solid color-mix(in srgb, var(--assistant-marker) 38%, transparent);
  background: color-mix(in srgb, var(--assistant-marker) 26%, var(--paper));
  pointer-events: none;
}

.thread-log__card:disabled .thread-log__tape {
  opacity: 0.45;
}

.thread-log__meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.thread-log__time {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.thread-log__state {
  flex: none;
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.thread-log__summary {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .thread-log__card,
  .thread-log__card:hover:not(:disabled) {
    transform: none;
    transition: none;
  }
}
</style>
