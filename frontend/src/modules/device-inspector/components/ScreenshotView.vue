<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { animate } from 'animejs'
import { mediaUrl } from '../store'
import { IconDevice } from '@/shared/icons'

/** groupColor 未传或非法时的兜底色（沿用历史分组框的蓝，避免整屏无框线） */
const FALLBACK_GROUP_COLOR = '#409eff'
/** 被展示裁剪丢弃的元素用虚线描边（画布坐标系下的短划长度） */
const DASH_PATTERN = [6, 4]

const props = defineProps({
  screenW: { type: Number, default: 1440 },
  screenH: { type: Number, default: 3040 },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  screenshotPath: { type: String, default: '' },
  /** 当前分组色（#rgb / #rrggbb）；缺省时用兜底色 */
  groupColor: { type: String, default: '' },
})
const emit = defineEmits(['click-element'])

const imgRef = ref(null)
const overlayRef = ref(null)
const screenInnerRef = ref(null)
const imgBoxRef = ref(null)
const hovered = ref(null)
/** 截图文件已失效（404）：降级为失效空态，MUST NOT 留空白画面 */
const shotFailed = ref(false)

// ── 两层画布 ──
// 底层（离屏 canvas，不进 DOM）：缓存「当前分组的全部元素框」，只在元素集 / 分组色 / 截图 / 尺寸变化时重画。
// 可见层（overlayRef）：每次把底层缓存贴上来，再画 hover 与选中（至多 4 个矩形）。
// 因此鼠标在同一分组内移动时，可见层的绘制量与分组规模无关。
let groupLayer = null
let groupLayerDirty = true
let drawPending = false

// ── No-snapshot idle animation ──
const ringOuterRef = ref(null)
const ringInnerRef = ref(null)
const noDeviceIconRef = ref(null)
const noDeviceTitleRef = ref(null)

let resizeObserver = null
let noDeviceAnimeInstances = []

const screenshotUrl = computed(() => mediaUrl(props.screenshotPath))

function startNoDeviceAnimation() {
  stopNoDeviceAnimation()
  nextTick(() => {
    const targets = [
      { el: noDeviceIconRef.value, key: 'icon' },
      { el: noDeviceTitleRef.value, key: 'title' },
      { el: ringOuterRef.value, key: 'ringOuter' },
      { el: ringInnerRef.value, key: 'ringInner' },
    ]
    for (const { el, key } of targets) {
      if (!el) continue
      if (key === 'icon') {
        noDeviceAnimeInstances.push(animate(el, { translateY: [-8, 8], duration: 2500, loop: true, ease: 'inOutSine', direction: 'alternate' }))
      } else if (key === 'title') {
        noDeviceAnimeInstances.push(animate(el, { opacity: [0.55, 1], duration: 2500, loop: true, ease: 'inOutSine', direction: 'alternate' }))
      } else if (key === 'ringOuter') {
        noDeviceAnimeInstances.push(animate(el, { scale: [0.85, 1.2], opacity: [0.28, 0.04], duration: 3000, loop: true, ease: 'inOutSine', direction: 'alternate' }))
      } else if (key === 'ringInner') {
        noDeviceAnimeInstances.push(animate(el, { scale: [0.9, 1.3], opacity: [0.22, 0.04], duration: 2200, loop: true, ease: 'inOutSine', direction: 'alternate' }))
      }
    }
  })
}

function stopNoDeviceAnimation() {
  noDeviceAnimeInstances.forEach(inst => { try { inst.pause() } catch (_) {} })
  noDeviceAnimeInstances = []
}

onMounted(() => {
  if (!props.screenshotPath) startNoDeviceAnimation()
  resizeObserver = new ResizeObserver(() => {
    fitBox()
    scheduleGroupDraw()
  })
  // 初始渲染时机：mounted 时 refs 已就绪，直接 observe + 首帧校正
  // （watch(ref) 默认 pre-flush 会错过本次赋值，这里补一次兜底）
  nextTick(() => {
    if (screenInnerRef.value) {
      resizeObserver.observe(screenInnerRef.value)
      fitBox()
      scheduleGroupDraw()
    }
  })
})

