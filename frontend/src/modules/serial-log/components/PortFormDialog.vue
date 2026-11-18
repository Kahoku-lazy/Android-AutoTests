<script setup lang="ts">
/** PortFormDialog — 新增 / 编辑自定义端口（el-dialog 全局皮肤 + sketch-kit 表单）
 *
 * 组件只渲染与本地表单态：校验走 helpers/port-form，HTTP 编排走 useCustomPorts。
 * 编辑模式端口号禁改；打开时按 editRow 重置表单（清表单）。
 */
import { reactive, ref, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { validatePortForm } from "../helpers/port-form"
import type { PortFormPayload } from "../helpers/port-form"
import type { LogPortRow } from "../api"
import {
  PORTS_BAUD_OPTIONS,
  PORT_FORM_BAUD_CUSTOM,
  PORT_FORM_BAUD_CUSTOM_LABEL,
  PORT_FORM_BAUD_CUSTOM_PLACEHOLDER,
  PORT_FORM_BAUD_LABEL,
  PORT_FORM_CANCEL,
  PORT_FORM_PORT_LABEL,
  PORT_FORM_PORT_PLACEHOLDER,
  PORT_FORM_SAVE,
  PORT_FORM_SAVING,
  PORT_FORM_SKU_LABEL,
  PORT_FORM_SKU_PLACEHOLDER,
  PORT_FORM_SUB_ADD,
  PORT_FORM_SUB_EDIT,
  PORT_FORM_TITLE_ADD,
  PORT_FORM_TITLE_EDIT,
} from "../constants"

const props = defineProps<{
  visible: boolean
  editRow: LogPortRow | null
  existingPorts: number[]
  saving: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  submit: [payload: PortFormPayload]
}>()

const form = reactive({
  portText: "",
  sku: "",
  baudChoice: PORTS_BAUD_OPTIONS[PORTS_BAUD_OPTIONS.length - 1] as number | "custom",
  baudCustomText: "",
})
const localError = ref("")

/** 打开即清表单 / 回填编辑行 */
watch(
  () => props.visible,
  (open) => {
    if (!open) return
    localError.value = ""
    const row = props.editRow
    form.portText = row ? String(row.port) : ""
    form.sku = row?.sku ?? ""
    if (row && !PORTS_BAUD_OPTIONS.includes(row.baud)) {
      form.baudChoice = "custom"
      form.baudCustomText = String(row.baud)
    } else {
      form.baudChoice = row?.baud ?? PORTS_BAUD_OPTIONS[PORTS_BAUD_OPTIONS.length - 1]
      form.baudCustomText = ""
    }
  },
)

function onVisibleChange(value: boolean): void {
  if (!value) emit("close")
}

function onSubmit(): void {
  const check = validatePortForm(form, {
    editMode: props.editRow !== null,
    editPort: props.editRow?.port,
    existingPorts: props.existingPorts,
  })
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
    :title="editRow ? PORT_FORM_TITLE_EDIT : PORT_FORM_TITLE_ADD"
    width="480px"
    :close-on-click-modal="false"
    @update:model-value="onVisibleChange"
  >
    <div class="sketch-kit pf-body">
      <p class="pf-sub">{{ editRow ? PORT_FORM_SUB_EDIT : PORT_FORM_SUB_ADD }}</p>
      <div class="sketch-form">
        <div class="sketch-field">
          <label class="sketch-field__label" for="pf-port">{{ PORT_FORM_PORT_LABEL }}</label>
          <el-input
            id="pf-port"
            v-model="form.portText"
            :disabled="!!editRow"
            :placeholder="PORT_FORM_PORT_PLACEHOLDER"
          />
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="pf-sku">{{ PORT_FORM_SKU_LABEL }}</label>
          <el-input
            id="pf-sku"
            v-model="form.sku"
            maxlength="100"
            :placeholder="PORT_FORM_SKU_PLACEHOLDER"
          />
        </div>
        <div class="sketch-field">
          <label class="sketch-field__label" for="pf-baud">{{ PORT_FORM_BAUD_LABEL }}</label>
          <el-select id="pf-baud" v-model="form.baudChoice">
            <el-option v-for="b in PORTS_BAUD_OPTIONS" :key="b" :label="String(b)" :value="b" />
            <el-option :label="PORT_FORM_BAUD_CUSTOM" value="custom" />
          </el-select>
        </div>
        <div v-if="form.baudChoice === 'custom'" class="sketch-field">
          <label class="sketch-field__label" for="pf-baud-custom">
            {{ PORT_FORM_BAUD_CUSTOM_LABEL }}
          </label>
          <el-input
            id="pf-baud-custom"
            v-model="form.baudCustomText"
            :placeholder="PORT_FORM_BAUD_CUSTOM_PLACEHOLDER"
          />
        </div>
      </div>
      <p class="pf-err" role="alert">{{ localError || error }}</p>
      <div class="sketch-form__actions">
        <DoodleBtn tone="paper" :disabled="saving" @click="emit('close')">
          {{ PORT_FORM_CANCEL }}
        </DoodleBtn>
        <DoodleBtn tone="teal" :disabled="saving" @click="onSubmit">
          {{ saving ? PORT_FORM_SAVING : PORT_FORM_SAVE }}
        </DoodleBtn>
      </div>
    </div>
  </el-dialog>
</template>

<style src="./PortFormDialog.style.css" scoped></style>
