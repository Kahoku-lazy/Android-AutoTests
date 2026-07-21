<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:modelValue"]);

const assertions = ref([...props.modelValue]);

watch(() => props.modelValue, (v) => { assertions.value = [...(v || [])]; }, { deep: true });
watch(assertions, (v) => { emit("update:modelValue", [...v]); }, { deep: true });

const ASSERTION_TYPES = [
  { value: "status", label: "📊 状态码" },
  { value: "json_path", label: "🔍 JSON Path" },
  { value: "header", label: "📋 响应头" },
  { value: "body_contains", label: "📝 响应体包含" },
  { value: "response_time", label: "⏱️ 响应时间" },
  { value: "schema", label: "🏗️ JSON Schema" },
];

function addAssertion() {
  assertions.value.push({ type: "json_path", path: "", operator: "equals", expected: "", description: "" });
}

function removeAssertion(index) {
  assertions.value.splice(index, 1);
}
</script>

<template>
  <div class="assertion-editor">
    <div class="assertion-toolbar">
      <span style="font-size:13px;font-weight:500;">断言规则</span>
      <button type="button" class="btn-text" @click="addAssertion">+ 添加断言</button>
      <span class="hint" v-if="!assertions.length">未定义断言</span>
    </div>

    <div v-for="(a, idx) in assertions" :key="idx" class="assertion-row">
      <select v-model="a.type" class="form-input" style="min-width:140px;">
        <option v-for="at in ASSERTION_TYPES" :key="at.value" :value="at.value">{{ at.label }}</option>
      </select>
      <input v-model="a.path" class="form-input" placeholder="JSON Path / 字段路径" style="flex:1;" />
      <select v-model="a.operator" class="form-input" style="min-width:100px;">
        <option value="equals">等于</option>
        <option value="contains">包含</option>
        <option value="not_contains">不包含</option>
        <option value="exists">存在</option>
        <option value="gt">大于</option>
        <option value="lt">小于</option>
      </select>
      <input v-model="a.expected" class="form-input" placeholder="期望值" style="flex:1;" />
      <input v-model="a.description" class="form-input" placeholder="说明" style="min-width:100px;" />
      <button type="button" class="btn-icon btn-danger" @click="removeAssertion(idx)">✕</button>
    </div>
  </div>
</template>

<style scoped>
.assertion-editor { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.assertion-toolbar { display: flex; align-items: center; gap: 12px; }
.hint { font-size: 13px; color: #999; }
.assertion-row { display: flex; gap: 8px; align-items: center; }
.form-input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.btn-text { padding: 4px 12px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.btn-icon { padding: 2px 6px; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; font-size: 11px; }
.btn-danger { color: #e85f5f; border-color: #fcc; }
</style>
