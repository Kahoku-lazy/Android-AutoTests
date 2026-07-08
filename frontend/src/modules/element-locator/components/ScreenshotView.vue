<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { wsUrl } from '@/shared/ws-url.js'
import { apiGetScreenshot } from '../api.js'

const props = defineProps({
  screenW: { type: Number, default: 1440 },
  screenH: { type: Number, default: 3040 },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
})
const emit = defineEmits(['click-element', 'do-action', 'device-changed'])

const screenshotUrl = ref('')
const ws = ref(null)
const wsState = ref('connecting') // connecting | connected | no_device | error
const statusMessage = ref('正在连接截图流…')
const imgRef = ref(null)
const overlayRef = ref(null)
const screenInnerRef = ref(null)
const hovered = ref(null)

let blobUrl = null
let resizeObserver = null
let frameTimer = null
let pendingFrame = null
let reconnectTimer = null
let snapshotTimer = null
const FRAME_INTERVAL_MS = 200

const placeholderText = computed(() => {
  if (wsState.value === 'connecting') return '正在连接截图流…'
  if (wsState.value === 'no_device') return statusMessage.value || '请先在上方选择设备'
  if (wsState.value === 'error') return statusMessage.value || '截图获取失败'
  if (wsState.value === 'connected') return '等待设备画面…'
  return '暂无设备画面'
})

const aspectStyle = computed(() => {
  if (!props.screenW || !props.screenH) return {}
  return {
    aspectRatio: `${props.screenW} / ${props.screenH}`,
    '--phone-w': props.screenW,
    '--phone-h': props.screenH,
  }
})

onMounted(() => {
  fetchSnapshot({ silent: true })
  connectWS()
  resizeObserver = new ResizeObserver(() => scheduleDrawOverlay())
})

watch(screenInnerRef, (el, prev) => {
  if (!resizeObserver) return
  if (prev) resizeObserver.unobserve(prev)
  if (el) resizeObserver.observe(el)
})

onUnmounted(() => {
  ws.value?.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (snapshotTimer) clearTimeout(snapshotTimer)
  if (frameTimer) clearTimeout(frameTimer)
  resizeObserver?.disconnect()
  revokeBlobUrl()
})

async function fetchSnapshot({ silent = false } = {}) {
  try {
    const { data } = await apiGetScreenshot()
    if (data.ok && data.image) {
      applyScreenshot(data.image, data.format || 'jpeg')
      wsState.value = 'connected'
      statusMessage.value = ''
      if (data.screen_w) emit('device-changed', data)
      return true
    }
    if (data.error) {
      wsState.value = 'no_device'
      statusMessage.value = data.error
      if (!silent) ElMessage.error(data.error)
    }
    return false
  } catch (e) {
    if (!silent) ElMessage.error(e?.message || '截图获取失败')
    return false
  }
}

async function refresh() {
  return fetchSnapshot()
}

defineExpose({ refresh })

function revokeBlobUrl() {
  if (blobUrl) {
    URL.revokeObjectURL(blobUrl)
    blobUrl = null
  }
}

function connectWS() {
  wsState.value = 'connecting'
  statusMessage.value = '正在连接截图流…'
  const url = wsUrl('/ws/screenshot')
  ws.value = new WebSocket(url)
  ws.value.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      if (msg.type === 'device_changed') {
        wsState.value = 'connected'
        emit('device-changed', msg)
      } else if (msg.type === 'screenshot' && msg.image) {
        wsState.value = 'connected'
        statusMessage.value = ''
        queueScreenshot(msg.image, msg.format || 'jpeg')
      } else if (msg.type === 'no_device') {
        wsState.value = 'no_device'
        statusMessage.value = msg.message || '未选择设备'
        revokeBlobUrl()
        screenshotUrl.value = ''
      } else if (msg.type === 'screenshot_error') {
        wsState.value = 'error'
        statusMessage.value = msg.message || '截图失败'
      }
    } catch (_) {}
  }
  ws.value.onopen = () => {
    wsState.value = 'connected'
    statusMessage.value = screenshotUrl.value ? '' : '已连接，正在获取画面…'
    emit('device-changed', { type: 'connected' })
    if (!screenshotUrl.value) fetchSnapshot({ silent: true })
  }
  ws.value.onerror = () => {
    wsState.value = 'error'
    statusMessage.value = '截图流连接失败，3 秒后重试'
  }
  ws.value.onclose = () => {
    wsState.value = 'connecting'
    statusMessage.value = '连接已断开，正在重连…'
    reconnectTimer = setTimeout(connectWS, 3000)
  }
}

function queueScreenshot(b64, format) {
  pendingFrame = { b64, format }
  if (frameTimer) return
  frameTimer = setTimeout(flushScreenshot, FRAME_INTERVAL_MS)
}