watch(screenInnerRef, (el, prev) => {
  if (!resizeObserver) return
  if (prev) resizeObserver.unobserve(prev)
  if (el) {
    resizeObserver.observe(el)
    fitBox()
    scheduleGroupDraw()
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  stopNoDeviceAnimation()
})

watch(() => props.screenshotPath, (val) => {
  shotFailed.value = false   // 换了一份快照就重置失效标记
  if (val) stopNoDeviceAnimation()
  else startNoDeviceAnimation()
  nextTick(() => {
    fitBox()
    scheduleGroupDraw()
  })
})

/** 坐标与比例的唯一基准：已加载截图的真实像素（截图就是整屏图）。
 *  截图未就绪时用传入的屏幕尺寸兜底——已保存页面不携带屏幕尺寸，不能拿它当基准。 */
function sourceSize() {
  const img = imgRef.value
  const w = img?.naturalWidth || props.screenW
  const h = img?.naturalHeight || props.screenH
  if (!w || !h) return null
  return { w, h }
}

// ── 选中联动：表格选中元素 → 截图区滚动到该位置（在可视区外时平滑滚动）──

const phoneFrameRef = ref(null)

function scrollToRow(el) {
  const box = imgBoxRef.value
  const frame = phoneFrameRef.value
  const size = sourceSize()
  if (!box || !frame || !el || !size) return
  const scale = box.clientWidth / size.w
  if (!scale) return
  const target = boxOf(el)
  if (!target) return
  const centerY = (target.y + target.h / 2) * scale
  const viewTop = frame.scrollTop
  const viewBottom = frame.scrollTop + frame.clientHeight
  if (centerY < viewTop || centerY > viewBottom) {
    frame.scrollTo({ top: Math.max(0, centerY - frame.clientHeight / 2), behavior: 'smooth' })
  }
}

/** 选中联动：选中即重绘高亮并在视区外滚动过去；清空选中同样要重绘（擦掉旧高亮），
 *  故重绘不设守卫、只有滚动才要求有选中元素。选中只影响可见层，不动底层缓存。 */
watch(() => props.selected, (el) => {
  scheduleDraw()
  if (!el) return
  nextTick(() => scrollToRow(el))
})
// ── 图片盒按屏幕比例精确适配容器（JS 计算，避免 aspect-ratio 双约束变形）──

function fitBox() {
  const frame = phoneFrameRef.value
  const box = imgBoxRef.value
  const size = sourceSize()
  if (!frame || !box || !size) return
  const cw = frame.clientWidth - 24   // 减去 phone-frame padding（12×2）
  const ch = frame.clientHeight - 24
  if (cw < 10 || ch < 10) return
  const scale = Math.min(cw / size.w, ch / size.h)
  box.style.width = `${Math.floor(size.w * scale)}px`
  box.style.height = `${Math.floor(size.h * scale)}px`
}

// ── Overlay ──

function displayScale() {
  const img = imgRef.value
  const size = sourceSize()
  if (!img?.clientWidth || !size) return 0
  return img.clientWidth / size.w
}

/** 可见层调度：同一帧内多次调用只画一次（hover 高频触发时靠它合并） */
function scheduleDraw() {
  if (drawPending) return
  drawPending = true
  nextTick(() => {
    requestAnimationFrame(() => {
      drawPending = false
      drawVisible()
    })
  })
}

/** 底层失效调度：元素集 / 分组色 / 截图 / 尺寸变化时标记底层需重画，下一帧连底层一起画 */
function scheduleGroupDraw() {
  groupLayerDirty = true
  scheduleDraw()
}

/** 元素行键：新数据形态带 seq，旧形态带 _idx；都没有时退回对象引用 */
function elKey(el) {
  if (!el) return null
  if (el._idx !== undefined) return `i${el._idx}`
  if (el.seq !== undefined) return `s${el.seq}`
  return el
}

/** 框归一化：优先取 coords{x,y,w,h}（分层接口形态），其次 x/y/width/height，最后从 bounds 文本解析 */
function boxOf(el) {
  const coords = el?.coords
  if (coords) {
    const cx = Number(coords.x)
    const cy = Number(coords.y)
    const cw = Number(coords.w)
    const ch = Number(coords.h)
    if ([cx, cy, cw, ch].every(Number.isFinite)) return { x: cx, y: cy, w: cw, h: ch }
  }
  let x = Number(el?.x)
  let y = Number(el?.y)
  let w = Number(el?.width)
  let h = Number(el?.height)
  if (![x, y, w, h].every(Number.isFinite) && typeof el?.bounds === 'string') {
    const m = el.bounds.match(/\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]/)
    if (m) {
      x = Number(m[1])
      y = Number(m[2])
      w = Number(m[3]) - x
      h = Number(m[4]) - y
    }
  }
  if (![x, y, w, h].every(Number.isFinite)) return null
  return { x, y, w, h }
}

