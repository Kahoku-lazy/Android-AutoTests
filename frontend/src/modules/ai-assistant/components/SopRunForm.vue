<script setup lang="ts">
/**
 * 工作流任务表单：左列基本信息（用例来源 / 设备 / 已选摘要），右列用例输入（平台用例选择器或里程碑 YAML）。
 *
 * 平台用例可多选、跨项目保留；缺项时「开始运行」置灰，原因写在 footer 左侧。
 * 设备从设备管理里选（USB 提交序列号、局域网提交 IP:端口），不手填。
 * 工作流由卡片带入，这里不再选一次；弹窗外壳与宽度由 `SopWorkflowSection.vue` 提供。
 */
import { computed, onMounted, ref } from "vue"
import CasePicker from "./CasePicker.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { formatApiError } from "@/shared/api-client"
import { listDevices } from "@/shared/api/devices"
import { deviceAddress, deviceLabel, isSelectableDevice } from "@/shared/helpers/device-address"
import { listAutomationProjects, runSopWorkflow } from "../api/assistants"
import { summarizePicked, type CaseProjectGroup } from "../helpers/case-picker"
import { sopRunError } from "../helpers/sop-form"
import type { SopWorkflow } from "../types"
import type { DeviceRecord } from "@/shared/types/device"

const props = defineProps<{ workflow: SopWorkflow }>()
const emit = defineEmits<{ close: []; submitted: [taskId: number] }>()

const source = ref<"yaml" | "platform">("platform")
const material = ref<File | null>(null)
const yaml = ref<File | null>(null)
const selectedCaseIds = ref<string[]>([])
const projects = ref<CaseProjectGroup[]>([])
const casesLoading = ref(false)
const casesError = ref("")
const serial = ref("")
const running = ref(false)
const error = ref("")
const devices = ref<DeviceRecord[]>([])
const devicesLoading = ref(false)
const devicesError = ref("")

/** 下拉只列能连的设备：无线调试别名那些记录先剔掉。 */
const deviceOptions = computed(() =>
  devices.value
    .filter(isSelectableDevice)
    .map((device) => ({ value: deviceAddress(device), label: deviceLabel(device) })),
)

/** 左栏摘要卡：条数、覆盖的项目数与所选用例名。 */
const picked = computed(() => summarizePicked(selectedCaseIds.value, projects.value))

/** 缺项原因与提交按钮同源：`sop-form.ts` 是唯一判据。 */
const kind = computed(() => props.workflow.kind || "ui_automation")
const blockReason = computed(() => {
  if (kind.value !== "ui_automation" && !material.value) return "先上传文档"
  return (
    sopRunError(
      {
        workflowId: props.workflow.id,
        source: source.value,
        yamlName: yaml.value?.name || "",
        caseCount: selectedCaseIds.value.length,
        serial: serial.value,
      },
      kind.value,
    ) || ""
  )
})

const canRun = computed(() => !blockReason.value && !running.value && !devicesError.value)

onMounted(async () => {
  await Promise.all([loadDevices(), loadCases()])
})

async function loadDevices(): Promise<void> {
  devicesLoading.value = true
  devicesError.value = ""
  try {
    devices.value = await listDevices()
  } catch (e) {
    devicesError.value = formatApiError(e as never, "设备列表加载失败")
  } finally {
    devicesLoading.value = false
  }
}

/** 项目与用例一次取全量：选择器的过滤、分组、计数都在前端做。 */
async function loadCases(): Promise<void> {
  casesLoading.value = true
  casesError.value = ""
  try {
    projects.value = await listAutomationProjects()
  } catch (e) {
    casesError.value = formatApiError(e as never, "自动化用例加载失败")
  } finally {
    casesLoading.value = false
  }
}

/** 切换来源：按既有口径清空另一侧的输入。 */
function switchSource(next: "yaml" | "platform"): void {
  if (source.value === next) return
  source.value = next
  selectedCaseIds.value = []
  yaml.value = null
  error.value = ""
}

/** 选文件只记在本机，提交时才随表单上传。 */
function onFile(event: Event): void {
  yaml.value = (event.target as HTMLInputElement).files?.[0] || null
  error.value = ""
}

function onMaterial(event: Event): void {
  material.value = (event.target as HTMLInputElement).files?.[0] || null
  error.value = ""
}

