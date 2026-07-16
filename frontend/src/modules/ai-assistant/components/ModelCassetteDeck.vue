<script setup>
/**
 * 卡带仓模型选择器 — 换带抽出/插入 + 上带保存（anime.js）
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { animate } from 'animejs'
import { buttonPress, particleBurst } from '@/shared/animations.js'

const props = defineProps({
  agentId: { type: [Number, String], required: true },
  provider: { type: String, default: '' },
  options: { type: Array, default: () => [] }, // { label, value }[]
  modelValue: { type: String, default: '' },
  savedModel: { type: String, default: '' },
  confirming: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const trayOpen = ref(false)
const swapping = ref(false)
const deckRef = ref(null)
const tapeRef = ref(null)
const trayRef = ref(null)

const dirty = computed(() => props.modelValue && props.modelValue !== props.savedModel)
const displayName = computed(() => props.modelValue || props.savedModel || '未选择')

const TAPE_PALETTE = [
  ['#19c8b9', '#14b3a5'],
  ['#889df0', '#6f87e6'],
  ['#f7cd67', '#e0b52e'],
  ['#f8a6b2', '#e88a9a'],
  ['#b39ef3', '#9b85e0'],
  ['#6fba2c', '#5aa31f'],
  ['#f5a623', '#e09415'],
]

function tapeColors(name) {
  let h = 0
  const s = String(name || '')
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return TAPE_PALETTE[h % TAPE_PALETTE.length]
}

const currentColors = computed(() => tapeColors(displayName.value))

function toggleTray() {
  if (swapping.value) return
  trayOpen.value = !trayOpen.value
  nextTick(() => {
    const tray = trayRef.value
    if (!tray) return
    if (trayOpen.value) {
      animate(tray, {
        opacity: [0, 1],
        scaleY: [0.55, 1],
        translateY: [-6, 0],
        duration: 320,
        ease: 'outBack(1.4)',
      })
    }
  })
}

async function pickModel(value) {
  if (swapping.value || value === props.modelValue) {
    trayOpen.value = false
    return
  }
  swapping.value = true
  trayOpen.value = false
  const tape = tapeRef.value
  if (tape) {
    await new Promise((resolve) => {
      animate(tape, {
        translateY: [0, -28],
        rotate: [0, -6],
        opacity: [1, 0],
        scale: [1, 0.92],
        duration: 280,
        ease: 'inCubic',
        onComplete: resolve,
      })
    })
  }
  emit('update:modelValue', value)
  await nextTick()
  const tape2 = tapeRef.value
  if (tape2) {
    await new Promise((resolve) => {
      animate(tape2, {
        translateY: [-32, 0],
        rotate: [5, 0],
        opacity: [0, 1],
        scale: [0.9, 1.06, 1],
        duration: 420,
        ease: 'outBack(1.7)',
        onComplete: resolve,
      })
    })
  }
  swapping.value = false
  // 未保存：卡带边框脉冲提示
  if (value !== props.savedModel && tapeRef.value) {
    animate(tapeRef.value, {
      boxShadow: [
        '0 2px 0 rgba(139,115,85,0.15)',
        '0 0 0 3px rgba(247,205,103,0.55)',
        '0 2px 0 rgba(139,115,85,0.15)',
      ],
      duration: 900,
      loop: 2,
      ease: 'inOutSine',
    })
  }
}

async function onConfirm(ev) {
  if (!dirty.value || props.confirming) return
  const btn = ev?.currentTarget
  if (btn) buttonPress(btn)
  if (ev?.clientX != null) particleBurst(ev.clientX, ev.clientY, null, 10)
  const tape = tapeRef.value
  if (tape) {
    animate(tape, {
      scale: [1, 0.94, 1.04, 1],
      duration: 380,
      ease: 'outCubic',
    })
  }
  emit('confirm')
}

watch(
  () => props.confirming,
  (v, prev) => {
    // 保存完成：咔哒锁定
    if (prev && !v && !dirty.value && tapeRef.value) {
      animate(tapeRef.value, {
        scale: [1, 1.08, 1],
        duration: 360,
        ease: 'outBack(1.6)',
      })
    }
  }
)

function onDocPointer(e) {
  if (!trayOpen.value) return
  const root = deckRef.value
  if (root && !root.contains(e.target)) trayOpen.value = false
}

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocPointer, true)
})

watch(trayOpen, (open) => {
  if (open) document.addEventListener('pointerdown', onDocPointer, true)
  else document.removeEventListener('pointerdown', onDocPointer, true)
})
</script>

<template>
  <div ref="deckRef" class="cassette-deck" :class="{ 'is-open': trayOpen, 'is-dirty': dirty }" @click.stop>
    <div class="deck-head">
      <span class="deck-label">卡带仓</span>
      <span class="deck-brand">{{ provider || '—' }}</span>
    </div>

    <!-- 仓口 -->
    <div class="deck-slot">
      <div class="slot-lip" />
      <div
        ref="tapeRef"
        class="cassette"
        :class="{ 'is-dirty': dirty }"
        :style="{
          '--c0': currentColors[0],
          '--c1': currentColors[1],
        }"
        @click="toggleTray"
      >
        <div class="cassette-reels" aria-hidden="true">
          <span class="reel" />
          <span class="reel" />
        </div>
        <div class="cassette-label">
          <span class="play-mark">▶</span>
          <span class="cassette-name" :title="displayName">{{ displayName }}</span>
        </div>
        <div class="cassette-window" aria-hidden="true" />
      </div>
    </div>

    <div class="deck-actions">
      <button type="button" class="deck-btn" :disabled="swapping" @click="toggleTray">
        {{ trayOpen ? '收起' : '换带' }}
      </button>
      <button
        type="button"
        class="deck-btn deck-btn--save"
        :class="{ on: dirty }"
        :disabled="!dirty || confirming"
        @click="onConfirm"
      >
        {{ confirming ? '上带中…' : '上带保存' }}
      </button>
    </div>

    <!-- 卡带托盘 -->
    <div v-show="trayOpen" ref="trayRef" class="tape-tray">
      <p class="tray-hint">点选一张卡带插入仓内</p>
      <div class="tray-grid">
        <button
          v-for="opt in options"
          :key="opt.value"
          type="button"
          class="tray-tape"
          :class="{ active: opt.value === modelValue }"
          :style="{
            '--c0': tapeColors(opt.value)[0],
            '--c1': tapeColors(opt.value)[1],
          }"
          @click="pickModel(opt.value)"
        >
          <span class="mini-reels" aria-hidden="true"><i /><i /></span>
          <span class="tray-name">{{ opt.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cassette-deck {
  position: relative;
  padding: 10px 10px 8px;
  border-radius: 14px;
  /* 与便签纸同色系：浅暖米，弱分层，避免灰褐块 */
  background: linear-gradient(180deg, #fffbf3 0%, #f6eedc 100%);
  border: 1.5px dashed rgba(139, 115, 85, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}
.deck-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.deck-label {
  font-size: 11px;
  font-weight: 800;
  color: #5c4a35;
  letter-spacing: 0.04em;
}
.deck-brand {
  font-size: 10px;
  font-weight: 800;
  color: #988b7a;
  text-transform: uppercase;
}

.deck-slot {
  position: relative;
  padding: 8px 6px 6px;
  border-radius: 10px;
  /* 暖木质卡口，替代接近黑的深槽 */
  background: linear-gradient(180deg, #d4c4a8 0%, #c4b090 100%);
  box-shadow:
    inset 0 2px 6px rgba(61, 52, 40, 0.18),
    inset 0 -1px 0 rgba(255, 255, 255, 0.35);
}
.slot-lip {
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 4px;
  border-radius: 0 0 4px 4px;
  background: rgba(90, 72, 48, 0.35);
}

.cassette {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(145deg, var(--c0), var(--c1));
  color: #fff;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.2);
  transform-origin: center top;
  user-select: none;
}
.cassette.is-dirty {
  outline: 2px dashed rgba(247, 205, 103, 0.85);
  outline-offset: 2px;
}
.cassette-reels {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.reel {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fff8, #2a241e 55%);
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  box-shadow: inset 0 0 0 3px rgba(0, 0, 0, 0.25);
}
.cassette-label {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
}
.play-mark {
  font-size: 9px;
  opacity: 0.85;
  flex-shrink: 0;
}
.cassette-name {
  font-size: 12px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.25);
}
.cassette-window {
  width: 18px;
  height: 22px;
  border-radius: 3px;
  flex-shrink: 0;
  background: rgba(255, 251, 245, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.deck-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-top: 8px;
}
.deck-btn {
  height: 28px;
  border-radius: 999px;
  border: 1.5px solid rgba(139, 115, 85, 0.2);
  background: #fffbf5;
  color: #5c4a35;
  font-size: 11px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.deck-btn:hover:not(:disabled) {
  border-color: #19c8b9;
  color: #0d7a70;
}
.deck-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.deck-btn--save {
  opacity: 0.55;
}
.deck-btn--save.on {
  opacity: 1;
  background: #19c8b9;
  border-color: #14b3a5;
  color: #fff;
}
.deck-btn--save.on:hover:not(:disabled) {
  background: #16d4c4;
  color: #fff;
}

.tape-tray {
  margin-top: 8px;
  padding: 8px;
  border-radius: 10px;
  background: #fffbf5;
  border: 1.5px solid rgba(139, 115, 85, 0.16);
  transform-origin: top center;
  max-height: 160px;
  overflow-y: auto;
}
.tray-hint {
  margin: 0 0 6px;
  font-size: 10px;
  font-weight: 700;
  color: #988b7a;
}
.tray-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tray-tape {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  background: linear-gradient(135deg, var(--c0), var(--c1));
  color: #fff;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.12);
}
.tray-tape:hover {
  filter: brightness(1.06);
}
.tray-tape.active {
  outline: 2px solid #4a3a28;
  outline-offset: 1px;
}
.mini-reels {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.mini-reels i {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fff8, #2a241e 55%);
  border: 1px solid rgba(255, 255, 255, 0.4);
}
.tray-name {
  font-size: 11px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