function strokeBox(ctx, box, scale) {
  ctx.strokeRect(
    Math.round(box.x * scale), Math.round(box.y * scale),
    Math.round(box.w * scale), Math.round(box.h * scale),
  )
}

function fillBox(ctx, box, scale) {
  ctx.fillRect(
    Math.round(box.x * scale), Math.round(box.y * scale),
    Math.round(box.w * scale), Math.round(box.h * scale),
  )
}

/** 分组色归一化为 #rrggbb；空值或非法值回落兜底色 */
function normalizeColor(raw) {
  const value = String(raw || '').trim()
  const short = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i.exec(value)
  if (short) return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`
  if (/^#[0-9a-f]{6}$/i.test(value)) return value
  return FALLBACK_GROUP_COLOR
}

/** 同色系 rgba（填充用） */
function withAlpha(hex, alpha) {
  const n = parseInt(normalizeColor(hex).slice(1), 16)
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`
}

/** 可见画布的像素尺寸（未就绪返回 null） */
function canvasSize() {
  const img = imgRef.value
  if (!img) return null
  const w = img.clientWidth
  const h = img.clientHeight
  if (w < 10 || h < 10) return null
  return { w, h }
}

/** 底层：把「当前分组的全部元素框」画进离屏画布。
 *  只按「框有效」过滤（w > 0 且 h > 0）——纯容器没有 resource-id/text/desc/clickable，同样要圈出来。
 *  线型：kept_in_snapshot 为假用虚线（被展示裁剪丢弃），否则实线；描边与填充取分组色同色系。 */
function drawGroupLayer() {
  const size = canvasSize()
  const source = sourceSize()
  if (!size || !source || !props.screenshotPath) return
  if (!groupLayer) groupLayer = document.createElement('canvas')
  groupLayer.width = size.w
  groupLayer.height = size.h
  const ctx = groupLayer.getContext('2d')
  ctx.clearRect(0, 0, size.w, size.h)
  const scale = size.w / source.w
  ctx.fillStyle = withAlpha(props.groupColor, 0.12)
  ctx.strokeStyle = normalizeColor(props.groupColor)
  ctx.lineWidth = 1.2
  for (const el of props.elements) {
    const box = boxOf(el)
    if (!box || box.w <= 0 || box.h <= 0) continue
    ctx.setLineDash(el.kept_in_snapshot === false ? DASH_PATTERN : [])
    fillBox(ctx, box, scale)
    strokeBox(ctx, box, scale)
  }
  ctx.setLineDash([])
  groupLayerDirty = false
}

/** 可见层：贴底层缓存 + 只画 hover 与选中（至多 2 + 2 个矩形，与分组规模无关） */
function drawVisible() {
  const size = canvasSize()
  const canvas = overlayRef.value
  if (!size || !canvas || !props.screenshotPath) return

  if (groupLayerDirty || !groupLayer || groupLayer.width !== size.w || groupLayer.height !== size.h) {
    drawGroupLayer()
  }
  if (canvas.width !== size.w || canvas.height !== size.h) {
    canvas.width = size.w
    canvas.height = size.h
  }

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, size.w, size.h)
  ctx.setLineDash([])
  if (groupLayer) ctx.drawImage(groupLayer, 0, 0)

  const source = sourceSize()
  const scale = source ? size.w / source.w : 0
  const selected = props.selected
  const selectedKey = elKey(selected)
  const selectedEl = selected
    ? (props.elements.find(el => elKey(el) === selectedKey) || selected)
    : null
  const hoveredKey = elKey(hovered.value)

  if (scale && hovered.value && hoveredKey !== selectedKey) {
    const box = boxOf(hovered.value)
    if (box && box.w > 0 && box.h > 0) {
      ctx.fillStyle = 'rgba(255,193,7,0.18)'
      fillBox(ctx, box, scale)
      ctx.strokeStyle = '#ff9800'
      ctx.lineWidth = 2
      strokeBox(ctx, box, scale)
    }
  }

  const selectedBox = selectedEl ? boxOf(selectedEl) : null
  if (scale && selectedBox && selectedBox.w > 0 && selectedBox.h > 0) {
    ctx.fillStyle = 'rgba(231,76,60,0.4)'
    fillBox(ctx, selectedBox, scale)
    ctx.strokeStyle = '#e74c3c'
    ctx.lineWidth = 3
    strokeBox(ctx, selectedBox, scale)
  }
}

