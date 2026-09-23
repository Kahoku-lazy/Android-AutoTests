<script setup lang="ts">
import { computed, h, ref, useSlots } from "vue"
import { ElTableColumn } from "element-plus"
import type { TableInstance } from "element-plus"

/** 属性直接透传到 el-table（height / header-cell-style / @row-click 等 EP 原生能力） */
defineOptions({ inheritAttrs: false })

const props = defineProps({
  columns: { type: Array as () => any[], required: true },
  dataSource: { type: Array as () => any[], required: true },
  rowKey: { type: String, default: "id" },
  striped: { type: Boolean, default: false },
  border: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: "暂无数据" },
  /** fixed 时弹性列会吃掉剩余宽度，适合需要铺满容器的列表 */
  tableLayout: { type: String, default: "auto" },
  /** el-table row-class-name，可传函数或字符串 */
  rowClassName: { type: [Function, String], default: undefined },
  /**
   * 表纸皮肤强调色（SketchTable 视觉名，非第二组件）。
   * 传入 CSS 色或 var(--c-*)；有值时外套虚线纸 + 模块色硬阴影，表体不旋转。
   */
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
  /** 表头覆写：列名与单元格插槽同源，如 #header-_select 放全选复选框 */
  [key: `header-${string}`]: () => any
}>()

const slots = useSlots()

/** 暴露底层 el-table 实例：消费方写 tableRef.value?.tableRef?.$el / setCurrentRow(...) */
const tableRef = ref<TableInstance>()
defineExpose({ tableRef })

/** Element Plus 列宽只认 px 数字/字符串，百分比会导致列塌缩挤成一团 */
function normalizeSize(value: any) {
  if (value == null || value === "") return undefined
  if (typeof value === "number" && Number.isFinite(value)) return value
  const raw = String(value).trim()
  if (!raw || raw.endsWith("%")) return undefined
  const num = Number(raw)
  return Number.isFinite(num) ? num : raw
}

/**
 * 递归生成列 VNode：
 * - 带 children 的列成为分组表头（层级不限）
 * - 单元格优先取 #cell-<prop> 插槽，表头可覆写为 #header-<prop>
 * - key 取 col.key / prop / 序号，让「无 prop 的列」（如选择列）也有稳定 key
 */
function buildColumns(cols: any[]): any[] {
  return (cols || []).map((col, index) => {
    const children =
      Array.isArray(col.children) && col.children.length ? buildColumns(col.children) : null
    // 没有 dataIndex/prop 时，key 同时充当插槽名（如 #cell-_select / #header-_select）
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

/** 每次渲染重建列 VNode（避免复用同一 VNode 对象） */
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
