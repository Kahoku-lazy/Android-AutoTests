<script setup lang="ts">
/** 助手线路卡片 — 展示某条线路（控制设备/平台任务）的规划/执行模型配置 */
import type { RouteConfig } from '@/shared/types/ai'

defineProps<{
  label: string
  icon: string
  config?: RouteConfig
  canManage?: boolean
  testing?: boolean
}>()
const emit = defineEmits<{ edit: []; test: [] }>()

function modelName(cfg?: { model_name?: string }): string {
  return cfg?.model_name || '未配置'
}
</script>

<template>
  <article class="route-card">
    <div class="route-head">
      <span class="route-icon">{{ icon }}</span>
      <h4 class="route-title">{{ label }}</h4>
    </div>
    <div class="route-config">
      <div class="cfg-row">
        <span class="cfg-role">规划模型</span>
        <span class="cfg-val">{{ modelName(config?.planner) }}</span>
      </div>
      <div class="cfg-row">
        <span class="cfg-role">执行模型</span>
        <span class="cfg-val">{{ modelName(config?.executor) }}</span>
      </div>
      <div class="cfg-row">
        <span class="cfg-role">校验模型</span>
        <span class="cfg-val">{{ modelName(config?.verifier) }}</span>
      </div>
    </div>
    <div class="route-actions">
      <button type="button" class="route-test" :disabled="testing" @click="emit('test')">
        {{ testing ? '校验中…' : '校验' }}
      </button>
      <button v-if="canManage" type="button" class="route-edit" @click="emit('edit')">配置</button>
    </div>
  </article>
</template>

<style scoped>
.route-card {
  background: var(--ai-sticky-bg, rgb(247, 243, 223));
  border: 1px solid rgba(196, 181, 160, 0.35);
  border-radius: 18px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 2px 6px rgba(61, 52, 40, 0.06);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.route-card:hover { transform: translateY(-2px); }
.route-head { display: flex; align-items: center; gap: 12px; }
.route-icon { font-size: 28px; line-height: 1; }
.route-title { margin: 0; font-size: var(--app-size-lg); font-weight: 800; color: var(--doodle-ink, #2d2d2d); }
.route-config { display: flex; flex-direction: column; gap: 8px; }
.cfg-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; background: rgba(139, 115, 85, 0.06); border-radius: 12px;
}
.cfg-role { font-size: var(--app-size-sm); font-weight: 700; color: var(--ai-ink-muted); }
.cfg-val { font-size: var(--app-size-sm); font-weight: 700; color: var(--ai-ink-soft); }
.route-actions { display: flex; gap: 8px; align-self: flex-end; }
.route-edit {
  height: 32px; padding: 0 20px;
  border: 1.5px solid rgba(139, 115, 85, 0.18);
  border-radius: 999px;
  background: var(--ai-sticky-cream, #fffdf5);
  color: var(--ai-ink-subtle);
  font-size: var(--app-size-sm); font-weight: 800; font-family: inherit;
  cursor: pointer;
}
.route-edit:hover { border-color: var(--app-accent-purple, #b39ef3); color: var(--ai-teal-text); }
.route-test {
  height: 32px; padding: 0 20px;
  border: 1.5px solid var(--app-accent-purple, #b39ef3);
  border-radius: 999px;
  background: var(--ai-sticky-cream, #fffdf5);
  color: var(--ai-teal-text);
  font-size: var(--app-size-sm); font-weight: 800; font-family: inherit;
  cursor: pointer;
}
.route-test:disabled { opacity: 0.6; cursor: not-allowed; }
.route-test:hover:not(:disabled) { background: var(--app-accent-purple, #b39ef3); color: #fff; }
</style>
