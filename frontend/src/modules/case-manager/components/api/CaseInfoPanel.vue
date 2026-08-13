<template>
  <div class="case-info-panel">
    <div class="panel-header">
      <h3>📋 用例信息</h3>
    </div>
    <div class="panel-body">
      <div class="form-row">
        <label class="form-label">用例 ID</label>
        <div class="id-display">
          <code>{{ modelValue.id || '保存后自动生成' }}</code>
          <el-button v-if="modelValue.id" size="small" text @click="copyId">
            复制
          </el-button>
        </div>
      </div>
      <div class="form-row">
        <label class="form-label required">测试标题</label>
        <el-input
          :model-value="modelValue.title"
          placeholder="输入测试标题（必填）"
          maxlength="500"
          show-word-limit
          @update:model-value="$emit('update:modelValue', { ...modelValue, title: $event })"
        />
      </div>
      <div class="form-row">
        <label class="form-label">测试点描述</label>
        <el-input
          :model-value="modelValue.description"
          type="textarea"
          :rows="2"
          placeholder="描述测试目的和覆盖场景"
          @update:model-value="$emit('update:modelValue', { ...modelValue, description: $event })"
        />
      </div>
      <div class="form-row">
        <label class="form-label">前置条件</label>
        <el-input
          :model-value="modelValue.precondition"
          type="textarea"
          :rows="2"
          placeholder="如：1. 测试用户 admin 已注册&#10;2. 密码为 admin123"
          @update:model-value="$emit('update:modelValue', { ...modelValue, precondition: $event })"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CaseInfo } from '../../types/api-config'
import { ElMessage } from 'element-plus'

const props = defineProps<{ modelValue: CaseInfo }>()
const emit = defineEmits<{ 'update:modelValue': [value: CaseInfo] }>()

function copyId() {
  if (props.modelValue.id) {
    navigator.clipboard.writeText(props.modelValue.id)
    ElMessage.success('已复制')
  }
}
</script>

<style scoped>
.case-info-panel {
  background: var(--c-bg-card, #fff);
  border-radius: 8px;
  border: 1px solid var(--c-border, #e4e7ed);
}
.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-border, #e4e7ed);
  background: var(--c-bg-subtle, #fafafa);
}
.panel-header h3 {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 600;
}
.panel-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-label {
  font-size: var(--app-size-sm);
  font-weight: 500;
  color: var(--c-text-secondary, #606266);
}
.form-label.required::after {
  content: ' *';
  color: var(--app-error);
}
.id-display {
  display: flex;
  align-items: center;
  gap: 8px;
}
.id-display code {
  padding: 2px 8px;
  background: var(--c-bg-subtle, #f5f7fa);
  border-radius: 4px;
  font-size: var(--app-size-xs);
  color: var(--c-text-secondary, #909399);
}
</style>
