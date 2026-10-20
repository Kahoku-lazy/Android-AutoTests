<script setup lang="ts">
import { computed, nextTick, ref } from "vue"
import { useRoute } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import CaseStepDrawer from "./components/CaseStepDrawer.vue"
import SheetTagPicker from "./components/SheetTagPicker.vue"
import { useCaseSheet } from "./composables/useCaseSheet"
import {
  BUSINESS_TYPE_OPTIONS,
  CASE_TYPE_OPTIONS,
  PRIORITY_OPTIONS,
  SYSTEM_OPTIONS,
} from "./types"
import type { CaseStep, SheetRowDraft } from "./types"

type TextField = "title" | "module" | "precondition"
type ToneKind = "priority" | "system" | "case_type" | "business_type"

const route = useRoute()

const projectId = computed(() => Number(route.params.projectId))
const fileId = computed(() => Number(route.params.fileId))

const {
  fileMeta,
  rows,
  loading,
  saving,
  error,
  dirtyCount,
  loadSheet,
  markDirty,
  applySteps,
  addRow,
  saveAll,
  removeRow,
  renameSheet,
} = useCaseSheet(
  () => projectId.value,
  () => fileId.value,
)

const pageTitle = computed(() => fileMeta.value?.name || "用例表格")
const renaming = ref(false)
const renameDraft = ref("")

/** `${rowId}:${field}` */
const editingKey = ref<string | null>(null)
const editDraft = ref("")

const stepDrawerOpen = ref(false)
const stepDrawerRow = ref<SheetRowDraft | null>(null)

const TONES: Record<ToneKind, Record<string, string>> = {
  priority: { P0: "pri-p0", P1: "pri-p1", P2: "pri-p2" },
  system: { ANDROID: "sys-android", WEB: "sys-web", IOS: "sys-ios", API: "sys-api" },
  case_type: { FUNC: "ct-func", AUTO: "ct-auto" },
  business_type: {
    appliance: "biz-appliance",
    lighting: "biz-lighting",
    app: "biz-app",
  },
}

function toneOf(kind: ToneKind) {
  return (value: string) => TONES[kind][value] || "pri-p2"
}

function cellKey(rowId: string, field: TextField): string {
  return `${rowId}:${field}`
}

function isEditing(rowId: string, field: TextField): boolean {
  return editingKey.value === cellKey(rowId, field)
}

function displayText(value: string): string {
  return (value || "").trim()
}

function stepsTooltip(row: SheetRowDraft): string {
  if (!row.steps.length) return "还没有步骤"
  return row.steps
    .slice(0, 3)
    .map((step, index) => `${index + 1}. ${step.action || "（空动作）"}`)
    .join("\n")
}

function startRename() {
  renameDraft.value = fileMeta.value?.name || ""
  renaming.value = true
}

async function confirmRename() {
  const name = renameDraft.value.trim()
  if (!name) return
  const ok = await renameSheet(name)
  if (ok) renaming.value = false
}

function pickTag(row: SheetRowDraft, kind: ToneKind, value: string) {
  if (kind === "priority") row.priority = value as SheetRowDraft["priority"]
  else if (kind === "system") row.system = value as SheetRowDraft["system"]
  else if (kind === "case_type") row.case_type = value as SheetRowDraft["case_type"]
  else row.business_type = value as SheetRowDraft["business_type"]
  markDirty(row)
}

async function beginEdit(row: SheetRowDraft, field: TextField) {
  editingKey.value = cellKey(row.id, field)
  editDraft.value = row[field] || ""
  await nextTick()
  const el = document.querySelector<HTMLTextAreaElement | HTMLInputElement>(
    `[data-edit-key="${editingKey.value}"]`,
  )
  el?.focus()
  el?.select()
}

function commitEdit(row: SheetRowDraft, field: TextField) {
  if (editingKey.value !== cellKey(row.id, field)) return
  const next = editDraft.value
  if (row[field] !== next) {
    row[field] = next
    markDirty(row)
  }
  editingKey.value = null
  editDraft.value = ""
}

function cancelEdit() {
  editingKey.value = null
  editDraft.value = ""
}

function onEditKeydown(e: KeyboardEvent, row: SheetRowDraft, field: TextField, multiline: boolean) {
  if (e.key === "Escape") {
    e.preventDefault()
    cancelEdit()
    return
  }
  if (e.key === "Enter" && !multiline && !e.shiftKey) {
    e.preventDefault()
    commitEdit(row, field)
  }
}

function openSteps(row: SheetRowDraft) {
  stepDrawerRow.value = row
  stepDrawerOpen.value = true
}

