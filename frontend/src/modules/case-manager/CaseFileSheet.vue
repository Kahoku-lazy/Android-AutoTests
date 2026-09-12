<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { useCaseSheet } from './composables/useCaseSheet'
import { BUSINESS_TYPE_OPTIONS, TEST_TYPE_OPTIONS } from './types'
import type { BusinessType, SheetRowDraft, TestType } from './types'

type TextField = 'title' | 'module' | 'precondition' | 'steps' | 'expected_result'
type TagKind = 'test_type' | 'business_type'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.projectId))
const fileId = computed(() => Number(route.params.fileId))

const {
  fileMeta,
  rows,
  loading,
  saving,
  error,
  dirtyCount,
  skipGuard,
  loadSheet,
  markDirty,
  addRow,
  saveAll,
  removeRow,
  renameSheet,
} = useCaseSheet(() => projectId.value, () => fileId.value)

const pageTitle = computed(() => fileMeta.value?.name || '用例表格')
const renaming = ref(false)
const renameDraft = ref('')

/** `${rowId}:${field}` */
const editingKey = ref<string | null>(null)
const editDraft = ref('')
const openTagKey = ref<string | null>(null)

const TEST_TAG_CLASS: Record<TestType, string> = {
  app: 'sheet-tag--app',
  web: 'sheet-tag--web',
  api: 'sheet-tag--api',
  func: 'sheet-tag--func',
}

const BIZ_TAG_CLASS: Record<BusinessType, string> = {
  appliance: 'sheet-tag--appliance',
  lighting: 'sheet-tag--lighting',
  app: 'sheet-tag--biz-app',
}

function labelOf(kind: TagKind, value: string): string {
  const opts = kind === 'test_type' ? TEST_TYPE_OPTIONS : BUSINESS_TYPE_OPTIONS
  return opts.find((o) => o.value === value)?.label || value
}

function tagClass(kind: TagKind, value: string): string {
  if (kind === 'test_type') return TEST_TAG_CLASS[value as TestType] || 'sheet-tag--app'
  return BIZ_TAG_CLASS[value as BusinessType] || 'sheet-tag--appliance'
}

function cellKey(rowId: string, field: TextField | TagKind): string {
  return `${rowId}:${field}`
}

function isEditing(rowId: string, field: TextField): boolean {
  return editingKey.value === cellKey(rowId, field)
}

function displayText(value: string): string {
  return (value || '').trim()
}

function startRename() {
  renameDraft.value = fileMeta.value?.name || ''
  renaming.value = true
}

async function confirmRename() {
  const name = renameDraft.value.trim()
  if (!name) return
  const ok = await renameSheet(name)
  if (ok) renaming.value = false
}

function toggleTagMenu(rowId: string, kind: TagKind) {
  const key = cellKey(rowId, kind)
  openTagKey.value = openTagKey.value === key ? null : key
}

function pickTag(row: SheetRowDraft, kind: TagKind, value: string) {
  if (kind === 'test_type') row.test_type = value as TestType
  else row.business_type = value as BusinessType
  markDirty(row)
  openTagKey.value = null
}

async function beginEdit(row: SheetRowDraft, field: TextField) {
  openTagKey.value = null
  editingKey.value = cellKey(row.id, field)
  editDraft.value = row[field] || ''
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
  editDraft.value = ''
}

function cancelEdit() {
  editingKey.value = null
  editDraft.value = ''
}

function onEditKeydown(e: KeyboardEvent, row: SheetRowDraft, field: TextField, multiline: boolean) {
  if (e.key === 'Escape') {
    e.preventDefault()
    cancelEdit()
    return
  }
  if (e.key === 'Enter' && !multiline && !e.shiftKey) {
    e.preventDefault()
    commitEdit(row, field)
  }
}

function onDocClick(e: MouseEvent) {
  const t = e.target as HTMLElement | null
  if (!t?.closest('.sheet-tag-wrap')) openTagKey.value = null
}

async function goBack() {
  skipGuard.value = true
  await router.push(`/cases/projects/${projectId.value}`)
}

onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div class="case-sheet">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="双击单元格编辑；类型标签可点击切换"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),#6ee7d8)'"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goBack">← 返回目录</el-button>
        <el-button class="wb-btn" @click="startRename">重命名</el-button>
        <el-button class="wb-btn" :loading="saving" type="primary" @click="saveAll">
          保存{{ dirtyCount ? ` (${dirtyCount})` : '' }}
        </el-button>
        <el-button class="wb-btn" type="success" @click="addRow">+ 新建行</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="error && !rows.length && !loading" :message="error" @retry="loadSheet" />

    <div v-else class="case-sheet__body" v-loading="loading">
      <EmptyState
        v-if="!loading && !rows.length"
        icon="📊"
        text="暂无用例行"
        hint="点击「新建行」开始填写；文本列双击编辑"
      />

      <div v-else class="case-sheet__table-wrap">
        <table class="case-sheet__table">
          <thead>
            <tr>
              <th class="col-id">用例 ID</th>
              <th class="col-type">测试类型</th>
              <th class="col-biz">业务类型</th>
              <th class="col-time">时间</th>
              <th class="col-title">标题</th>
              <th class="col-module">模块</th>
              <th class="col-pre">前置</th>
              <th class="col-steps">步骤</th>
              <th class="col-expect">预期结果</th>
              <th class="col-ops">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" :class="{ 'is-dirty': row.dirty }">
              <td class="col-id">
                <div class="sheet-cell sheet-cell--muted">
                  {{ row.isNew ? '（新建）' : row.id }}
                </div>
              </td>

              <td class="col-type">
                <div class="sheet-tag-wrap" @click.stop>
                  <button
                    type="button"
                    class="sheet-tag"
                    :class="tagClass('test_type', row.test_type)"
                    @click="toggleTagMenu(row.id, 'test_type')"
                  >
                    {{ labelOf('test_type', row.test_type) }}
                    <span class="sheet-tag__caret">▾</span>
                  </button>
                  <div
                    v-if="openTagKey === cellKey(row.id, 'test_type')"
                    class="sheet-tag-menu"
                  >
                    <button
                      v-for="opt in TEST_TYPE_OPTIONS"
                      :key="opt.value"
                      type="button"
                      class="sheet-tag-menu__item"
                      @click="pickTag(row, 'test_type', opt.value)"
                    >
                      <span class="sheet-tag sheet-tag--sm" :class="tagClass('test_type', opt.value)">
                        {{ opt.label }}
                      </span>
                    </button>
                  </div>
                </div>
              </td>

              <td class="col-biz">
                <div class="sheet-tag-wrap" @click.stop>
                  <button
                    type="button"
                    class="sheet-tag"
                    :class="tagClass('business_type', row.business_type)"
                    @click="toggleTagMenu(row.id, 'business_type')"
                  >
                    {{ labelOf('business_type', row.business_type) }}
                    <span class="sheet-tag__caret">▾</span>
                  </button>
                  <div
                    v-if="openTagKey === cellKey(row.id, 'business_type')"
                    class="sheet-tag-menu"
                  >
                    <button
                      v-for="opt in BUSINESS_TYPE_OPTIONS"
                      :key="opt.value"
                      type="button"
                      class="sheet-tag-menu__item"
                      @click="pickTag(row, 'business_type', opt.value)"
                    >
                      <span
                        class="sheet-tag sheet-tag--sm"
                        :class="tagClass('business_type', opt.value)"
                      >
                        {{ opt.label }}
                      </span>
                    </button>
                  </div>
                </div>
              </td>

              <td class="col-time">
                <div class="sheet-cell sheet-cell--muted sheet-cell--center">
                  {{ row.updated_at || '—' }}
                </div>
              </td>

              <td
                class="col-title"
                @dblclick="beginEdit(row, 'title')"
              >
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
                  {{ displayText(row.title) || '双击填写' }}
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
                  {{ displayText(row.module) || '双击填写' }}
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
                  {{ displayText(row.precondition) || '双击填写' }}
                </div>
              </td>

              <td class="col-steps" @dblclick="beginEdit(row, 'steps')">
                <div v-if="isEditing(row.id, 'steps')" class="sheet-cell sheet-cell--editing">
                  <textarea
                    :data-edit-key="cellKey(row.id, 'steps')"
                    v-model="editDraft"
                    class="sheet-editor sheet-editor--area"
                    rows="4"
                    @blur="commitEdit(row, 'steps')"
                    @keydown="onEditKeydown($event, row, 'steps', true)"
                  />
                </div>
                <div
                  v-else
                  class="sheet-cell sheet-cell--editable sheet-cell--pre"
                  :class="{ 'is-empty': !displayText(row.steps) }"
                >
                  {{ displayText(row.steps) || '双击填写' }}
                </div>
              </td>

              <td class="col-expect" @dblclick="beginEdit(row, 'expected_result')">
                <div
                  v-if="isEditing(row.id, 'expected_result')"
                  class="sheet-cell sheet-cell--editing"
                >
                  <textarea
                    :data-edit-key="cellKey(row.id, 'expected_result')"
                    v-model="editDraft"
                    class="sheet-editor sheet-editor--area"
                    rows="4"
                    @blur="commitEdit(row, 'expected_result')"
                    @keydown="onEditKeydown($event, row, 'expected_result', true)"
                  />
                </div>
                <div
                  v-else
                  class="sheet-cell sheet-cell--editable sheet-cell--pre"
                  :class="{ 'is-empty': !displayText(row.expected_result) }"
                >
                  {{ displayText(row.expected_result) || '双击填写' }}
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

    <el-dialog v-model="renaming" title="重命名文件" width="400px" :close-on-click-modal="false">
      <el-input v-model="renameDraft" maxlength="200" @keyup.enter="confirmRename" />
      <template #footer>
        <el-button @click="renaming = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.case-sheet {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.case-sheet__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  border-top: 2px solid var(--case-border-subtle);
  background: var(--paper);
  padding: 12px;
}
.case-sheet__table-wrap {
  overflow: auto;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--paper);
  padding: var(--app-space-sm);
}
.case-sheet__table {
  width: 100%;
  min-width: 1280px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: var(--app-size-sm);
  background: #fff;
}
.case-sheet__table th,
.case-sheet__table td {
  border: 1.5px solid #cfc9bb;
  padding: 0;
  vertical-align: middle;
}
.case-sheet__table th {
  background: #d6ebff;
  color: #1a4a73;
  font-weight: 700;
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: center;
  padding: 10px var(--app-space-sm);
  border-color: #9ec9f0;
}
.case-sheet__table tr.is-dirty td {
  background: color-mix(in srgb, var(--c-case) 10%, white);
}
.col-id { width: 150px; }
.col-type { width: 110px; }
.col-biz { width: 110px; }
.col-time { width: 150px; }
.col-title { width: 160px; }
.col-module { width: 120px; }
.col-pre { width: 180px; }
.col-steps { width: 220px; }
.col-expect { width: 220px; }
.col-ops {
  width: 88px;
  text-align: center;
}

