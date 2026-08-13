<script setup lang="ts">
import { IconSave } from '@/shared/icons/index'

defineProps<{ isNew?: boolean }>()
const emit = defineEmits<{ save: [] }>()
</script>

<template>
  <div class="step-nav">
    <button class="nav-btn nav-save" @click="emit('save')">
      <IconSave :size="18" />
      <span>{{ isNew ? '保存智能体' : '保存修改' }}</span>
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
.nav-save { background: linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover)); color: var(--app-bg-card); border-color: var(--ai-teal); }
.nav-save:hover { background: linear-gradient(135deg, var(--ai-teal-hover), #0d8a80); transform: translateY(-2px); box-shadow: 0 4px 14px rgba(25,200,185,0.35); }
</style>
