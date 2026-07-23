<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { staggerReveal } from '@/shared/animations.js'

const props = defineProps({
  items: { type: Array, default: () => [] },
})

const listRef = ref(null)

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
  font-family: var(--font-display, 'Quicksand', sans-serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary, #4a4e69);
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
  color: var(--text-secondary, #9a8c98);
  font-size: 13px;
}

/* Item */
.timeline-item {
  position: relative;
  padding-left: 28px;
  padding-bottom: 20px;
  opacity: 0;
}

.timeline-item:last-child { padding-bottom: 0; }

.timeline-item__dot {
  position: absolute;
  left: 0;
  top: 4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--text-secondary, #9a8c98);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.timeline-item--success .timeline-item__dot { border-color: #10b981; }
.timeline-item--warning .timeline-item__dot { border-color: #f59e0b; }
.timeline-item--error .timeline-item__dot { border-color: #ef4444; }

.timeline-item__dot-inner {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: #999;
}
.timeline-item--success .timeline-item__dot-inner { background: #6BCB77; }
.timeline-item--warning .timeline-item__dot-inner { background: #F7C948; }
.timeline-item--error .timeline-item__dot-inner   { background: #FFB5A7; }

.timeline-item__line {
  position: absolute;
  left: 7px;
  top: 22px;
  bottom: 0;
  width: 1.5px;
  background: repeating-linear-gradient(0deg, #d4cdc0 0px, #d4cdc0 3px, transparent 3px, transparent 6px);
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
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #4a4e69);
}

.timeline-item__time {
  font-size: 11px;
  color: var(--text-secondary, #9a8c98);
  flex-shrink: 0;
}

.timeline-item__detail {
  font-size: 12px;
  color: var(--text-secondary, #9a8c98);
  margin: 0;
  line-height: 1.5;
}

.timeline-item__tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.timeline-item__tag {
  font-size: 9px;
  padding: 2px 7px;
  border-radius: 3px 6px 3px 6px;
  background: #f8f6f2;
  border: 1px solid #e8ecf1;
  color: #999;
  font-weight: 600;
}
</style>
