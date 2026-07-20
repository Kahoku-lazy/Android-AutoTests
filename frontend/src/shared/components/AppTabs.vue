<script setup>
defineProps({
  items: { type: Array, required: true },
  modelValue: { type: String, default: '' },
  leafAnimation: { type: Boolean, default: false },
  shadow: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
</script>
<template>
  <el-tabs
    :model-value="modelValue"
    class="ac-tabs"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-tab-pane
      v-for="item in items"
      :key="item.key"
      :label="item.label"
      :name="item.key"
    >
      <slot :name="item.key" />
    </el-tab-pane>
  </el-tabs>
</template>
