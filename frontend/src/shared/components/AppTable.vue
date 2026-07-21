<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: { type: Array, required: true },
  dataSource: { type: Array, required: true },
  rowKey: { type: String, default: 'id' },
  striped: { type: Boolean, default: false },
  border: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  /** fixed 时弹性列会吃掉剩余宽度，适合需要铺满容器的列表 */
  tableLayout: { type: String, default: 'auto' },
})

/** Element Plus 列宽只认 px 数字/字符串，百分比会导致列塌缩挤成一团 */
function normalizeSize(value) {
  if (value == null || value === '') return undefined
  if (typeof value === 'number' && Number.isFinite(value)) return value
  const raw = String(value).trim()
  if (!raw || raw.endsWith('%')) return undefined
  const num = Number(raw)
  return Number.isFinite(num) ? num : raw
}

const elColumns = computed(() =>
  props.columns.map((col) => {
    const prop = col.dataIndex || col.prop
    const width = normalizeSize(col.width)
    const minWidth = normalizeSize(col.minWidth) ?? (width ? undefined : 120)
    return {
      prop,
      label: col.label || col.title,
      width,
      minWidth,
      align: col.align,
      fixed: col.fixed,
      sortable: col.sortable,
      showOverflowTooltip: col.showOverflowTooltip ?? false,
    }
  }),
)
</script>

<template>
  <el-table
    :data="dataSource"
    :row-key="rowKey"
    :stripe="striped"
    :border="border"
    v-loading="loading"
    class="ac-table"
    style="width: 100%"
    :table-layout="tableLayout"
    :empty-text="emptyText"
  >
    <el-table-column
      v-for="col in elColumns"
      :key="col.prop"
      :prop="col.prop"
      :label="col.label"
      :width="col.width"
      :min-width="col.minWidth"
      :align="col.align"
      :fixed="col.fixed"
      :sortable="col.sortable"
      :show-overflow-tooltip="col.showOverflowTooltip"
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
