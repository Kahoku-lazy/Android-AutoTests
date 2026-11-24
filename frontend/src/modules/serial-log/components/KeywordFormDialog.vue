<script setup lang="ts">
import { reactive, ref, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { validateKeywordForm } from "../helpers/keyword-form"
import type { KeywordFormPayload } from "../helpers/keyword-form"
import { SCOPE_GENERAL } from "../helpers/log-keyword-rows"
import type { LogKeywordRow } from "../helpers/log-keyword-rows"
import {
  KEYWORD_FORM_CANCEL,
  KEYWORD_FORM_FEATURE_ID_LABEL,
  KEYWORD_FORM_FEATURE_ID_PLACEHOLDER,
  KEYWORD_FORM_FEATURE_LABEL,
  KEYWORD_FORM_FEATURE_PLACEHOLDER,
  KEYWORD_FORM_KEYWORD_LABEL,
  KEYWORD_FORM_KEYWORD_PLACEHOLDER,
  KEYWORD_FORM_MODULE_LABEL,
  KEYWORD_FORM_MODULE_PLACEHOLDER,
  KEYWORD_FORM_SAVE,
  KEYWORD_FORM_SAVING,
  KEYWORD_FORM_SCOPE_LABEL,
  KEYWORD_FORM_SUB_ADD,
  KEYWORD_FORM_SUB_EDIT,
  KEYWORD_FORM_TITLE_ADD,
  KEYWORD_FORM_TITLE_EDIT,
} from "../constants"

const props = defineProps<{
  visible: boolean
  editRow: LogKeywordRow | null
  scopeOptions: { value: string; label: string }[]
  saving: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  submit: [payload: KeywordFormPayload]
}>()

const form = reactive({
  keyword: "",
  module: "",
  feature: "",
  scope: SCOPE_GENERAL as string,
  featureIdText: "",
})
const localError = ref("")

watch(
  () => props.visible,
  (open) => {
    if (!open) return
    localError.value = ""
    const row = props.editRow
    form.keyword = row?.keyword ?? ""
    form.module = row?.module ?? ""
    form.feature = row?.featureName ?? ""
    form.scope = row?.scope ?? SCOPE_GENERAL
    form.featureIdText = row?.featureId !== undefined ? String(row.featureId) : ""
  },
)

function onVisibleChange(value: boolean): void {
  if (!value) emit("close")
}

function onSubmit(): void {
  const check = validateKeywordForm(form)
  if (check.kind === "error") {
    localError.value = check.error
    return
  }
  localError.value = ""
  emit("submit", check.payload)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="editRow ? KEYWORD_FORM_TITLE_EDIT : KEYWORD_FORM_TITLE_ADD"
    width="480px"
    :close-on-click-modal="false"
    @update:model-value="onVisibleChange"
  >
    <div class="sketch-kit kf-body">
      <p class="kf-sub">{{ editRow ? KEYWORD_FORM_SUB_EDIT : KEYWORD_FORM_SUB_ADD }}</p>
      <div class="sketch-form">
        <div class="sketch-field">
          <label class="sketch-field__label" for="kf-keyword">{{
            KEYWORD_FORM_KEYWORD_LABEL
          }}</label>
          <el-input
            id="kf-keyword"
            v-model="form.keyword"
            maxlength="200"
            :placeholder="KEYWORD_FORM_KEYWORD_PLACEHOLDER"
          />
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="kf-module">{{ KEYWORD_FORM_MODULE_LABEL }}</label>
          <el-input
            id="kf-module"
            v-model="form.module"
            maxlength="100"
            :placeholder="KEYWORD_FORM_MODULE_PLACEHOLDER"
          />
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="kf-feature">{{
            KEYWORD_FORM_FEATURE_LABEL
          }}</label>
          <el-input
            id="kf-feature"
            v-model="form.feature"
            maxlength="200"
            :placeholder="KEYWORD_FORM_FEATURE_PLACEHOLDER"
          />
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="kf-scope">{{ KEYWORD_FORM_SCOPE_LABEL }}</label>
          <el-select
            id="kf-scope"
            v-model="form.scope"
            filterable
            allow-create
            default-first-option
            :teleported="false"
          >
            <el-option
              v-for="option in scopeOptions"
              :key="option.value"
              :value="option.value"
              :label="option.label"
            />
          </el-select>
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="kf-feature-id">
            {{ KEYWORD_FORM_FEATURE_ID_LABEL }}
          </label>
          <el-input
            id="kf-feature-id"
            v-model="form.featureIdText"
            :placeholder="KEYWORD_FORM_FEATURE_ID_PLACEHOLDER"
          />
        </div>
      </div>
      <p class="kf-err" role="alert">{{ localError || error }}</p>
      <div class="sketch-form__actions">
        <DoodleBtn tone="paper" :disabled="saving" @click="emit('close')">
          {{ KEYWORD_FORM_CANCEL }}
        </DoodleBtn>
        <DoodleBtn tone="teal" :disabled="saving" @click="onSubmit">
          {{ saving ? KEYWORD_FORM_SAVING : KEYWORD_FORM_SAVE }}
        </DoodleBtn>
      </div>
    </div>
  </el-dialog>
</template>

<style src="./KeywordFormDialog.style.css" scoped></style>