.sheet-cell {
  min-height: 44px;
  padding: var(--app-space-sm) 10px;
  line-height: 1.4;
  word-break: break-word;
}
.sheet-cell--muted {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}
.sheet-cell--center {
  text-align: center;
}
.sheet-cell--pre {
  white-space: pre-wrap;
}
.sheet-cell--editable {
  cursor: text;
}
.sheet-cell--editable:hover {
  outline: 2px dashed color-mix(in srgb, var(--c-case) 55%, transparent);
  outline-offset: -2px;
}
.sheet-cell--editable.is-empty {
  color: #c0bbb0;
}
.sheet-cell--editing {
  padding: var(--app-space-xs);
  outline: 2px solid var(--c-case);
  outline-offset: -2px;
  background: #fff;
}
.sheet-editor {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  color: var(--ink);
  padding: 6px;
  min-height: 32px;
}
.sheet-editor--area {
  resize: vertical;
  min-height: 64px;
  line-height: 1.45;
}

.sheet-tag-wrap {
  position: relative;
  display: inline-flex;
  padding: var(--app-space-sm) 10px;
}
.sheet-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-xs);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: var(--app-space-xs) 10px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  cursor: pointer;
  font-family: inherit;
  background: #e6faf8;
  color: #1a7a74;
}
.sheet-tag--sm {
  cursor: default;
  border-width: 1.5px;
  padding: 2px var(--app-space-sm);
  font-size: var(--app-size-xs);
}
.sheet-tag__caret {
  font-size: var(--app-size-xs);
  opacity: 0.75;
}
.sheet-tag--app { background: #e6faf8; color: #1a7a74; }
.sheet-tag--web { background: #e8f6fc; color: #2a6f96; }
.sheet-tag--api { background: #f1ebff; color: #5b4aa8; }
.sheet-tag--func { background: #fff8db; color: #8a6a00; }
.sheet-tag--appliance { background: #e9f8ec; color: #2f7a3d; }
.sheet-tag--lighting { background: #fff0ec; color: #b35a48; }
.sheet-tag--biz-app { background: #fce8ff; color: #9a3aad; }

.sheet-tag-menu {
  position: absolute;
  top: calc(100% - 4px);
  left: 10px;
  z-index: 20;
  min-width: 128px;
  background: #fff;
  border: 2px solid var(--ink);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 4px 4px 0 rgba(30, 30, 36, 0.15);
}
.sheet-tag-menu__item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 6px var(--app-space-sm);
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
}
.sheet-tag-menu__item:hover {
  background: var(--paper);
}

.sheet-del-btn {
  margin: 6px auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 30px;
  padding: 0 12px;
  border-radius: 12px;
  border: 2px solid var(--ink);
  background: #fff;
  color: #e85d5d;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 2px 2px 0 var(--ink);
}
.sheet-del-btn:hover {
  background: #ffe8e8;
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 var(--ink);
}
</style>
