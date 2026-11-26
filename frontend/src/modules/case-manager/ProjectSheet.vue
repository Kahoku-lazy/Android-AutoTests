<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue"
import { useRoute } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import { formatApiError } from "@/shared/api-client"
import SheetToolbar from "./components/SheetToolbar.vue"
import SheetTable from "./components/SheetTable.vue"
import SheetRowDrawer from "./components/SheetRowDrawer.vue"
import { applySheetView, editablePayload, isGroupHeader } from "./helpers/sheet"
import type { SheetDisplayRow } from "./helpers/sheet"
import {
  createRow,
  deleteRow,
  getProjectSheet,
  importProjectYaml,
  saveSheetView,
  updateRow,
} from "./api"
import {
  DEFAULT_SHEET_VIEW,
  GROUP_OPTIONS,
  SHEET_COLUMNS,
  type CaseRow,
  type ProjectSheet,
  type SheetView,
} from "./types"

const route = useRoute()
const projectId = computed(() => Number(route.params.projectId))

const loading = ref(false)
const saving = ref(false)
const error = ref("")
const sheet = ref<ProjectSheet | null>(null)
const draftTitle = ref("")
const drawerOpen = ref(false)
const editingRow = ref<CaseRow | null>(null)

const dirtyIds = reactive(new Set<string>())

const view = computed<SheetView>(() => sheet.value?.view ?? DEFAULT_SHEET_VIEW)
const rows = computed<CaseRow[]>(() => sheet.value?.rows ?? [])
const displayRows = computed<SheetDisplayRow[]>(() => applySheetView(rows.value, view.value))
const groupCount = computed(() => displayRows.value.filter(isGroupHeader).length)
const dirtyCount = computed(() => dirtyIds.size)
const projectName = computed(() => sheet.value?.project.name || "项目用例表")
const caseLimit = computed(() => sheet.value?.project.case_limit || 999)
const groupLabel = computed(
  () => GROUP_OPTIONS.find((option) => option.key === view.value.group_by)?.label || "",
)

const crumbs = computed(() => [
  { label: "用例管理", to: "/cases" },
  { label: sheet.value?.project.name || "项目" },
])

const columns = computed(() => [
  ...SHEET_COLUMNS.filter((column) => !view.value.hidden_columns.includes(column.key)).map(
    (column) => ({
      dataIndex: column.key,
      label: column.label,
      minWidth: column.key === "title" ? 220 : column.key === "id" ? 150 : 96,
    }),
  ),
  { key: "actions", label: "", width: 92, align: "right" },
])

async function load() {
  loading.value = true
  error.value = ""
  try {
    const { data } = await getProjectSheet(projectId.value)
    if (!data.status || !data.data) throw data
    sheet.value = data.data
    dirtyIds.clear()
  } catch (e: unknown) {
    error.value = formatApiError(e, "用例表加载失败")
  } finally {
    loading.value = false
  }
}

async function persistView(next: SheetView) {
  if (!sheet.value) return
  const previous = view.value
  sheet.value = { ...sheet.value, view: next }
  try {
    const { data } = await saveSheetView(projectId.value, next)
    if (!data.status) throw data
  } catch (e: unknown) {
    sheet.value = { ...sheet.value, view: previous }
    ElMessage.error(formatApiError(e, "视图保存失败"))
  }
}

function setGroupBy(value: string) {
  void persistView({ ...view.value, group_by: value })
}

function setFilter(field: string, value: string) {
  void persistView({ ...view.value, filters: { ...view.value.filters, [field]: value } })
}

function setHidden(hidden: string[]) {
  void persistView({ ...view.value, hidden_columns: hidden })
}

async function onCreate() {
  const title = draftTitle.value.trim()
  if (!title) {
    ElMessage.warning("请先输入用例标题")
    return
  }
  try {
    const { data } = await createRow(projectId.value, {
      title,
      steps: [{ action: "待补充动作", assertion: "待补充断言" }],
    })
    if (!data.status) throw data
    draftTitle.value = ""
    await load()
    ElMessage.success("已新增一行")
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, "新增失败"))
  }
}

