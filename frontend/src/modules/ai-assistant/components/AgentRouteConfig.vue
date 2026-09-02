<script setup lang="ts">
import { watch } from 'vue'
import type { RouteConfig } from '@/shared/types/ai'
import ModelConfigField from './ModelConfigField.vue'

defineProps<{ label: string; disabled?: boolean }>()
const config = defineModel<RouteConfig>({ required: true })

watch(config, (c) => {
  if (!c) return
  if (!c.planner) c.planner = {}
  if (!c.executor) c.executor = {}
  if (!c.verifier) c.verifier = {}
}, { immediate: true, deep: true })
</script>

<template>
  <section class="doc-section step-panel route-config">
    <div class="section-title"><span class="section-num">🚀</span>{{ label }}</div>
    <ModelConfigField v-model="config.planner" label="规划模型 Planner" :disabled="disabled" />
    <ModelConfigField v-model="config.executor" label="执行模型 Executor" :disabled="disabled" />
    <ModelConfigField v-model="config.verifier" label="校验模型 Verifier" :disabled="disabled" />
  </section>
</template>

<style scoped>
.route-config { gap: 18px; }
</style>