function flushScreenshot() {
  frameTimer = null
  if (!pendingFrame) return
  const { b64, format } = pendingFrame
  pendingFrame = null
  applyScreenshot(b64, format)
}

function applyScreenshot(b64, format) {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  revokeBlobUrl()
  blobUrl = URL.createObjectURL(new Blob([bytes], { type: `image/${format}` }))
  screenshotUrl.value = blobUrl
}

function displayScale() {
  const img = imgRef.value
  if (!img?.clientWidth || !props.screenW) return 0
  return img.clientWidth / props.screenW
}

function scheduleDrawOverlay() {
  nextTick(() => requestAnimationFrame(drawOverlay))
}

function drawOverlay() {
  const img = imgRef.value
  const canvas = overlayRef.value
  if (!img || !canvas || !screenshotUrl.value) return
  const w = img.clientWidth
  const h = img.clientHeight
  if (w < 10 || h < 10) return
  canvas.width = w
  canvas.height = h
  const s = w / props.screenW
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, w, h)

  if (hovered.value) {
    const el = hovered.value
    ctx.fillStyle = 'rgba(255,193,7,0.18)'
    ctx.fillRect(
      Math.round(el.x * s), Math.round(el.y * s),
      Math.round(el.width * s), Math.round(el.height * s),
    )
  }

  props.elements.forEach(el => {
    if (!el.clickable && !el.text && !el.resource_id) return
    const isHovered = hovered.value && el._idx === hovered.value._idx
    const isSelected = props.selected && el._idx === props.selected._idx

    if (isSelected) {
      ctx.strokeStyle = '#e74c3c'
      ctx.lineWidth = 2
    } else if (isHovered) {
      ctx.strokeStyle = '#ff9800'
      ctx.lineWidth = 2
    } else {
      ctx.strokeStyle = 'rgba(64,158,255,0.5)'
      ctx.lineWidth = 1.2
    }
    ctx.strokeRect(
      Math.round(el.x * s), Math.round(el.y * s),
      Math.round(el.width * s), Math.round(el.height * s),
    )
  })
}

function onImgLoad() {
  scheduleDrawOverlay()
}

watch(() => props.selected, () => scheduleDrawOverlay())
watch(() => props.elements, () => scheduleDrawOverlay(), { deep: true })
watch([() => props.screenW, () => props.screenH], () => scheduleDrawOverlay())

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
    if (x >= el.x && x <= el.x + el.width && y >= el.y && y <= el.y + el.height) {
      const area = el.width * el.height
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

function onMouseMove(e) {
  const hit = hitTest(e.clientX, e.clientY)
  if (hit !== hovered.value) {
    hovered.value = hit
    scheduleDrawOverlay()
  }
  if (overlayRef.value) {
    overlayRef.value.style.cursor = hit ? 'pointer' : 'crosshair'
  }
}

function onMouseLeave() {
  if (hovered.value) {
    hovered.value = null
    scheduleDrawOverlay()
    if (overlayRef.value) overlayRef.value.style.cursor = 'crosshair'
  }
}
</script>

<template>
  <div class="screenshot-panel">
    <div class="phone-frame">
      <div v-if="screenshotUrl" class="screen-wrap">
        <div ref="screenInnerRef" class="screen-inner" :style="aspectStyle">
          <img
            ref="imgRef"
            :src="screenshotUrl"
            class="screen-img"
            draggable="false"
            @load="onImgLoad"
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
      <div v-else class="no-signal" :class="`no-signal--${wsState}`">
        <span class="no-signal__icon">📱</span>
        <p class="no-signal__title">{{ placeholderText }}</p>
        <p v-if="wsState === 'no_device'" class="no-signal__hint">在设备管理连接设备后，于上方下拉框选择</p>
        <p v-else-if="wsState === 'error'" class="no-signal__hint">请确认后端服务与 ADB 设备已就绪</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screenshot-panel {
  height: 100%;
  min-height: 420px;
  width: 100%;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  display: flex;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.phone-frame {
  container-type: size;
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  box-sizing: border-box;
}
.screen-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}
.screen-inner {
  position: relative;
  line-height: 0;
  width: min(100cqw, calc(100cqh * var(--phone-w) / var(--phone-h)));
  height: min(100cqh, calc(100cqw * var(--phone-h) / var(--phone-w)));
}
.screen-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
}
.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: crosshair;
}
.no-signal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  padding: 24px;
  color: #988B7A;
}
.no-signal__icon {
  font-size: 36px;
  opacity: 0.7;
}
.no-signal__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #725d42;
}
.no-signal__hint {
  margin: 0;
  font-size: 12px;
  color: #9f927d;
  max-width: 220px;
  line-height: 1.5;
}
.no-signal--error .no-signal__title { color: #b33a3a; }
</style>
