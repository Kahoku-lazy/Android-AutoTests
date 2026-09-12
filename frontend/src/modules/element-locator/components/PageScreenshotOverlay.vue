<script setup lang="ts">
/**
 * 页面截图 + 元素矩形叠加。
 * 点击矩形高亮并向上抛出元素 id。
 */
import { computed, nextTick, ref, watch } from 'vue'
import { mediaPathToUrl, resolveElementRect, type ElementRect } from '../helpers/element-bounds'

export interface OverlayElement {
  id: number
  x?: number
  y?: number
  width?: number
  height?: number
  bounds?: string
}

const props = defineProps<{
  screenshotPath: string
  elements: OverlayElement[]
  selectedId: number | null
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

const frameRef = ref<HTMLElement | null>(null)
const naturalW = ref(0)
const naturalH = ref(0)
const hoveredId = ref<number | null>(null)

const screenshotUrl = computed(() => mediaPathToUrl(props.screenshotPath))

interface RectItem {
  id: number
  rect: ElementRect
}

const rectItems = computed<RectItem[]>(() => {
  const items: RectItem[] = []
  for (const el of props.elements) {
    const rect = resolveElementRect(el)
    if (!rect) continue
    items.push({ id: el.id, rect })
  }
  return items
})

const viewBox = computed(() => {
  if (naturalW.value > 0 && naturalH.value > 0) {
    return `0 0 ${naturalW.value} ${naturalH.value}`
  }
  // 截图未加载时，用元素最大边界兜底
  let maxX = 1
  let maxY = 1
  for (const item of rectItems.value) {
    maxX = Math.max(maxX, item.rect.x + item.rect.width)
    maxY = Math.max(maxY, item.rect.y + item.rect.height)
  }
  return `0 0 ${maxX} ${maxY}`
})

function onImgLoad(e: Event) {
  const img = e.target as HTMLImageElement
  naturalW.value = img.naturalWidth || 0
  naturalH.value = img.naturalHeight || 0
  void scrollSelectedIntoView()
}

function onRectClick(id: number, e: MouseEvent) {
  e.stopPropagation()
  emit('select', id)
}

function onCanvasClick(e: MouseEvent) {
  const svg = e.currentTarget as SVGSVGElement
  const pt = svg.createSVGPoint()
  pt.x = e.clientX
  pt.y = e.clientY
  const ctm = svg.getScreenCTM()
  if (!ctm) return
  const local = pt.matrixTransform(ctm.inverse())
  let best: RectItem | null = null
  let bestArea = Infinity
  for (const item of rectItems.value) {
    const { x, y, width, height } = item.rect
    if (local.x >= x && local.x <= x + width && local.y >= y && local.y <= y + height) {
      const area = width * height
      if (area > 0 && area < bestArea) {
        bestArea = area
        best = item
      }
    }
  }
  if (best) emit('select', best.id)
}

async function scrollSelectedIntoView() {
  const id = props.selectedId
  if (id == null || !frameRef.value) return
  const item = rectItems.value.find((r) => r.id === id)
  if (!item || !naturalW.value || !naturalH.value) return
  const frame = frameRef.value
  const stage = frame.querySelector('.shot-pane__stage') as HTMLElement | null
  const stageW = stage?.clientWidth || frame.clientWidth
  const scale = stageW / naturalW.value
  if (!scale) return
  const centerY = (item.rect.y + item.rect.height / 2) * scale
  const viewTop = frame.scrollTop
  const viewBottom = frame.scrollTop + frame.clientHeight
  if (centerY < viewTop + 24 || centerY > viewBottom - 24) {
    frame.scrollTo({
      top: Math.max(0, centerY - frame.clientHeight / 2),
      behavior: 'smooth',
    })
  }
}

watch(
  () => props.selectedId,
  async () => {
    await nextTick()
    await scrollSelectedIntoView()
  },
)
</script>

<template>
  <div class="shot-pane">
    <div v-if="!screenshotPath" class="shot-pane__empty">
      <p class="shot-pane__empty-title">暂无页面截图</p>
      <p class="shot-pane__empty-hint">从设备检查器导入快照后可在此圈选元素</p>
    </div>
    <div v-else ref="frameRef" class="shot-pane__frame">
      <div class="shot-pane__stage">
        <img
          class="shot-pane__img"
          :src="screenshotUrl"
          alt="页面截图"
          draggable="false"
          @load="onImgLoad"
        />
        <svg
          class="shot-pane__overlay"
          :viewBox="viewBox"
          preserveAspectRatio="xMidYMin meet"
          @click="onCanvasClick"
        >
          <template v-for="item in rectItems" :key="item.id">
            <!-- 选中：外圈红线，形成红+绿双色描边 -->
            <rect
              v-if="item.id === selectedId"
              class="shot-rect shot-rect--active-ring"
              :x="item.rect.x"
              :y="item.rect.y"
              :width="item.rect.width"
              :height="item.rect.height"
              pointer-events="none"
            />
            <rect
              class="shot-rect"
              :class="{
                'shot-rect--active': item.id === selectedId,
                'shot-rect--hover': item.id === hoveredId && item.id !== selectedId,
              }"
              :x="item.rect.x"
              :y="item.rect.y"
              :width="item.rect.width"
              :height="item.rect.height"
              @click="onRectClick(item.id, $event)"
              @mouseenter="hoveredId = item.id"
              @mouseleave="hoveredId = null"
            />
          </template>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shot-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  min-width: 0;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--paper);
  overflow: hidden;
}
.shot-pane__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--app-space-xs);
  padding: var(--app-space-lg);
  text-align: center;
}
.shot-pane__empty-title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.shot-pane__empty-hint {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.shot-pane__frame {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
  padding: var(--app-space-sm);
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.shot-pane__stage {
  position: relative;
  /* 截图显示压缩：不全宽铺开，便于同屏看更多区域 */
  width: min(100%, 420px);
  line-height: 0;
}
.shot-pane__img {
  width: 100%;
  height: auto;
  display: block;
  user-select: none;
  pointer-events: none;
}
.shot-pane__overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: crosshair;
}
/* 未选中：红色描边，无填充 */
.shot-rect {
  fill: transparent;
  stroke: var(--app-status-danger-text);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
  cursor: pointer;
}
.shot-rect--hover {
  fill: color-mix(in srgb, var(--app-status-danger) 18%, transparent);
  stroke: var(--app-status-danger-text);
  stroke-width: 2.5;
}
/* 选中：淡绿填充 + 绿描边（外圈另有红环） */
.shot-rect--active-ring {
  fill: none;
  stroke: var(--app-status-danger-text);
  stroke-width: 5;
  vector-effect: non-scaling-stroke;
  pointer-events: none;
}
.shot-rect--active {
  fill: color-mix(in srgb, var(--app-status-success-bg) 72%, transparent);
  stroke: var(--app-status-success-text);
  stroke-width: 2.5;
}
</style>