async function run(): Promise<void> {
  if (!canRun.value) return
  if (source.value === "yaml" && !yaml.value) return
  running.value = true
  error.value = ""
  try {
    const created = await runSopWorkflow({
      workflowId: props.workflow.id,
      title: props.workflow.name,
      yaml: source.value === "yaml" ? yaml.value : null,
      caseIds: source.value === "platform" ? selectedCaseIds.value : [],
      serial: serial.value.trim(),
      material: kind.value === "ui_automation" ? null : material.value,
    })
    emit("submitted", created.id)
  } catch (e) {
    error.value = formatApiError(e as never, "提交失败")
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="sop-run">
    <p class="sop-run__meta">工作流：{{ workflow.name }}</p>

    <label v-if="kind !== 'ui_automation'" class="assistant-field">
      <span class="assistant-field__label">{{
        kind === "case_authoring" ? "模块材料" : "需求文档"
      }}</span>
      <input
        class="assistant-input"
        type="file"
        accept=".pdf,.doc,.docx,.md,.markdown,.yaml,.yml"
        @change="onMaterial"
      />
      <span class="sop-run__hint">支持 PDF、Word、Markdown、YAML，提交后统一解析成 Markdown</span>
    </label>
    <div v-else class="sop-run__grid">
      <aside class="sop-run__side">
        <div class="assistant-field">
          <span id="sop-source-label" class="assistant-field__label">用例来源</span>
          <div class="sop-run__seg" role="group" aria-labelledby="sop-source-label">
            <button
              type="button"
              class="sop-run__seg-btn"
              :class="{ 'is-on': source === 'platform' }"
              :aria-pressed="source === 'platform'"
              @click="switchSource('platform')"
            >
              平台用例
            </button>
            <button
              type="button"
              class="sop-run__seg-btn"
              :class="{ 'is-on': source === 'yaml' }"
              :aria-pressed="source === 'yaml'"
              @click="switchSource('yaml')"
            >
              本地 YAML
            </button>
          </div>
        </div>

        <label class="assistant-field">
          <span class="assistant-field__label">设备</span>
          <span class="assistant-select">
            <select
              v-model="serial"
              class="assistant-input"
              :disabled="devicesLoading || Boolean(devicesError)"
            >
              <option value="">请选择设备</option>
              <option v-for="item in deviceOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </span>
          <span v-if="devicesError" class="sop-run__hint">{{ devicesError }}，暂时不能提交</span>
          <span v-else-if="devicesLoading" class="sop-run__hint">设备列表加载中…</span>
          <span v-else-if="!deviceOptions.length" class="sop-run__hint">
            设备管理里还没有可连设备，暂时不能提交
          </span>
          <span v-else class="sop-run__hint">只列设备管理里可连的设备，不手填序列号</span>
        </label>

        <div v-if="source === 'platform'" class="sop-run__summary">
          <p class="sop-run__summary-k">本次选用例</p>
          <p class="sop-run__summary-v">
            <b>{{ picked.count }}</b> 条 · 覆盖 <b>{{ picked.projectCount }}</b> 个项目
          </p>
          <p v-if="picked.names.length" class="sop-run__summary-list">
            <span v-for="name in picked.names" :key="name" class="sop-run__summary-item"
              >· {{ name }}</span
            >
            <span v-if="picked.rest" class="sop-run__summary-item"
              >… 还有 {{ picked.rest }} 条</span
            >
          </p>
          <p v-else class="sop-run__summary-list">还没有勾选用例</p>
          <p class="sop-run__summary-note">
            所选用例按步骤编译成一份里程碑，作为任务配置随任务提交。
          </p>
        </div>
      </aside>

      <section class="sop-run__main">
        <CasePicker
          v-if="source === 'platform'"
          :projects="projects"
          :model-value="selectedCaseIds"
          :loading="casesLoading"
          :error="casesError"
          @update:model-value="selectedCaseIds = $event"
          @retry="loadCases"
        />

        <div v-else class="sop-run__yaml">
          <div class="sop-run__yaml-head">
            <span class="assistant-field__label">里程碑 YAML</span>
            <span class="sop-run__hint">上传后按里程碑执行，不选平台用例</span>
          </div>
          <div class="sop-run__pick-row">
            <label class="sop-run__pick">
              <input class="sop-run__file" type="file" accept=".yaml,.yml" @change="onFile" />
              <span>选择文件</span>
            </label>
            <span class="sop-run__filename">{{ yaml?.name || "未选择任何文件" }}</span>
          </div>
          <p class="sop-run__hint">
            一份里程碑 YAML，顶层含 name 与 steps；提交时作为任务配置上传。
          </p>
        </div>
      </section>
    </div>

    <p v-if="error" class="sop-run__error">{{ error }}</p>

    <div class="sop-run__actions">
      <p class="sop-run__status" :class="{ 'is-blocked': !canRun }">
        <template v-if="devicesError">{{ devicesError }}，暂时不能提交</template>
        <template v-else-if="blockReason">{{ blockReason }}</template>
        <template v-else-if="source === 'platform'"
          >已选 <b>{{ selectedCaseIds.length }}</b> 条用例 · 可以开始</template
        >
        <template v-else>里程碑已就绪 · 可以开始</template>
      </p>
      <div class="sop-run__btns">
        <DoodleBtn tone="paper" @click="emit('close')">取消</DoodleBtn>
        <DoodleBtn tone="teal" :disabled="!canRun" @click="run">开始运行</DoodleBtn>
      </div>
    </div>
  </div>
</template>

<style src="./SopRunForm.style.css" scoped></style>
