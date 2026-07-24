<script setup>
import { IconArrowLeft, IconSave } from '@/shared/icons/index.js'

defineProps({
  isNew: { type: Boolean, default: false },
  step: { type: Number, default: 1 },
})

const emit = defineEmits(['save'])
</script>

<template>
  <div v-if="isNew" class="step-nav">
    <button v-if="step > 1" class="nav-btn nav-prev" @click="$emit('prev-step')">
      <IconArrowLeft :size="18" />
      <span>上一步</span>
    </button>
    <button v-if="step < 5" class="nav-btn nav-next" @click="$emit('next-step')">
      <span>下一步</span>
      <IconArrowLeft :size="18" style="transform: rotate(180deg)" />
    </button>
    <button v-if="step === 5" class="nav-btn nav-save" @click="emit('save')">
      <IconSave :size="18" />
      <span>保存智能体</span>
    </button>
  </div>
  <div v-else class="step-nav">
    <button class="nav-btn nav-save" @click="emit('save')">
      <IconSave :size="18" />
      <span>保存修改</span>
    </button>
  </div>
</template>

<style scoped>
.step-nav { display: flex; justify-content: center; gap: 16px; padding: 20px 0; }
.nav-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px;
  border: 2px solid var(--ink); border-radius: 12px; font-size: var(--app-size-md); font-weight: 700;
  font-family: inherit; cursor: pointer; transition: all 0.2s ease;
}
.nav-prev { background: #fff; color: var(--ink); }
.nav-prev:hover { background: #f0ebe0; transform: translateX(-2px); }
.nav-next { background: #19c8b9; color: #fff; border-color: #19c8b9; }
.nav-next:hover { background: #15a89c; transform: translateX(2px); }
.nav-save { background: linear-gradient(135deg, #19c8b9, #15a89c); color: #fff; border-color: #19c8b9; }
.nav-save:hover { background: linear-gradient(135deg, #15a89c, #0d8a80); transform: translateY(-2px); box-shadow: 0 4px 14px rgba(25,200,185,0.35); }
</style>
