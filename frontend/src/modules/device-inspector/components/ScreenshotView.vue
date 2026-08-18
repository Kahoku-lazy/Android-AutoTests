<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { wsUrl } from '@/shared/ws-url'
import { getToken } from '@/shared/auth/token-storage'
import { apiGetScreenshot } from '../api'
import { IconDevice } from '@/shared/icons'

const props = defineProps({
  screenW: { type: Number, default: 1440 },
  screenH: { type: Number, default: 3040 },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  ocrResults: { type: Array, default: () => [] },
  selectedOcr: { type: Object, default: null },
  active: { type: Boolean, default: false },
})
const emit = defineEmits(['click-element', 'click-ocr', 'device-changed', 'screenshot-update'])

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
    if (data.status && data.image) {
      applyScreenshot(data.image, data.format || 'jpeg')
      wsState.value = 'connected'
      statusMessage.value = ''
      if (data.screen_w) emit('device-changed', data)
      return true
    }
    if (data.message) {
      wsState.value = 'no_device'
      statusMessage.value = data.message
      if (!silent) ElMessage.error(data.message)
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
  const token = getToken()
  if (!token) return
  const url = `${wsUrl('/ws/screenshot')}?token=${encodeURIComponent(token)}`
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

  props.ocrResults.forEach(ocr => {
    const isSelected = props.selectedOcr && ocr === props.selectedOcr
    if (isSelected) {
      ctx.fillStyle = 'rgba(231,76,60,0.15)'
      ctx.fillRect(
        Math.round(ocr.x * s), Math.round(ocr.y * s),
        Math.round(ocr.width * s), Math.round(ocr.height * s),
      )
      ctx.strokeStyle = '#e74c3c'
      ctx.lineWidth = 2.5
    } else {
      ctx.strokeStyle = 'rgba(167,139,250,0.55)'
      ctx.lineWidth = 1.2
    }
    ctx.strokeRect(
      Math.round(ocr.x * s), Math.round(ocr.y * s),
      Math.round(ocr.width * s), Math.round(ocr.height * s),
    )
  })
}

function onImgLoad() {
  scheduleDrawOverlay()
}

watch(() => props.selected, () => scheduleDrawOverlay())
watch(() => props.selectedOcr, () => scheduleDrawOverlay())
// Shallow watch — parent passes new array reference when elements change
watch(() => props.elements, () => scheduleDrawOverlay())
watch(() => props.ocrResults, () => scheduleDrawOverlay())
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

function hitTestOcr(clientX, clientY) {
  const img = imgRef.value
  if (!img) return null
  const rect = img.getBoundingClientRect()
  const s = displayScale()
  if (!s) return null
  const x = Math.round((clientX - rect.left) / s)
  const y = Math.round((clientY - rect.top) / s)
  let best = null
  let bestArea = Infinity
  for (const ocr of props.ocrResults) {
    if (x >= ocr.x && x <= ocr.x + ocr.width && y >= ocr.y && y <= ocr.y + ocr.height) {
      const area = ocr.width * ocr.height
      if (area > 0 && area < bestArea) {
        bestArea = area
        best = ocr
      }
    }
  }
  return best
}

function onScreenClick(e) {
  const ocrHit = hitTestOcr(e.clientX, e.clientY)
  if (ocrHit) {
    emit('click-ocr', ocrHit)
    return
  }
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
        <span class="no-signal__icon"><IconDevice :size="32" /></span>
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
          <span ref="noDeviceIconRef" class="no-signal__icon"><IconDevice :size="32" /></span>
          <p ref="noDeviceTitleRef" class="no-signal__title">设备未连接~</p>
          <p class="no-signal__hint">在上方下拉框选择设备并点击「连接」后开始</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./ScreenshotView.css"></style>
