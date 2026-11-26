<script setup lang="ts">
import { computed, h, ref, useSlots } from "vue"
import { ElTableColumn } from "element-plus"
import type { TableInstance } from "element-plus"

defineOptions({ inheritAttrs: false })

const props = defineProps({
  columns: { type: Array as () => any[], required: true },
  dataSource: { type: Array as () => any[], required: true },
  rowKey: { type: String, default: "id" },
  striped: { type: Boolean, default: false },
  border: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: "暂无数据" },

  tableLayout: { type: String, default: "auto" },

  rowClassName: { type: [Function, String], default: undefined },

  accent: { type: String, default: "" },
})

const sheetStyle = computed(() =>
  props.accent ? ({ "--sketch-accent": props.accent } as Record<string, string>) : undefined,
)

defineSlots<{
  empty: () => any
  [key: `cell-${string}`]: (props: {
    record: any
    row: any
    value: any
    column: any
    index: number
  }) => any

  [key: `header-${string}`]: () => any
}>()

const slots = useSlots()

const tableRef = ref<TableInstance>()
defineExpose({ tableRef })

function normalizeSize(value: any) {
  if (value == null || value === "") return undefined
  if (typeof value === "number" && Number.isFinite(value)) return value
  const raw = String(value).trim()
  if (!raw || raw.endsWith("%")) return undefined
  const num = Number(raw)
  return Number.isFinite(num) ? num : raw
}

function buildColumns(cols: any[]): any[] {
  return (cols || []).map((col, index) => {
    const children =
      Array.isArray(col.children) && col.children.length ? buildColumns(col.children) : null

    const prop = col.dataIndex || col.prop || col.key
    const width = normalizeSize(col.width)
    const geometry = {
      key: col.key ?? prop ?? `col-${index}`,
      label: col.label || col.title,
      align: col.align,
      headerAlign: col.headerAlign || col.align,
      fixed: col.fixed,
      width,
      minWidth: normalizeSize(col.minWidth) ?? (width || children ? undefined : 120),
    }
    if (children) return h(ElTableColumn, geometry, () => children)

    const cellSlot = prop ? slots[`cell-${prop}`] : undefined
    const headerSlot = prop ? slots[`header-${prop}`] : undefined
    return h(
      ElTableColumn,
      {
        ...geometry,
        prop,
        sortable: col.sortable,
        showOverflowTooltip: col.showOverflowTooltip ?? true,
      },
      {
        ...(headerSlot ? { header: () => headerSlot() } : {}),
        default: (scope: any) =>
          cellSlot
            ? cellSlot({
                record: scope.row,
                row: scope.row,
                value: scope.row?.[prop],
                column: scope.column,
                index: scope.$index,
              })
            : (scope.row?.[prop] ?? ""),
      },
    )
  })
}

const elColumns = computed(() => buildColumns(props.columns))
</script>

<template>
  <div class="ac-table-wrap" :class="{ 'sketch-sheet': !!accent }" :style="sheetStyle">
    <el-table
      ref="tableRef"
      v-bind="$attrs"
      :data="dataSource"
      :row-key="rowKey"
      :stripe="striped"
      :border="border"
      v-loading="loading"
      class="ac-table"
      style="width: 100%"
      :table-layout="tableLayout as any"
      :empty-text="emptyText"
      :row-class-name="rowClassName as any"
    >
      <component :is="col" v-for="(col, i) in elColumns" :key="i" />
      <template v-if="$slots.empty" #empty>
        <slot name="empty" />
      </template>
    </el-table>
  </div>
</template>