async function onImport(file: File) {
  try {
    const { data } = await importProjectYaml(projectId.value, file)
    if (!data.status) throw data
    ElMessage.success(`已追加 ${data.data?.imported || 0} 条`)
    await load()
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, "导入失败"))
  }
}

function openRow(row: SheetDisplayRow | CaseRow) {
  if (isGroupHeader(row as SheetDisplayRow)) return
  editingRow.value = row as CaseRow
  drawerOpen.value = true
}

function onApply(next: CaseRow) {
  if (!sheet.value) return
  sheet.value = {
    ...sheet.value,
    rows: sheet.value.rows.map((row) => (row.id === next.id ? next : row)),
  }
  dirtyIds.add(next.id)
  drawerOpen.value = false
  editingRow.value = null
}

async function onRemove(row: CaseRow) {
  try {
    await ElMessageBox.confirm(
      `删除用例「${row.title}」后不可恢复，其步骤会一并删除。`,
      "确认删除用例",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    )
  } catch {
    return
  }
  try {
    const { data } = await deleteRow(projectId.value, row.id)
    if (!data.status) throw data
    dirtyIds.delete(row.id)
    drawerOpen.value = false
    editingRow.value = null
    await load()
    ElMessage.success("已删除")
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, "删除失败"))
  }
}

async function saveAll() {
  if (!dirtyIds.size || saving.value) return
  saving.value = true
  const pending = rows.value.filter((row) => dirtyIds.has(row.id))
  let done = 0
  try {
    for (const row of pending) {
      const { data } = await updateRow(projectId.value, row.id, editablePayload(row))
      if (!data.status) throw data
      dirtyIds.delete(row.id)
      done += 1
    }
    ElMessage.success(`已保存 ${done} 行`)
    await load()
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, `保存失败（已完成 ${done} 行）`))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell case-workbench case-sheet-page">
    <WorkbenchHeader
      :title="projectName"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    />
    <div class="doc-body">
      <WorkbenchCrumbs back-to="/cases" back-label="返回项目列表" :items="crumbs" />

      <SkeletonCard v-if="loading" variant="list" :lines="6" />
      <ErrorState v-else-if="error" :message="error" @retry="load" />
      <template v-else>
        <SheetToolbar
          :group-by="view.group_by"
          :priority="view.filters.priority || ''"
          :business-type="view.filters.business_type || ''"
          :hidden="view.hidden_columns"
          :draft-title="draftTitle"
          :case-count="sheet?.project.case_count || 0"
          :case-limit="caseLimit"
          :dirty-count="dirtyCount"
          :saving="saving"
          @update:group-by="setGroupBy"
          @update:priority="setFilter('priority', $event)"
          @update:business-type="setFilter('business_type', $event)"
          @update:hidden="setHidden"
          @update:draft-title="draftTitle = $event"
          @create="onCreate"
          @import="onImport"
          @save="saveAll"
        />

        <EmptyState
          v-if="!rows.length"
          icon="📋"
          text="这张表还没有用例"
          hint="在控制区输入标题回车建一行，或导入 YAML"
        />
        <EmptyState
          v-else-if="!displayRows.length"
          icon="🔍"
          text="没有符合筛选条件的用例"
          hint="清掉筛选或换一种分组再看"
        />
        <template v-else>
          <SheetTable
            :rows="displayRows"
            :columns="columns"
            :dirty-ids="dirtyIds"
            @open="openRow"
          />
          <p v-if="groupCount" class="case-sheet-note">
            按「{{ groupLabel }}」分成 {{ groupCount }} 组；组头行不参与编辑。
          </p>
        </template>
      </template>
    </div>

    <SheetRowDrawer v-model="drawerOpen" :row="editingRow" @apply="onApply" @remove="onRemove" />
  </div>
</template>

<style src="./ProjectSheet.style.css" scoped></style>