function onImgLoad() {
  fitBox()
  scheduleGroupDraw()
}

/** 截图加载失败（文件已随快照删除等）：切到失效空态并让空态动画接手 */
function onShotError() {
  shotFailed.value = true
  nextTick(() => startNoDeviceAnimation())
}

// 底层缓存的三类失效源：元素集、分组色、兜底尺寸
watch(() => props.elements, () => scheduleGroupDraw())
watch(() => props.groupColor, () => scheduleGroupDraw())
watch([() => props.screenW, () => props.screenH], () => scheduleGroupDraw())

function hitTest(clientX, clientY) {
  const img = imgRef.value
  if (!img) return null
  const rect = img.getBoundingClientRect()
  const s = displayScale()
  if (!s) return null
  const x = Math.round((clientX - rect.left) / s)
  const y = Math.round((clientY - rect.top) / s)
  let best = null
  let bestArea = Infinity
  for (const el of props.elements) {
    const box = boxOf(el)
    if (!box || box.w <= 0 || box.h <= 0) continue
    if (x >= box.x && x <= box.x + box.w && y >= box.y && y <= box.y + box.h) {
      const area = box.w * box.h
      if (area > 0 && area < bestArea) {
        bestArea = area
        best = el
      }
    }
  }
  return best
}

function onScreenClick(e) {
  const hit = hitTest(e.clientX, e.clientY)
  if (hit) emit('click-element', hit)
}

function onScreenContextMenu(e) { e.preventDefault(); onScreenClick(e) }

let mousemoveRaf = null

function onMouseMove(e) {
  if (mousemoveRaf) return
  mousemoveRaf = requestAnimationFrame(() => {
    mousemoveRaf = null
    const hit = hitTest(e.clientX, e.clientY)
    if (hit !== hovered.value) {
      hovered.value = hit
      scheduleDraw()
    }
    if (overlayRef.value) {
      overlayRef.value.style.cursor = hit ? 'pointer' : 'crosshair'
    }
  })
}

function onMouseLeave() {
  if (hovered.value) {
    hovered.value = null
    scheduleDraw()
    if (overlayRef.value) overlayRef.value.style.cursor = 'crosshair'
  }
}

</script>

<template>
  <div class="screenshot-panel">
    <div ref="phoneFrameRef" class="phone-frame">
      <!-- 快照截图（静态，按屏幕比例自适应）+ 边界框 overlay 贴图 -->
      <div v-if="screenshotPath && !shotFailed" class="screen-wrap">
        <div ref="screenInnerRef" class="screen-inner">
          <div ref="imgBoxRef" class="img-box">
            <img
              ref="imgRef"
              :src="screenshotUrl"
              class="screen-img"
              draggable="false"
              @load="onImgLoad"
              @error="onShotError"
            />
            <canvas
              ref="overlayRef"
              class="overlay"
              @click="onScreenClick"
              @contextmenu="onScreenContextMenu"
              @mousemove="onMouseMove"
              @mouseleave="onMouseLeave"
            />
          </div>
        </div>
      </div>

      <!-- 无快照 → 空态 -->
      <div v-else class="no-signal no-signal--idle">
        <div class="no-device-animation">
          <div class="no-device-rings">
            <div ref="ringOuterRef" class="no-device-ring no-device-ring--outer"></div>
            <div ref="ringInnerRef" class="no-device-ring no-device-ring--inner"></div>
          </div>
          <span ref="noDeviceIconRef" class="no-signal__icon"><IconDevice :size="32" /></span>
          <p ref="noDeviceTitleRef" class="no-signal__title">
            {{ shotFailed ? '截图已失效' : '暂无页面快照' }}
          </p>
          <p class="no-signal__hint">
            {{ shotFailed
              ? '该页面的截图文件已不存在，请重新获取或换一份快照回看'
              : '选择设备后点击「获取」，或从快照列表 / 已保存页面回看' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./ScreenshotView.css"></style>