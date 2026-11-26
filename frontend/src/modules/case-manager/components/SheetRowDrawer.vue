<script setup lang="ts">
import { ref, watch } from "vue"
import { ElMessage } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import { cloneRow, hasAnchor, hasLog, validateDraft } from "../helpers/sheet"
import { BUSINESS_OPTIONS, PRIORITY_OPTIONS, SYSTEM_OPTIONS } from "../types"
import type { CaseRow, CaseStep } from "../types"

const props = defineProps<{
  modelValue: boolean

  row: CaseRow | null
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "apply": [row: CaseRow]
  "remove": [row: CaseRow]
}>()

const draft = ref<CaseRow | null>(null)

watch(
  () => [props.modelValue, props.row] as const,
  () => {
    try {
      draft.value = props.modelValue && props.row ? cloneRow(props.row) : null
    } catch (e: unknown) {
      draft.value = null
      ElMessage.error(`打开编辑面板失败：${e instanceof Error ? e.message : String(e)}`)
    }
  },
  { immediate: true },
)

function close() {
  emit("update:modelValue", false)
}

function addStep() {
  draft.value?.steps.push({ action: "", assertion: "" })
}

function removeStep(index: number) {
  draft.value?.steps.splice(index, 1)
}

function moveStep(index: number, delta: number) {
  const steps = draft.value?.steps
  if (!steps) return
  const target = index + delta
  if (target < 0 || target >= steps.length) return
  const [moved] = steps.splice(index, 1)
  steps.splice(target, 0, moved)
}

function stepIndexOf(step: CaseStep): number {
  return (draft.value?.steps || []).indexOf(step) + 1
}

function applyChanges() {
  if (!draft.value) return
  const issue = validateDraft(draft.value)
  if (issue) {
    ElMessage.warning(issue.message)
    return
  }
  emit("apply", cloneRow(draft.value))
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="'编辑用例 ' + (row?.id || '')"
    size="min(520px, 92vw)"
    class="case-row-drawer"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="draft" class="sheet-drawer sketch-kit">
      <p class="sheet-drawer__hint">
        改动先落在草稿里；点「应用改动」后该行标记为未保存，由页面的「保存」统一写库。
      </p>

      <div class="sheet-drawer__grid">
        <div class="sketch-field">
          <span class="sketch-field__label">优先级</span>
          <el-select v-model="draft.priority" class="sheet-drawer__control">
            <el-option
              v-for="option in PRIORITY_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
        <div class="sketch-field">
          <span class="sketch-field__label">系统</span>
          <el-select v-model="draft.system" class="sheet-drawer__control">
            <el-option
              v-for="option in SYSTEM_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
        <div class="sketch-field">
          <span class="sketch-field__label">业务类型</span>
          <el-select v-model="draft.business_type" class="sheet-drawer__control">
            <el-option
              v-for="option in BUSINESS_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
        <div class="sketch-field">
          <span class="sketch-field__label">模块</span>
          <el-input v-model="draft.module" class="sheet-drawer__control" maxlength="120" />
        </div>
      </div>

      <div class="sketch-field">
        <span class="sketch-field__label">标题</span>
        <el-input v-model="draft.title" class="sheet-drawer__control" maxlength="200" />
      </div>

      <div class="sketch-field">
        <span class="sketch-field__label">前置条件</span>
        <el-input
          v-model="draft.precondition"
          class="sheet-drawer__control"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 3 }"
          maxlength="2000"
          placeholder="可选，例如：设备已配网且在线"
        />
      </div>

      <div class="sheet-drawer__steps-head">
        <span class="sketch-field__label">步骤序列（{{ draft.steps.length }} 步）</span>
        <DoodleBtn tone="paper" @click="addStep">新增一步</DoodleBtn>
      </div>

      <EmptyState
        v-if="!draft.steps.length"
        icon="🧩"
        text="这条用例还没有步骤"
        hint="点「新增一步」开始写动作与断言"
      />

      <div v-for="(step, index) in draft.steps" :key="index" class="sheet-step">
        <div class="sheet-step__head">
          <span class="sheet-step__no">{{ String(index + 1).padStart(2, "0") }}</span>
          <div class="sheet-step__ops">
            <DoodleBtn
              tone="paper"
              :disabled="index === 0"
              :aria-label="`上移第 ${index + 1} 步`"
              @click="moveStep(index, -1)"
            >
              ↑
            </DoodleBtn>
            <DoodleBtn
              tone="paper"
              :disabled="index === draft.steps.length - 1"
              :aria-label="`下移第 ${index + 1} 步`"
              @click="moveStep(index, 1)"
            >
              ↓
            </DoodleBtn>
            <DoodleBtn
              tone="danger"
              :aria-label="`删除第 ${index + 1} 步`"
              @click="removeStep(index)"
            >
              ✕
            </DoodleBtn>
          </div>
        </div>
        <el-input
          v-model="step.action"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          maxlength="2000"
          :placeholder="`第 ${stepIndexOf(step)} 步的动作`"
        />
        <el-input
          v-model="step.assertion"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          maxlength="2000"
          :placeholder="`第 ${stepIndexOf(step)} 步的断言`"
        />
        <p v-if="hasAnchor(step) || hasLog(step)" class="sheet-step__hint">
          该步带执行提示（{{ hasAnchor(step) ? "页面锚点" : ""
          }}{{ hasAnchor(step) && hasLog(step) ? " + " : ""
          }}{{ hasLog(step) ? "日志证据" : "" }}），本轮只编辑动作与断言，提示原样保留。
        </p>
      </div>
    </div>

    <template #footer>
      <div class="sheet-drawer__foot">
        <DoodleBtn tone="danger" @click="row && emit('remove', row)">删除用例</DoodleBtn>
        <span class="sheet-drawer__spacer" />
        <DoodleBtn tone="paper" @click="close">取消</DoodleBtn>
        <DoodleBtn tone="teal" @click="applyChanges">应用改动</DoodleBtn>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.sheet-drawer {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.sheet-drawer__hint {
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-secondary);
}

.sheet-drawer__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--app-space-sm) var(--app-space-md);
}

.sheet-drawer__control {
  width: 100%;
}

.sheet-drawer__steps-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-xs);
}

.sheet-step {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  padding: var(--app-space-sm);
  border: 1.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-subtle);
}

.sheet-step__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.sheet-step__no {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-secondary);
}

.sheet-step__ops {
  display: flex;
  gap: var(--app-space-xs);
}

.sheet-step__ops :deep(.doodle-btn) {
  min-height: 26px;
  padding: 0 var(--app-space-sm);
}

.sheet-step__hint {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.sheet-drawer__foot {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.sheet-drawer__spacer {
  flex: 1 1 auto;
}
</style>
