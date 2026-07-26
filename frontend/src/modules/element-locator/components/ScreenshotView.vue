<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { wsUrl } from '@/shared/ws-url.js'
import { apiGetScreenshot } from '../api.js'

const props = defineProps({
  screenW: { type: Number, default: 1440 },
  screenH: { type: Number, default: 3040 },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  active: { type: Boolean, default: false },
})
const emit = defineEmits(['click-element', 'do-action', 'device-changed', 'screenshot-update'])

const screenshotUrl = ref('')
const ws = ref(null)
const wsState = ref('connecting')
const statusMessage = ref('正在连接截图流…')
const imgRef = ref(null)
const overlayRef = ref(null)
const screenInnerRef = ref(null)
const hovered = ref(null)

// ── No-device animation refs ──
const ringOuterRef = ref(null)
const ringInnerRef = ref(null)
const noDeviceIconRef = ref(null)
const noDeviceTitleRef = ref(null)

let resizeObserver = null
let frameTimer = null
let pendingFrame = null
let reconnectTimer = null
let snapshotTimer = null
let pollTimer = null
const FRAME_INTERVAL_MS = 250
const POLL_INTERVAL_MS = 250

let noDeviceAnimeInstances = []

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
        noDeviceAnimeInstances.push(animate(el, {
          translateY: [-8, 8],
          duration: 2500,
          loop: true,
          ease: 'inOutSine',
          direction: 'alternate',
        }))
      } else if (key === 'title') {
        noDeviceAnimeInstances.push(animate(el, {
          opacity: [0.55, 1],
          duration: 2500,
          loop: true,
          ease: 'inOutSine',
          direction: 'alternate',
        }))
      } else if (key === 'ringOuter') {
        noDeviceAnimeInstances.push(animate(el, {
          scale: [0.85, 1.2],
          opacity: [0.28, 0.04],
          duration: 3000,
          loop: true,
          ease: 'inOutSine',
          direction: 'alternate',
        }))
      } else if (key === 'ringInner') {
        noDeviceAnimeInstances.push(animate(el, {
          scale: [0.9, 1.3],
          opacity: [0.22, 0.04],
          duration: 2200,
          loop: true,
          ease: 'inOutSine',
          direction: 'alternate',
        }))
      }
    }
  })
}

function stopNoDeviceAnimation() {
  noDeviceAnimeInstances.forEach(inst => { try { inst.pause() } catch (_) {} })
  noDeviceAnimeInstances = []
}

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

// ── Lifecycle ──

onMounted(() => {
  if (props.active) {
    startPolling()
    connectWS()
  } else {
    startNoDeviceAnimation()
  }
  resizeObserver = new ResizeObserver(() => scheduleDrawOverlay())
})

watch(screenInnerRef, (el, prev) => {
  if (!resizeObserver) return
  if (prev) resizeObserver.unobserve(prev)
  if (el) resizeObserver.observe(el)
})

onUnmounted(() => {
  teardown()
})

// ── active gate: when parent connects/disconnects ──

watch(() => props.active, (val) => {
  if (val) {
    stopNoDeviceAnimation()
    startPolling()
    connectWS()
  } else {
    teardown()
    // Clear screenshot immediately
    revokeBlobUrl()
    screenshotUrl.value = ''
    startNoDeviceAnimation()
  }
})

function teardown() {
  ws.value?.close()
  ws.value = null
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (snapshotTimer) { clearTimeout(snapshotTimer); snapshotTimer = null }
  if (frameTimer) { clearTimeout(frameTimer); frameTimer = null }
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  stopNoDeviceAnimation()
}

// ── Screenshot polling (250 ms) ──

function startPolling() {
  stopPolling()
  fetchSnapshot({ silent: true })
  pollTimer = setInterval(() => {
    fetchSnapshot({ silent: true })
  }, POLL_INTERVAL_MS)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// ── REST screenshot ──

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

defineExpose({ refresh, redraw: scheduleDrawOverlay })

// ── WebSocket ──

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
    } catch (e) { console.error(e); }
  }
  ws.value.onopen = () => {
    wsState.value = 'connected'
    statusMessage.value = screenshotUrl.value ? '' : '已连接，正在获取画面…'
    emit('device-changed', { type: 'connected' })
    if (!screenshotUrl.value) fetchSnapshot({ silent: true })
    // WebSocket connected — stop redundant HTTP polling
    stopPolling()
  }
  ws.value.onerror = () => {
    wsState.value = 'error'
    statusMessage.value = '截图流连接失败，3 秒后重试'
  }
  ws.value.onclose = () => {
    if (!props.active) return  // don't reconnect if parent disconnected
    wsState.value = 'connecting'
    statusMessage.value = '连接已断开，正在重连…'
    // Restart HTTP polling as fallback while WS reconnects
    startPolling()
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
  // Use data URL directly — browser decodes natively (much faster than atob + byte loop)
  screenshotUrl.value = `data:image/${format};base64,${b64}`
  emit('screenshot-update', { url: screenshotUrl.value })
}

