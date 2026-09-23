<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from "vue"
import { staggerReveal } from "@/shared/animations"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { fetchRecentActivities } from "../api"
import type { ActivityItem } from "@/shared/types/dashboard"

/** 主屏最多展示条数；与后端缺省 limit、十条槽位一致 */
const BOARD_LIMIT = 10
/** 历史弹层每页条数 */
const HISTORY_PAGE = 50

const props = withDefaults(defineProps<{ items?: ActivityItem[] }>(), {
  items: () => [],
})

const listRef = ref<HTMLElement | null>(null)

/** 主屏只渲染最新十条 */
const boardItems = computed(() => props.items.slice(0, BOARD_LIMIT))

async function revealItems() {
  await nextTick()
  if (!listRef.value) return
  const children = listRef.value.querySelectorAll(".timeline-item")
  if (children.length) staggerReveal(children, 100, 0.95)
}

onMounted(revealItems)
watch(() => boardItems.value.length, revealItems)

// ── 活动历史弹层 ──
const historyOpen = ref(false)
const historyItems = ref<ActivityItem[]>([])
const historyOffset = ref(BOARD_LIMIT)
const historyLoading = ref(false)
const historyError = ref<string | null>(null)
const historyHasMore = ref(false)
/** 丢弃过期的历史请求结果（防并发重置） */
let historyReqSeq = 0

async function loadHistoryPage(reset: boolean) {
  const seq = ++historyReqSeq
  historyLoading.value = true
  historyError.value = null
  try {
    const offset = reset ? BOARD_LIMIT : historyOffset.value
    const res = await fetchRecentActivities({ offset, limit: HISTORY_PAGE })
    if (seq !== historyReqSeq) return
    const body = res.data
    if (!body?.status) {
      historyError.value = body?.message || "历史活动加载失败"
      if (reset) historyItems.value = []
      historyHasMore.value = false
      return
    }
    const page = body.data || []
    historyItems.value = reset ? page : [...historyItems.value, ...page]
    historyOffset.value = offset + page.length
    historyHasMore.value = page.length >= HISTORY_PAGE
  } catch {
    if (seq !== historyReqSeq) return
    historyError.value = "历史活动加载失败，请稍后重试"
    if (reset) historyItems.value = []
    historyHasMore.value = false
  } finally {
    if (seq === historyReqSeq) historyLoading.value = false
  }
}

async function openHistory() {
  historyOpen.value = true
  historyItems.value = []
  historyOffset.value = BOARD_LIMIT
  historyHasMore.value = false
  await loadHistoryPage(true)
}

function loadMoreHistory() {
  if (historyLoading.value || !historyHasMore.value) return
  void loadHistoryPage(false)
}

defineExpose({ openHistory, loadMoreHistory, historyItems, historyHasMore })
</script>

<template>
  <div class="activity-timeline">
    <div class="timeline__head">
      <h3 class="timeline__title">最近活动</h3>
      <DoodleBtn tone="paper" type="button" @click="openHistory">查看历史</DoodleBtn>
    </div>

    <div ref="listRef" class="timeline__list">
      <div
        v-for="(item, i) in boardItems"
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
            <span v-for="(tag, ti) in item.tags" :key="ti" class="timeline-item__tag">{{
              tag
            }}</span>
          </div>
        </div>
        <div v-if="i < boardItems.length - 1" class="timeline-item__line"></div>
      </div>

      <div v-if="!boardItems.length" class="timeline__empty">
        <p>暂无活动记录</p>
      </div>
    </div>

    <el-dialog v-model="historyOpen" title="活动历史" width="560px" append-to-body destroy-on-close>
      <div v-if="historyError" class="timeline-history__error">{{ historyError }}</div>
      <div v-else-if="!historyItems.length && !historyLoading" class="timeline-history__empty">
        没有更多历史记录
      </div>
      <ul v-else class="timeline-history__list">
        <li
          v-for="(item, i) in historyItems"
          :key="i"
          class="timeline-history__row"
          :class="'timeline-item--' + (item.type || 'info')"
        >
          <span class="timeline-history__action">{{ item.action }}</span>
          <span class="timeline-history__time">{{ item.time }}</span>
          <p v-if="item.detail" class="timeline-history__detail">{{ item.detail }}</p>
        </li>
      </ul>
      <div v-if="historyLoading" class="timeline-history__loading">加载中…</div>
      <template #footer>
        <DoodleBtn
          v-if="historyHasMore"
          tone="paper"
          type="button"
          :disabled="historyLoading"
          @click="loadMoreHistory"
        >
          加载更多
        </DoodleBtn>
        <DoodleBtn tone="paper" type="button" @click="historyOpen = false">关闭</DoodleBtn>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.activity-timeline {
  /* 单槽≈标题行 + 条目底距，十条固定可视高度 */
  --timeline-slot: calc(var(--app-size-sm) * 1.5 + var(--app-space-xl));
  height: 100%;
  display: flex;
  flex-direction: column;
}

.timeline__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
  margin: 0 0 var(--app-space-md);
}

.timeline__title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}

.timeline__list {
  flex: 1;
  min-height: calc(var(--timeline-slot) * 10);
  overflow-y: auto;
  padding-right: var(--app-space-sm);
}

.timeline__empty {
  min-height: calc(var(--timeline-slot) * 10);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
}

/* Item */
.timeline-item {
  position: relative;
  padding-left: 30px;
  padding-bottom: var(--app-space-md);
  opacity: 0;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

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
  z-index: var(--z-base);
}

/* 事件类型样式（PRD §2.3）：run=测试执行→紫，agent=智能体更新→黄；枚举外值用默认灰 */
.timeline-item--run .timeline-item__dot {
  border-color: var(--app-status-purple);
}
.timeline-item--agent .timeline-item__dot {
  border-color: var(--c-dashboard);
}

.timeline-item__dot-inner {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--app-timeline-dot);
}
.timeline-item--run .timeline-item__dot-inner {
  background: var(--app-status-purple);
}
.timeline-item--agent .timeline-item__dot-inner {
  background: var(--c-dashboard);
}

.timeline-item__line {
  position: absolute;
  left: 6px;
  top: 22px;
  bottom: 0;
  width: 2px;
  border-radius: 2px;
  background: repeating-linear-gradient(
    0deg,
    var(--app-border-light) 0px,
    var(--app-border-light) 3px,
    transparent 3px,
    transparent 6px
  );
}

.timeline-item__content {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
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
  color: var(--app-text-secondary);
  flex-shrink: 0;
}

.timeline-item__detail {
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
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
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-pill);
  background: var(--app-bg-subtle);
  border: 1px solid var(--app-border-light);
  color: var(--app-text-secondary);
  font-weight: 600;
}

.timeline-history__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  max-height: 60vh;
  overflow-y: auto;
}

.timeline-history__row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--app-space-xs) var(--app-space-md);
  padding: var(--app-space-sm) 0;
  border-bottom: 1px dashed var(--app-border-light);
}

.timeline-history__action {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}

.timeline-history__time {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.timeline-history__detail {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}

.timeline-history__empty,
.timeline-history__error,
.timeline-history__loading {
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  text-align: center;
  padding: var(--app-space-lg) 0;
}

.timeline-history__error {
  color: var(--app-status-danger);
}
</style>
