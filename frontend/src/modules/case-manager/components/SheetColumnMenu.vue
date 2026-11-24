<script setup lang="ts">
import { computed } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"

const props = defineProps<{
  hidden: string[]

  columns: { key: string; label: string }[]
}>()

const emit = defineEmits<{
  "update:hidden": [value: string[]]
}>()

const visibleCount = computed(() => props.columns.length - props.hidden.length)

function toggle(key: string, checked: boolean) {
  const next = new Set(props.hidden)
  if (checked) next.delete(key)
  else next.add(key)
  emit("update:hidden", [...next])
}
</script>

<template>
  <div class="sketch-field sheet-field sheet-field--columns">
    <span class="sketch-field__label">显示列</span>
    <el-popover
      :teleported="false"
      placement="bottom-end"
      trigger="click"
      :width="196"
      popper-class="case-col-pop"
    >
      <template #reference>
        <DoodleBtn tone="paper"> 列 {{ visibleCount }}/{{ columns.length }} </DoodleBtn>
      </template>
      <p class="sheet-col__title">勾选要显示的列</p>
      <el-checkbox
        v-for="column in columns"
        :key="column.key"
        class="sheet-col__item"
        :model-value="!hidden.includes(column.key)"
        @change="toggle(column.key, Boolean($event))"
      >
        {{ column.label }}
      </el-checkbox>
    </el-popover>
  </div>
</template>

<style scoped>
.sheet-field--columns {
  min-width: 116px;
}

.sheet-col__title {
  margin-bottom: var(--app-space-xs);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  letter-spacing: 0.08em;
  color: var(--app-text-secondary);
  text-transform: uppercase;
}

.sheet-col__item {
  display: flex;
  height: 28px;
  margin-right: 0;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
}

:global(.el-popover.case-col-pop) {
  border: 1.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  box-shadow: 4px 4px 0 0 var(--c-case);
  background: var(--app-bg-card);
}
</style>
