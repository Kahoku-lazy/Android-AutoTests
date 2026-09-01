<script setup lang="ts">
import type { RouteModelConfig } from '@/shared/types/ai'
import ModelConfigField from './ModelConfigField.vue'

defineProps<{ label: string; disabled?: boolean }>()
const planner = defineModel<RouteModelConfig>('planner', { required: true })
const executor = defineModel<RouteModelConfig>('executor', { required: true })
const verifier = defineModel<RouteModelConfig>('verifier', { required: true })
</script>

<template>
  <section class="doc-section step-panel route-config">
    <div class="section-title"><span class="section-num">🚀</span>{{ label }}</div>
    <ModelConfigField v-model="planner" label="规划模型 Planner" :disabled="disabled" />
    <ModelConfigField v-model="executor" label="执行模型 Executor" :disabled="disabled" />
    <ModelConfigField v-model="verifier" label="校验模型 Verifier" :disabled="disabled" />
  </section>
</template>

<style scoped>
.route-config { gap: 18px; }
</style>