function onStepsApply(steps: CaseStep[]) {
  if (stepDrawerRow.value) applySteps(stepDrawerRow.value, steps)
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell case-workbench case-sheet">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="双击文本单元格编辑；枚举标签可点击切换；步骤在右侧面板编辑"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    >
      <template #actions>
        <el-button class="wb-btn" @click="startRename">重命名</el-button>
        <el-button class="wb-btn" :loading="saving" type="primary" @click="saveAll">
          保存{{ dirtyCount ? ` (${dirtyCount})` : "" }}
        </el-button>
        <el-button class="wb-btn" type="success" @click="addRow">+ 新建行</el-button>
      </template>
    </WorkbenchHeader>

    <div class="doc-body" v-loading="loading">
      <WorkbenchCrumbs
        :back-to="`/cases/projects/${projectId}`"
        back-label="返回目录"
        :items="[
          { label: '用例管理', to: '/cases' },
          { label: '项目工作台', to: `/cases/projects/${projectId}` },
          { label: pageTitle },
        ]"
      />
      <ErrorState v-if="error && !rows.length && !loading" :message="error" @retry="loadSheet" />
      <EmptyState
        v-else-if="!loading && !rows.length"
        icon="📊"
        text="暂无用例行"
        hint="点击「新建行」开始填写；步骤在「N 步」面板里编辑"
      />

      <div v-else class="case-sheet__table-wrap">
        <table class="case-sheet__table">
          <thead>
            <tr>
              <th class="col-id">用例 ID</th>
              <th class="col-pri">优先级</th>
              <th class="col-sys">系统</th>
              <th class="col-kind">类型</th>
              <th class="col-biz">业务类型</th>
              <th class="col-title">标题</th>
              <th class="col-module">模块</th>
              <th class="col-pre">前置</th>
              <th class="col-steps">步骤</th>
              <th class="col-time">时间</th>
              <th class="col-ops">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" :class="{ 'is-dirty': row.dirty }">
              <td class="col-id">
                <div class="sheet-cell sheet-cell--muted">
                  {{ row.isNew ? "（新建）" : row.id }}
                </div>
              </td>

              <td class="col-pri">
                <SheetTagPicker
                  :options="PRIORITY_OPTIONS"
                  :value="row.priority"
                  :tone-of="toneOf('priority')"
                  @pick="pickTag(row, 'priority', $event)"
                />
              </td>

              <td class="col-sys">
                <SheetTagPicker
                  :options="SYSTEM_OPTIONS"
                  :value="row.system"
                  :tone-of="toneOf('system')"
                  @pick="pickTag(row, 'system', $event)"
                />
              </td>

              <td class="col-kind">
                <SheetTagPicker
                  :options="CASE_TYPE_OPTIONS"
                  :value="row.case_type"
                  :tone-of="toneOf('case_type')"
                  @pick="pickTag(row, 'case_type', $event)"
                />
              </td>

              <td class="col-biz">
                <SheetTagPicker
                  :options="BUSINESS_TYPE_OPTIONS"
                  :value="row.business_type"
                  :tone-of="toneOf('business_type')"
                  @pick="pickTag(row, 'business_type', $event)"
                />
              </td>

              <td class="col-title" @dblclick="beginEdit(row, 'title')">
                <div v-if="isEditing(row.id, 'title')" class="sheet-cell sheet-cell--editing">
                  <input
                    :data-edit-key="cellKey(row.id, 'title')"
                    v-model="editDraft"
                    class="sheet-editor"
                    @blur="commitEdit(row, 'title')"
                    @keydown="onEditKeydown($event, row, 'title', false)"
                  />
                </div>
                <div
                  v-else
                  class="sheet-cell sheet-cell--editable"
                  :class="{ 'is-empty': !displayText(row.title) }"
                >
                  {{ displayText(row.title) || "双击填写" }}
                </div>
              </td>

              <td class="col-module" @dblclick="beginEdit(row, 'module')">
                <div v-if="isEditing(row.id, 'module')" class="sheet-cell sheet-cell--editing">
                  <input
                    :data-edit-key="cellKey(row.id, 'module')"
                    v-model="editDraft"
                    class="sheet-editor"
                    @blur="commitEdit(row, 'module')"
                    @keydown="onEditKeydown($event, row, 'module', false)"
                  />
                </div>
                <div
                  v-else
                  class="sheet-cell sheet-cell--editable"
                  :class="{ 'is-empty': !displayText(row.module) }"
                >
                  {{ displayText(row.module) || "双击填写" }}
                </div>
              </td>

              <td class="col-pre" @dblclick="beginEdit(row, 'precondition')">
                <div v-if="isEditing(row.id, 'precondition')" class="sheet-cell sheet-cell--editing">
                  <textarea
                    :data-edit-key="cellKey(row.id, 'precondition')"
                    v-model="editDraft"
                    class="sheet-editor sheet-editor--area"
                    rows="3"
                    @blur="commitEdit(row, 'precondition')"
                    @keydown="onEditKeydown($event, row, 'precondition', true)"
                  />
                </div>
                <div
                  v-else
                  class="sheet-cell sheet-cell--editable sheet-cell--pre"
                  :class="{ 'is-empty': !displayText(row.precondition) }"
                >
                  {{ displayText(row.precondition) || "双击填写" }}
                </div>
              </td>

              <td class="col-steps">
                <button
                  type="button"
                  class="steps-trigger"
                  :class="{ 'is-empty': !row.steps.length }"
                  :title="stepsTooltip(row)"
                  @click="openSteps(row)"
                >
                  {{ row.steps.length }} 步
                </button>
              </td>

              <td class="col-time">
                <div class="sheet-cell sheet-cell--muted sheet-cell--center">
                  {{ row.updated_at || "—" }}
                </div>
              </td>

              <td class="col-ops">
                <button type="button" class="sheet-del-btn" @click="removeRow(row)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <CaseStepDrawer
      v-model="stepDrawerOpen"
      :title="stepDrawerRow?.title || ''"
      :steps="stepDrawerRow?.steps || []"
      @apply="onStepsApply"
    />

    <el-dialog v-model="renaming" title="重命名文件" width="400px" :close-on-click-modal="false">
      <el-input v-model="renameDraft" maxlength="200" @keyup.enter="confirmRename" />
      <template #footer>
        <el-button @click="renaming = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style src="./CaseFileSheet.style.css" scoped></style>
