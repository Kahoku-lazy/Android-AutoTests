<template>
  <div class="step-list-panel">
    <div class="panel-header">
      <h3>📋 测试步骤</h3>
      <span class="panel-badge">{{ modelValue.length }} 步</span>
      <el-button size="small" type="primary" text :disabled="readonly" @click="addStep">+ 添加步骤</el-button>
    </div>
    <div class="panel-body">
      <el-empty v-if="!modelValue.length" description="暂无步骤，点击上方按钮添加" :image-size="60" />
      <ApiStepCard
        v-for="(step, i) in modelValue"
        :key="i"
        :model-value="step"
        :index="i"
        :upstream-vars="getUpstreamVars(i)"
        :readonly="readonly"
        @update:model-value="updateStep(i, $event)"
        @remove="removeStep(i)"
        @duplicate="duplicateStep(i)"
        @move-up="moveStep(i, -1)"
        @move-down="moveStep(i, 1)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import type { ApiStep } from '../../types/api-config'
import { defaultApiStep } from '../../types/api-config'
import ApiStepCard from './ApiStepCard.vue'

const props = defineProps<{
  modelValue: ApiStep[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ApiStep[]]
}>()

function updateStep(index: number, step: ApiStep) {
  const copy = [...props.modelValue]
  copy[index] = step
  emit('update:modelValue', copy)
}

function addStep() {
  emit('update:modelValue', [...props.modelValue, defaultApiStep()])
}

async function removeStep(index: number) {
  try {
    await ElMessageBox.confirm('确定删除此步骤？', '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  const copy = [...props.modelValue]
  copy.splice(index, 1)
  emit('update:modelValue', copy)
}

function duplicateStep(index: number) {
  const copy = [...props.modelValue]
  copy.splice(index + 1, 0, JSON.parse(JSON.stringify(copy[index])))
  emit('update:modelValue', copy)
}

function moveStep(index: number, delta: number) {
  const newIndex = index + delta
  if (newIndex < 0 || newIndex >= props.modelValue.length) return
  const copy = [...props.modelValue]
  const [item] = copy.splice(index, 1)
  copy.splice(newIndex, 0, item)
  emit('update:modelValue', copy)
}

function getUpstreamVars(stepIndex: number) {
  const vars: { stepIndex: number; stepName: string; name: string; path: string }[] = []
  for (let i = 0; i < stepIndex && i < props.modelValue.length; i++) {
    const s = props.modelValue[i]
    for (const ex of s.extract || []) {
      if (ex.name) {
        vars.push({ stepIndex: i, stepName: s.name || `步骤${i + 1}`, name: ex.name, path: ex.path })
      }
    }
  }
  return vars
}
</script>

<style scoped>
.step-list-panel {
  background: var(--c-bg-card, #fff);
  border-radius: 8px;
  border: 1px solid var(--c-border, #e4e7ed);
}
.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-border, #e4e7ed);
  background: var(--c-bg-subtle, #fafafa);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.panel-header h3 { margin: 0; font-size: var(--app-size-sm); font-weight: 600; }
.panel-badge { font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600; margin-left: auto; }
.panel-body { padding: 12px 16px; }
</style>
