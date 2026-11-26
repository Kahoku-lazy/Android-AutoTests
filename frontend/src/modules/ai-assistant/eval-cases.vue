<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import {
  createEvalCase,
  deleteEvalCase,
  fetchEvalCases,
  updateEvalCase,
  type EvalCase,
  type EvalCaseStep,
} from "./api/assistants"
import { appendCase, caseRows, dropCase, replaceCase } from "./helpers/eval-view"

interface StepDraft {
  action: string
  assertion: string
  page: string
}

const CRUMBS = [
  { label: "平台助手", to: "/ai-assistant" },
  { label: "评测", to: "/ai-assistant/evals" },
  { label: "评测题库" },
]

const COLUMNS = [
  { dataIndex: "title", title: "题目", minWidth: 240 },
  { dataIndex: "stepCount", title: "步数", width: 92 },
  { dataIndex: "actions", title: "操作", width: 196 },
]

const cases = ref<EvalCase[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")

const editorOpen = ref(false)
const editing = ref<EvalCase | null>(null)
const draftTitle = ref("")
const draftSteps = ref<StepDraft[]>([])
const saving = ref(false)
const saveError = ref("")

const rows = computed(() => caseRows(cases.value))
const dialogTitle = computed(() => (editing.value ? "编辑题目" : "新建题目"))

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    cases.value = await fetchEvalCases()
    loaded.value = true
  } catch (cause) {
    error.value = formatApiError(cause as never, "题库加载失败")
  } finally {
    loading.value = false
  }
}

function toDraft(item: EvalCase): StepDraft[] {
  const steps = item.steps.length ? item.steps : [blankStep()]
  return steps.map((step) => ({
    action: step.action,
    assertion: step.assertion,
    page: String((step.anchor || {}).page || ""),
  }))
}

function blankStep(): StepDraft {
  return { action: "", assertion: "", page: "" }
}

function openCreate(): void {
  editing.value = null
  draftTitle.value = ""
  draftSteps.value = [blankStep()]
  saveError.value = ""
  editorOpen.value = true
}

function openEdit(caseId: number): void {
  const item = cases.value.find((row) => row.id === caseId)
  if (!item) return
  editing.value = item
  draftTitle.value = item.title
  draftSteps.value = toDraft(item)
  saveError.value = ""
  editorOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  editing.value = null
  saveError.value = ""
}

function buildSteps(): EvalCaseStep[] {
  return draftSteps.value.map((step) => ({
    action: step.action,
    assertion: step.assertion,
    anchor: { page: step.page },
  }))
}

async function save(): Promise<void> {
  const title = draftTitle.value.trim()
  if (!title || saving.value) return
  saving.value = true
  saveError.value = ""
  try {
    if (editing.value) {
      const next = await updateEvalCase(editing.value.id, { title, steps: buildSteps() })
      cases.value = replaceCase(cases.value, next)
    } else {
      const next = await createEvalCase({ title, steps: buildSteps() })
      cases.value = appendCase(cases.value, next)
    }
    closeEditor()
    ElMessage.success("已保存")
  } catch (cause) {
    saveError.value = formatApiError(cause as never, "保存失败")
    ElMessage.error(saveError.value)
  } finally {
    saving.value = false
  }
}

