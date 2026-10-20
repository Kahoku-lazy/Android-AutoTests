<script setup lang="ts">
/**
 * CaseStepDrawer — 用例步骤序列编辑器（抽屉）。
 *
 * 只改草稿：新增 / 删除 / 上下移动都落在本地副本，点「应用到用例」才回传父级，
 * 由父级标记该行为未保存，随页面「保存」统一提交——抽屉内不发任何写请求。
 */
import { ref, watch } from "vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import type { CaseStep } from "../types"

const props = defineProps<{
  modelValue: boolean
  title: string
  steps: CaseStep[]
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "apply": [steps: CaseStep[]]
}>()

const draft = ref<CaseStep[]>([])

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    draft.value = (props.steps || []).map((step) => ({
      action: step.action,
      assertion: step.assertion,
    }))
  },
)

function close() {
  emit("update:modelValue", false)
}

function addStep() {
  draft.value.push({ action: "", assertion: "" })
}

function removeStep(index: number) {
  draft.value.splice(index, 1)
}

function moveStep(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= draft.value.length) return
  const [moved] = draft.value.splice(index, 1)
  draft.value.splice(target, 0, moved)
}

function apply() {
  emit(
    "apply",
    draft.value.map((step) => ({ action: step.action, assertion: step.assertion })),
  )
  close()
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="`步骤编辑 · ${title || '未命名用例'}`"
    size="760px"
    @update:model-value="emit('update:modelValue', $event as boolean)"
  >
    <div class="step-drawer">
      <p class="step-drawer__hint">
        序号即执行顺序；动作与断言都必填。这里的修改先落在草稿，点「应用到用例」后随页面「保存」一起提交。
      </p>

      <EmptyState
        v-if="!draft.length"
        icon="📝"
        text="这条用例还没有步骤"
        hint="点下方「添加步骤」，或先取消再去别处补写"
      />

      <ol v-else class="step-drawer__list">
        <li v-for="(step, index) in draft" :key="index" class="step-drawer__item">
          <div class="step-drawer__head">
            <span class="step-drawer__index">第 {{ index + 1 }} 步</span>
            <span class="step-drawer__ops">
              <button
                type="button"
                class="step-drawer__op"
                :disabled="index === 0"
                @click="moveStep(index, -1)"
              >
                上移
              </button>
              <button
                type="button"
                class="step-drawer__op"
                :disabled="index === draft.length - 1"
                @click="moveStep(index, 1)"
              >
                下移
              </button>
              <button type="button" class="step-drawer__op is-danger" @click="removeStep(index)">
                删除
              </button>
            </span>
          </div>
          <label class="step-drawer__label">
            动作
            <textarea
              v-model="step.action"
              class="step-drawer__input"
              rows="2"
              maxlength="2000"
              placeholder="例如：点击 H6810 开关按键"
            />
          </label>
          <label class="step-drawer__label">
            断言
            <textarea
              v-model="step.assertion"
              class="step-drawer__input"
              rows="2"
              maxlength="2000"
              placeholder="例如：设备日志出现开灯事件"
            />
          </label>
        </li>
      </ol>

      <el-button class="step-drawer__add" @click="addStep">+ 添加步骤</el-button>
    </div>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="apply">应用到用例</el-button>
    </template>
  </el-drawer>
</template>

<style src="./CaseStepDrawer.style.css" scoped></style>
