<script setup lang="ts">
/**
 * 用例表纸：把展示行渲染成一张纸。
 *
 * 只负责「怎么画」——列定义、组头合并、未保存行配色、各列读态插槽；
 * 数据流（加载 / 视图 / 草稿 / 保存）留在页面壳里。
 */
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import SheetGroupCell from "./SheetGroupCell.vue"
import CaseChip from "./CaseChip.vue"
import { businessLabel, isGroupHeader, priorityTone, stepSummary } from "../helpers/sheet"
import type { SheetDisplayRow } from "../helpers/sheet"
import { formatDateTime, formatRelativeTime } from "@/shared/helpers/datetime"
import type { CaseRow } from "../types"

const props = defineProps<{
  rows: SheetDisplayRow[]
  /** AppTable 的列定义（已按隐藏列过滤） */
  columns: Record<string, unknown>[]
  /** 已应用未写库的用例编号 */
  dirtyIds: Set<string>
}>()

const emit = defineEmits<{
  open: [row: CaseRow]
}>()

/** 组头行：首列跨满整个可见宽度，其余列折叠 */
function spanMethod({ row, columnIndex }: { row: SheetDisplayRow; columnIndex: number }) {
  if (!isGroupHeader(row)) return undefined
  return (columnIndex === 0 ? [1, props.columns.length] : [0, 0]) as [number, number]
}

function rowClassName({ row }: { row: SheetDisplayRow }) {
  if (isGroupHeader(row)) return "is-case-group"
  return props.dirtyIds.has(row.id) ? "is-case-dirty" : ""
}
</script>

<template>
  <AppTable
    :columns="columns"
    :data-source="rows"
    row-key="id"
    accent="var(--c-case)"
    :span-method="spanMethod"
    :row-class-name="rowClassName"
    @row-click="emit('open', $event)"
  >
    <!-- 每个单元格的第一行都是组头守卫：无论哪一列被隐藏，组头都落在「第一个可见列」上 -->
    <template #cell-id="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <code v-else class="case-id" :title="row.id">{{ row.id }}</code>
    </template>
    <template #cell-priority="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <CaseChip v-else :tone="priorityTone(row.priority)" :text="row.priority" />
    </template>
    <template #cell-system="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <CaseChip
        v-else
        tone="system"
        :text="row.system"
        :hint="row.system === 'IOS' ? 'IOS 暂不支持执行' : ''"
      />
    </template>
    <template #cell-business_type="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <CaseChip v-else tone="business" :text="businessLabel(row.business_type)" />
    </template>
    <template #cell-module="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <span v-else class="case-text">{{ row.module || "—" }}</span>
    </template>
    <template #cell-title="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <span v-else class="case-title" :title="row.title">{{ row.title }}</span>
    </template>
    <template #cell-steps="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <CaseChip v-else tone="steps" :text="stepSummary(row.steps?.length ?? row.step_count)" />
    </template>
    <template #cell-updated_at="{ row }">
      <SheetGroupCell v-if="isGroupHeader(row)" :name="row.__group" :count="row.__count" />
      <span v-else class="case-time" :title="formatDateTime(row.updated_at)">
        {{ formatRelativeTime(row.updated_at) }}
      </span>
    </template>
    <template #cell-actions="{ row }">
      <DoodleBtn tone="paper" @click.stop="emit('open', row)">编辑</DoodleBtn>
    </template>
  </AppTable>
</template>

<style scoped>
/* 读态文案：表纸与三档字号由 workbench-theme 提供，这里只定「这一格怎么排」 */
.case-id {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-secondary);
  white-space: nowrap;
}

.case-title {
  display: block;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}

.case-text {
  font-size: var(--app-size-sm);
  color: var(--app-text-primary);
}

.case-time {
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  white-space: nowrap;
}
</style>
