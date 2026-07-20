<script setup>
import { computed } from 'vue'
const props = defineProps({
  columns: { type: Array, required: true },
  dataSource: { type: Array, required: true },
  rowKey: { type: String, default: 'id' },
  striped: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
})
const elColumns = computed(() =>
  props.columns.map(col => {
    const prop = col.dataIndex || col.prop
    return { ...col, prop, label: col.label || col.title }
  })
)
</script>
<template>
  <el-table
    :data="dataSource"
    :row-key="rowKey"
    :stripe="striped"
    v-loading="loading"
    class="ac-table"
    :empty-text="emptyText"
  >
    <el-table-column
      v-for="col in elColumns"
      :key="col.dataIndex || col.prop"
      v-bind="col"
    >
      <template #default="scope">
        <slot
          v-if="$slots[`cell-${col.prop}`]"
          :name="`cell-${col.prop}`"
          :record="scope.row"
          :row="scope.row"
          :value="scope.row?.[col.prop]"
          :column="scope.column"
          :index="scope.$index"
        />
        <span v-else>{{ scope.row?.[col.prop] ?? '' }}</span>
      </template>
    </el-table-column>
    <template v-if="$slots.empty" #empty>
      <slot name="empty" />
    </template>
  </el-table>
</template>
