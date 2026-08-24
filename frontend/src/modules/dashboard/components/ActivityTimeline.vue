<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { staggerReveal } from '@/shared/animations'
import type { ActivityItem } from '@/shared/types/dashboard'

const props = withDefaults(defineProps<{ items?: ActivityItem[] }>(), {
  items: () => [],
})

const listRef = ref<HTMLElement | null>(null)

async function revealItems() {
  await nextTick()
  if (!listRef.value) return
  const children = listRef.value.querySelectorAll('.timeline-item')
  if (children.length) staggerReveal(children, 100, 0.95)
}

onMounted(revealItems)
watch(() => props.items.length, revealItems)
</script>

<template>
  <div class="activity-timeline">
    <h3 class="timeline__title">最近活动</h3>
    <div ref="listRef" class="timeline__list">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="timeline-item"
        :class="'timeline-item--' + (item.type || 'info')"
      >
        <div class="timeline-item__dot">
          <div class="timeline-item__dot-inner"></div>
        </div>
        <div class="timeline-item__content">
          <div class="timeline-item__header">
            <span class="timeline-item__action">{{ item.action }}</span>
            <span class="timeline-item__time">{{ item.time }}</span>
          </div>
          <p v-if="item.detail" class="timeline-item__detail">{{ item.detail }}</p>
          <div v-if="item.tags" class="timeline-item__tags">
            <span v-for="(tag, ti) in item.tags" :key="ti" class="timeline-item__tag">{{ tag }}</span>
          </div>
        </div>
        <div v-if="i < items.length - 1" class="timeline-item__line"></div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!items.length" class="timeline__empty">
      <p>暂无活动记录</p>
    </div>
  </div>
</template>

<style scoped>
.activity-timeline {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.timeline__title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 16px;
}

.timeline__list {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.timeline__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-ink-muted);
  font-size: var(--app-size-sm);
}

/* Item */
.timeline-item {
  position: relative;
  padding-left: 30px;
  padding-bottom: 20px;
  opacity: 0;
}

.timeline-item:last-child { padding-bottom: 0; }

.timeline-item__dot {
  position: absolute;
  left: 0;
  top: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--app-timeline-dot);
  background: var(--app-bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

/* 事件类型样式（PRD §2.3）：run=测试执行→紫，agent=智能体更新→黄；枚举外值用默认灰 */
.timeline-item--run .timeline-item__dot { border-color: var(--app-status-purple); }
.timeline-item--agent .timeline-item__dot { border-color: var(--c-dashboard); }

.timeline-item__dot-inner {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--app-timeline-dot);
}
.timeline-item--run .timeline-item__dot-inner { background: var(--app-status-purple); }
.timeline-item--agent .timeline-item__dot-inner { background: var(--c-dashboard); }

.timeline-item__line {
  position: absolute;
  left: 6px;
  top: 22px;
  bottom: 0;
  width: 2px;
  border-radius: 2px;
  background: repeating-linear-gradient(0deg, var(--app-border-light) 0px, var(--app-border-light) 3px, transparent 3px, transparent 6px);
}

.timeline-item__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.timeline-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.timeline-item__action {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}

.timeline-item__time {
  font-size: var(--app-size-xs);
  color: var(--app-ink-muted);
  flex-shrink: 0;
}

.timeline-item__detail {
  font-size: var(--app-size-sm);
  color: var(--app-ink-muted);
  margin: 0;
  line-height: 1.5;
}

.timeline-item__tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.timeline-item__tag {
  font-size: var(--app-size-xs);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--app-bg-subtle);
  border: 1px solid var(--app-border-light);
  color: var(--app-ink-muted);
  font-weight: 600;
}
</style>
