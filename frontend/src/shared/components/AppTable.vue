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
  props.columns.map(col => ({ ...col, prop: col.dataIndex || col.prop }))
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
    />
    <template v-for="(_, slot) in $slots" :key="slot" #[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
  </el-table>
</template>