async function remove(caseId: number): Promise<void> {
  try {
    await deleteEvalCase(caseId)
    cases.value = dropCase(cases.value, caseId)
    if (editing.value?.id === caseId) closeEditor()
    ElMessage.success("已删除")
  } catch (cause) {
    ElMessage.error(formatApiError(cause as never, "删除失败"))
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell eval-bank">
    <WorkbenchHeader title="评测题库" icon="bot" />
    <div class="doc-body">
      <WorkbenchCrumbs :items="CRUMBS" back-to="/ai-assistant/evals" back-label="返回评测" />

      <ErrorState v-if="error" :message="error" @retry="load" />
      <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="4" />

      <section v-else class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            真题集 <span class="doc-tag">共 {{ cases.length }} 条</span>
          </h3>
          <DoodleBtn tone="yellow" @click="openCreate">新建题目</DoodleBtn>
        </div>

        <AppTable
          v-if="rows.length"
          :columns="COLUMNS"
          :data-source="rows"
          row-key="id"
          table-layout="fixed"
          accent="var(--c-case)"
          class="bank-table"
        >
          <template #cell-title="{ record }">
            <strong class="bank-table__title">{{ record.title }}</strong>
          </template>
          <template #cell-actions="{ record }">
            <div class="bank-actions">
              <DoodleBtn tone="paper" @click="openEdit(record.id)">编辑</DoodleBtn>
              <ConfirmButton
                doodle
                :message="`删除「${record.title}」？删除后不能恢复。`"
                title="删除题目"
                confirm-text="删除"
                @confirm="remove(record.id)"
              >
                删除
              </ConfirmButton>
            </div>
          </template>
        </AppTable>

        <EmptyState
          v-else
          icon="🧾"
          text="还没有题目"
          hint="每条题目由一组步骤组成，每步写清动作、断言与停留页面"
        >
          <DoodleBtn tone="yellow" @click="openCreate">新建第一条</DoodleBtn>
        </EmptyState>
      </section>
    </div>

    <el-dialog
      v-model="editorOpen"
      :title="dialogTitle"
      width="min(760px, 92vw)"
      destroy-on-close
      @closed="editing = null"
    >
      <div class="bank-form">
        <label class="bank-form__field">
          <span>题目</span>
          <input
            v-model="draftTitle"
            class="bank-form__input"
            placeholder="例如：H6810 定时功能测试"
          />
        </label>

        <div v-for="(step, index) in draftSteps" :key="index" class="bank-form__step">
          <p class="bank-form__step-title">步骤 {{ index + 1 }}</p>
          <div class="bank-form__grid">
            <label class="bank-form__field">
              <span>动作</span>
              <input v-model="step.action" class="bank-form__input" placeholder="要做什么" />
            </label>
            <label class="bank-form__field">
              <span>断言</span>
              <input v-model="step.assertion" class="bank-form__input" placeholder="怎么算做到" />
            </label>
            <label class="bank-form__field">
              <span>页面锚点</span>
              <input v-model="step.page" class="bank-form__input" placeholder="停在哪个页面" />
            </label>
          </div>
        </div>

        <p v-if="saveError" class="bank-form__error">{{ saveError }}</p>
      </div>

      <template #footer>
        <div class="bank-form__footer">
          <ConfirmButton
            v-if="editing"
            doodle
            :message="`删除「${draftTitle}」？删除后不能恢复。`"
            title="删除题目"
            confirm-text="删除"
            @confirm="remove(editing.id)"
          >
            删除
          </ConfirmButton>
          <span class="bank-form__spacer" />
          <DoodleBtn tone="paper" @click="closeEditor">取消</DoodleBtn>
          <DoodleBtn tone="teal" :disabled="saving || !draftTitle.trim()" @click="save">
            {{ saving ? "保存中…" : "保存" }}
          </DoodleBtn>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.bank-table {
  margin-top: var(--app-space-sm);
}

.bank-table__title {
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.bank-actions {
  display: flex;
  gap: var(--app-space-xs);
}

.bank-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.bank-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-secondary);
}

.bank-form__input {
  min-height: 34px;
  padding: 0 var(--app-space-sm);
  border: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
  border-radius: var(--app-radius-sm);
  background: var(--paper);
  color: var(--app-text-primary);
  font-family: inherit;
  font-size: var(--app-size-sm);
}

.bank-form__input:focus-visible {
  outline: 2px solid var(--c-case);
  outline-offset: 1px;
}

.bank-form__step {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding: var(--app-space-sm);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-sm);
  background: color-mix(in srgb, var(--c-case) 6%, var(--paper));
}

.bank-form__step-title {
  margin: 0;
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.bank-form__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--app-space-sm);
}

.bank-form__error {
  margin: 0;
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-marker-red);
}

.bank-form__footer {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.bank-form__spacer {
  flex: 1;
}

@media (max-width: 768px) {
  .bank-form__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
