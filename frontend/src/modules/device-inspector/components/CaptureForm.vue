<script setup>
import { useElementStore } from '../store'
import { IconZap } from '@/shared/icons'

const store = useElementStore()
const emit = defineEmits(['capture'])

const METHODS = [
  { value: 'both', label: 'Dump + OCR' },
  { value: 'dump', label: '仅 Dump' },
  { value: 'ocr', label: '仅 OCR' },
]
</script>

<template>
  <div class="cap-form">
    <el-select
      v-model="store.captureSerial"
      placeholder="选择设备"
      size="small"
      class="cap-device"
      data-testid="capture-device-select"
    >
      <el-option
        v-for="d in store.availableDevices"
        :key="d.serial"
        :value="d.serial"
        :label="`${d.model || d.brand || ''} (${d.serial})${d.status === 'BUSY' ? ' · 使用中' : ''}`"
      />
    </el-select>
    <el-radio-group v-model="store.captureMethod" size="small" class="cap-method">
      <el-radio-button v-for="m in METHODS" :key="m.value" :value="m.value">{{ m.label }}</el-radio-button>
    </el-radio-group>
    <button
      class="action-btn action-btn--primary"
      :disabled="store.captLoading || !store.captureSerial"
      @click="emit('capture')"
      data-testid="capture-btn"
    >
      <IconZap :size="14" />{{ store.captLoading ? '获取中...' : '获取' }}
    </button>
  </div>
</template>

<style scoped>
.cap-form { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.cap-device { width: 280px; }
.cap-method { flex-shrink: 0; }
.action-btn {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: var(--app-size-xs); font-weight: 700; padding: 4px 12px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  background: var(--app-bg-card); color: var(--app-ink, #2d2d2d);
  cursor: pointer; font-family: inherit; transition: all 0.12s; white-space: nowrap; flex-shrink: 0;
}
.action-btn:hover:not(:disabled) { background: var(--app-highlight, #FFE066); }
.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.action-btn--primary { background: var(--app-ink, #2d2d2d); color: var(--app-bg-card); }
</style>