function displayScale() {
  const img = imgRef.value
  if (!img?.clientWidth || !props.screenW) return 0
  return img.clientWidth / props.screenW
}

let overlayDrawPending = false

function scheduleDrawOverlay() {
  if (overlayDrawPending) return
  overlayDrawPending = true
  nextTick(() => {
    requestAnimationFrame(() => {
      overlayDrawPending = false
      drawOverlay()
    })
  })
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
      // Fill with semi-transparent color for readability
      ctx.fillStyle = 'rgba(231,76,60,0.15)'
      ctx.fillRect(
        Math.round(el.x * s), Math.round(el.y * s),
        Math.round(el.width * s), Math.round(el.height * s),
      )
      ctx.strokeStyle = '#e74c3c'
      ctx.lineWidth = 2.5
    } else if (isHovered) {
      ctx.fillStyle = 'rgba(255,152,0,0.10)'
      ctx.fillRect(
        Math.round(el.x * s), Math.round(el.y * s),
        Math.round(el.width * s), Math.round(el.height * s),
      )
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
// Shallow watch — parent passes new array reference when elements change
watch(() => props.elements, () => scheduleDrawOverlay())
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

let mousemoveRaf = null

function onMouseMove(e) {
  if (mousemoveRaf) return // throttle to one hit-test per animation frame
  mousemoveRaf = requestAnimationFrame(() => {
    mousemoveRaf = null
    const hit = hitTest(e.clientX, e.clientY)
    if (hit !== hovered.value) {
      hovered.value = hit
      scheduleDrawOverlay()
    }
    if (overlayRef.value) {
      overlayRef.value.style.cursor = hit ? 'pointer' : 'crosshair'
    }
  })
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
      <!-- Active + screenshot → phone screen -->
      <div v-if="active && screenshotUrl" class="screen-wrap">
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

      <!-- Active but no screenshot yet → WS state placeholder -->
      <div v-else-if="active && !screenshotUrl" class="no-signal" :class="`no-signal--${wsState}`">
        <span class="no-signal__icon">📱</span>
        <p class="no-signal__title">{{ placeholderText }}</p>
        <p v-if="wsState === 'error'" class="no-signal__hint">请确认后端服务与 ADB 设备已就绪</p>
      </div>

      <!-- Not active → idle animation -->
      <div v-else class="no-signal no-signal--idle">
        <div class="no-device-animation">
          <div class="no-device-rings">
            <div ref="ringOuterRef" class="no-device-ring no-device-ring--outer"></div>
            <div ref="ringInnerRef" class="no-device-ring no-device-ring--inner"></div>
          </div>
          <span ref="noDeviceIconRef" class="no-signal__icon">📱</span>
          <p ref="noDeviceTitleRef" class="no-signal__title">设备未连接~</p>
          <p class="no-signal__hint">在上方下拉框选择设备并点击「连接」后开始</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screenshot-panel {
  height: 100%;
  min-height: 0;
  width: 100%;
  background: #fff);
  
  border-radius: 20px;
  border: 1px solid var(--ink));
  display: flex;
  overflow: hidden;
  box-shadow: 2px 3px 0 rgba(0,0,0,0.05);
  position: relative;
  padding-top: 6px;
}
.screenshot-panel::before {
  content: '';
  position: absolute;
  top: 4px; left: 50%; transform: translateX(-50%);
  width: 9px; height: 9px;
  background: radial-gradient(circle, #e8e0d5 30%, #c0b8a8 60%, #a09080 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08);
  z-index: 10;
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
  border-radius: 6px 10px 6px 10px;
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
  color: var(--app-ink-muted);
}
.no-signal__icon {
  font-size: var(--app-size-2xl);
  opacity: 0.7;
}
.no-signal__title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-ink);
}
.no-signal__hint {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-ink-muted);
  max-width: 220px;
  line-height: 1.5;
}
.no-signal--error .no-signal__title { color: var(--app-status-danger-text); }

/* ── No-device idle animation ── */
.no-device-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
}
.no-device-rings {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.no-device-ring {
  position: absolute;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.no-device-ring--outer {
  width: 110px;
  height: 110px;
  border: 3px solid var(--app-ink, #2d2d2d);
}
.no-device-ring--inner {
  width: 78px;
  height: 78px;
  border: 3px solid var(--app-ink, #2d2d2d);
}
</style>
