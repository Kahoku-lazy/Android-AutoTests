<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { animate } from 'animejs'
import { mediaUrl } from '../store'
import { IconDevice } from '@/shared/icons'

const props = defineProps({
  screenW: { type: Number, default: 1440 },
  screenH: { type: Number, default: 3040 },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  ocrResults: { type: Array, default: () => [] },
  selectedOcr: { type: Object, default: null },
  screenshotPath: { type: String, default: '' },
})
const emit = defineEmits(['click-element', 'click-ocr'])

const imgRef = ref(null)
const overlayRef = ref(null)
const screenInnerRef = ref(null)
const imgBoxRef = ref(null)
const hovered = ref(null)

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
    scheduleDrawOverlay()
  })
  // 初始渲染时机：mounted 时 refs 已就绪，直接 observe + 首帧校正
  // （watch(ref) 默认 pre-flush 会错过本次赋值，这里补一次兜底）
  nextTick(() => {
    if (screenInnerRef.value) {
      resizeObserver.observe(screenInnerRef.value)
      fitBox()
      scheduleDrawOverlay()
    }
  })
})

watch(screenInnerRef, (el, prev) => {
  if (!resizeObserver) return
  if (prev) resizeObserver.unobserve(prev)
  if (el) {
    resizeObserver.observe(el)
    fitBox()
    scheduleDrawOverlay()
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  stopNoDeviceAnimation()
})

watch(() => props.screenshotPath, (val) => {
  if (val) stopNoDeviceAnimation()
  else startNoDeviceAnimation()
  nextTick(() => {
    fitBox()
    scheduleDrawOverlay()
  })
})

// ── 选中联动：表格选中元素 → 截图区滚动到该位置（在可视区外时平滑滚动）──

const phoneFrameRef = ref(null)

function scrollToRow(el) {
  const box = imgBoxRef.value
  const frame = phoneFrameRef.value
  if (!box || !frame || !el || !props.screenW) return
  const scale = box.clientWidth / props.screenW
  if (!scale) return
  const centerY = (el.y + (el.height || 0) / 2) * scale
  const viewTop = frame.scrollTop
  const viewBottom = frame.scrollTop + frame.clientHeight
  if (centerY < viewTop || centerY > viewBottom) {
    frame.scrollTo({ top: Math.max(0, centerY - frame.clientHeight / 2), behavior: 'smooth' })
  }
}

watch(() => props.selected, (el) => {
  if (!el) return
  scheduleDrawOverlay()
  nextTick(() => scrollToRow(el))
})
watch(() => props.selectedOcr, (t) => {
  if (!t) return
  scheduleDrawOverlay()
  nextTick(() => scrollToRow(t))
})

// ── 图片盒按屏幕比例精确适配容器（JS 计算，避免 aspect-ratio 双约束变形）──

function fitBox() {
  const frame = phoneFrameRef.value
  const box = imgBoxRef.value
  if (!frame || !box || !props.screenW || !props.screenH) return
  const cw = frame.clientWidth - 24   // 减去 phone-frame padding（12×2）
  const ch = frame.clientHeight - 24
  if (cw < 10 || ch < 10) return
  const scale = Math.min(cw / props.screenW, ch / props.screenH)
  box.style.width = `${Math.floor(props.screenW * scale)}px`
  box.style.height = `${Math.floor(props.screenH * scale)}px`
}

// ── Overlay ──

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
  if (!img || !canvas || !props.screenshotPath) return
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
      ctx.fillStyle = 'rgba(231,76,60,0.15)'
      ctx.fillRect(Math.round(el.x * s), Math.round(el.y * s), Math.round(el.width * s), Math.round(el.height * s))
      ctx.strokeStyle = '#e74c3c'
      ctx.lineWidth = 2.5
    } else if (isHovered) {
      ctx.fillStyle = 'rgba(255,152,0,0.10)'
      ctx.fillRect(Math.round(el.x * s), Math.round(el.y * s), Math.round(el.width * s), Math.round(el.height * s))
      ctx.strokeStyle = '#ff9800'
      ctx.lineWidth = 2
    } else {
      ctx.strokeStyle = 'rgba(64,158,255,0.5)'
      ctx.lineWidth = 1.2
    }
    ctx.strokeRect(Math.round(el.x * s), Math.round(el.y * s), Math.round(el.width * s), Math.round(el.height * s))
  })

  props.ocrResults.forEach(ocr => {
    const isSelected = props.selectedOcr && ocr === props.selectedOcr
    if (isSelected) {
      ctx.fillStyle = 'rgba(231,76,60,0.15)'
      ctx.fillRect(Math.round(ocr.x * s), Math.round(ocr.y * s), Math.round(ocr.width * s), Math.round(ocr.height * s))
      ctx.strokeStyle = '#e74c3c'
      ctx.lineWidth = 2.5
    } else {
      ctx.strokeStyle = 'rgba(167,139,250,0.55)'
      ctx.lineWidth = 1.2
    }
    ctx.strokeRect(Math.round(ocr.x * s), Math.round(ocr.y * s), Math.round(ocr.width * s), Math.round(ocr.height * s))
  })
}

function onImgLoad() {
  fitBox()
  scheduleDrawOverlay()
}

watch(() => props.selected, () => scheduleDrawOverlay())
watch(() => props.selectedOcr, () => scheduleDrawOverlay())
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
  if (mousemoveRaf) return
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
    <div ref="phoneFrameRef" class="phone-frame">
      <!-- 快照截图（静态，按屏幕比例自适应）+ 边界框 overlay 贴图 -->
      <div v-if="screenshotPath" class="screen-wrap">
        <div ref="screenInnerRef" class="screen-inner">
          <div ref="imgBoxRef" class="img-box">
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
      </div>

      <!-- 无快照 → 空态 -->
      <div v-else class="no-signal no-signal--idle">
        <div class="no-device-animation">
          <div class="no-device-rings">
            <div ref="ringOuterRef" class="no-device-ring no-device-ring--outer"></div>
            <div ref="ringInnerRef" class="no-device-ring no-device-ring--inner"></div>
          </div>
          <span ref="noDeviceIconRef" class="no-signal__icon"><IconDevice :size="32" /></span>
          <p ref="noDeviceTitleRef" class="no-signal__title">暂无页面快照</p>
          <p class="no-signal__hint">选择设备与方法后点击「获取」，或从快照列表 / 已保存页面回看</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./ScreenshotView.css"></style>
