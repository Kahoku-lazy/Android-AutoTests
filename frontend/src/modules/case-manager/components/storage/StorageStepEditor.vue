<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:modelValue"]);

const operations = ref([...props.modelValue]);

watch(() => props.modelValue, (v) => { operations.value = [...(v || [])]; }, { deep: true });
watch(operations, (v) => { emit("update:modelValue", [...v]); }, { deep: true });

const OPERATION_TYPES = [
  { value: "insert", label: "📥 插入数据" },
  { value: "update", label: "✏️ 更新数据" },
  { value: "delete", label: "🗑️ 删除数据" },
  { value: "verify", label: "✅ 验证数据" },
  { value: "transform", label: "🔄 转换数据" },
  { value: "aggregate", label: "📊 聚合查询" },
  { value: "query", label: "🔍 查询数据" },
];

function addOperation() {
  operations.value.push({ type: "verify", target: "", params: {}, description: "" });
}

function removeOperation(index) {
  operations.value.splice(index, 1);
}

function moveUp(index) {
  if (index > 0) {
    const tmp = operations.value[index];
    operations.value[index] = operations.value[index - 1];
    operations.value[index - 1] = tmp;
  }
}

function moveDown(index) {
  if (index < operations.value.length - 1) {
    const tmp = operations.value[index];
    operations.value[index] = operations.value[index + 1];
    operations.value[index + 1] = tmp;
  }
}
</script>

<template>
  <div class="step-editor">
    <div class="step-toolbar">
      <button type="button" class="btn-text" @click="addOperation">+ 添加操作</button>
      <span class="step-hint" v-if="!operations.length">暂无操作，请添加数据操作步骤</span>
    </div>

    <div v-for="(op, idx) in operations" :key="idx" class="step-item">
      <div class="step-header">
        <span class="step-number">{{ idx + 1 }}</span>
        <select v-model="op.type" class="step-select">
          <option v-for="ot in OPERATION_TYPES" :key="ot.value" :value="ot.value">{{ ot.label }}</option>
        </select>
        <button type="button" class="btn-icon" title="上移" @click="moveUp(idx)">▲</button>
        <button type="button" class="btn-icon" title="下移" @click="moveDown(idx)">▼</button>
        <button type="button" class="btn-icon btn-danger" title="删除" @click="removeOperation(idx)">✕</button>
      </div>
      <div class="step-body">
        <div class="step-fields">
          <div class="field">
            <label>目标（表名/字段/键）</label>
            <input v-model="op.target" class="form-input" placeholder="如：users / order.total" />
          </div>
          <div class="field">
            <label>参数 (JSON)</label>
            <textarea v-model="op.params" class="form-input font-mono" rows="3" placeholder='{"field": "value"}' />
          </div>
          <div class="field">
            <label>描述</label>
            <input v-model="op.description" class="form-input" placeholder="此操作的目的说明" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-editor { display: flex; flex-direction: column; gap: 8px; }
.step-toolbar { display: flex; align-items: center; gap: 12px; }
.step-hint { font-size: 13px; color: #999; }
.step-item { border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden; }
.step-header { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f8f8f8; }
.step-number { width: 24px; height: 24px; border-radius: 50%; background: var(--animal-primary-color, #6fba2c); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
.step-select { padding: 4px 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.step-body { padding: 12px; }
.step-fields { display: flex; flex-direction: column; gap: 8px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 12px; color: #888; }
.form-input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.font-mono { font-family: monospace; font-size: 12px; }
.btn-text { padding: 4px 12px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.btn-icon { padding: 2px 6px; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; font-size: 11px; }
.btn-danger { color: #e85f5f; border-color: #fcc; }
</style>
