<script setup lang="ts">
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import type { FormInstance, UploadFile } from "element-plus"
import { ElMessage } from "element-plus"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue"
import DoodleNote from "@/shared/components/DoodleNote.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import {
  TASK_STATUS_LABELS,
  taskDetailRoute,
  taskStatusTone,
  type TaskStatusTone,
} from "../constants"
import { formatTaskCost, formatTaskDuration } from "../helpers/task-detail"
import {
  isSelectableTaskDevice,
  taskDeviceAddress,
  taskDeviceLabel,
} from "../helpers/task-device-address"
import { useTaskPublish } from "../composables/useTaskPublish"
import { useTaskList } from "../composables/useTaskList"
import type { TaskRecord } from "@/shared/types/ai"

/** 任务态 → sticky 底色：成功 Do / 失败 Dont / 执行中 / 等待 */
function stickyStatus(tone: TaskStatusTone): "ok" | "run" | "fail" | "wait" {
  if (tone === "success") return "ok"
  if (tone === "failed") return "fail"
  if (tone === "running") return "run"
  return "wait"
}

function deviceDisplay(t: TaskRecord): string {
  return (t.device_label || t.device_serial || "—").trim() || "—"
}

function statusLabel(status: string): string {
  return TASK_STATUS_LABELS[status] || TASK_STATUS_LABELS[taskStatusTone(status)] || status || "—"
}

const router = useRouter()
const {
  form,
  submitting,
  devices,
  agentOptions,
  isCaseAuthoring,
  caseTitles,
  caseError,
  dialogVisible,
  CONFIG_ACCEPT,
  DOCUMENT_ACCEPT,
  openDialog,
  closeDialog,
  submit,
  canSubmit,
  onConfigChange,
  clearConfig,
  onDocumentChange,
  onDocumentRemove,
} = useTaskPublish()

const selectableDevices = computed(() => devices.value.filter(isSelectableTaskDevice))

const taskFormRef = ref<FormInstance>()
const taskRules = computed(() => ({
  title: [{ required: true, message: "请填写任务标题", trigger: "blur" }],
  agent_id: [{ required: true, message: "请选择智能体", trigger: "change" }],
  ...(isCaseAuthoring.value
    ? {}
    : { device_serial: [{ required: true, message: "请选择设备", trigger: "change" }] }),
}))
const {
  tasks,
  loading,
  error,
  load,
  activeFilter,
  filterTabs,
  filteredItems,
  groupedByStatus,
  expandedGroups,
  emptyCopy,
  clearAll,
  rerun,
  rerunningId,
  cancel,
  cancellingId,
} = useTaskList()

function openDetail(taskId: number) {
  router.push(taskDetailRoute(taskId))
}

function isFailed(t: TaskRecord): boolean {
  const tone = taskStatusTone(t.status)
  return tone === "failed" || tone === "interrupted"
}

function attachmentNames(t: TaskRecord): string {
  const names = t.attachment_names?.filter(Boolean) || []
  if (names.length) return names.join("、")
  return t.attachment_filename || "—"
}

function isRunning(t: TaskRecord): boolean {
  return taskStatusTone(t.status) === "running"
}

function pickedFile(file: UploadFile): File | null {
  return file.raw ?? null
}

function onConfigPicked(file: UploadFile) {
  const raw = pickedFile(file)
  if (!raw) return
  if (!/\.(yaml|yml)$/i.test(raw.name || "")) {
    ElMessage.error("配置只收 YAML（.yaml / .yml）")
    clearConfig()
    return
  }
  if (raw.size > 20 * 1024 * 1024) {
    ElMessage.error("文件过大（上限 20MB）")
    clearConfig()
    return
  }
  onConfigChange(raw)
}

async function onSubmit() {
  try {
    await taskFormRef.value?.validate()
  } catch {
    return
  }
  await submit(() => {
    closeDialog()
    load()
  })
}
</script>

<template>
  <section class="doc-section step-panel">
    <div class="doc-section__header">
      <h3 class="doc-section__title">任务卡片<span class="doc-tag">Task</span></h3>
      <div class="task-board__actions">
        <FilterTabs :tabs="filterTabs" v-model="activeFilter" />
        <ConfirmButton
          type="warning"
          danger
          plain
          message="将删除全部任务卡片，且不可恢复。确认清空？"
          title="调试 · 清空任务"
          confirm-text="清空"
          :disabled="!tasks.length"
          @confirm="clearAll"
          >调试 · 清空</ConfirmButton
        >
        <el-button type="primary" @click="openDialog">新建任务</el-button>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建任务" width="640px" :close-on-click-modal="false">
      <el-form
        ref="taskFormRef"
        :model="form"
        :rules="taskRules"
        label-width="120px"
        @submit.prevent
      >
        <el-form-item label="任务标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="例如：校准 H705F 色温"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="智能体" prop="agent_id">
          <el-select
            v-model="form.agent_id"
            style="width: 100%"
            filterable
            placeholder="请选择智能体"
          >
            <el-option
              v-for="item in agentOptions"
              :key="item.id"
              :label="item.label"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <template v-if="isCaseAuthoring">
          <el-form-item label="需求文档">
            <el-upload
              :accept="DOCUMENT_ACCEPT"
              :limit="5"
              multiple
              :auto-upload="false"
              :show-file-list="true"
              :on-change="onDocumentChange"
              :on-remove="onDocumentRemove"
            >
              <el-button size="small">选择 PRD / Word</el-button>
            </el-upload>
            <p class="task-attach-name">
              支持 .docx / .pdf / .md；上传后由 Agent-02 解析需求并生成测试用例
            </p>
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="配置">
            <el-upload
              :accept="CONFIG_ACCEPT"
              :limit="1"
              :auto-upload="false"
              :show-file-list="true"
              :on-change="onConfigPicked"
              :on-remove="clearConfig"
            >
              <el-button size="small">选择 YAML</el-button>
            </el-upload>
            <p class="task-attach-name">配置只收 YAML：.yaml / .yml，单份，上限 20MB</p>
            <p v-if="form.configFile" class="task-attach-name">已选：{{ form.configFile.name }}</p>
            <p v-if="caseError" class="task-case-error">{{ caseError }}</p>
          </el-form-item>
          <el-form-item label="设备" prop="device_serial">
            <el-select
              v-model="form.device_serial"
              style="width: 100%"
              clearable
              filterable
              placeholder="请选择设备"
            >
              <el-option
                v-for="d in selectableDevices"
                :key="d.serial"
                :label="taskDeviceLabel(d)"
                :value="taskDeviceAddress(d)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="测试指定用例">
            <el-select
              v-model="form.case_title"
              style="width: 100%"
              clearable
              placeholder="全部用例"
              @clear="form.case_title = ''"
            >
              <el-option label="全部用例" value="" />
              <el-option v-for="title in caseTitles" :key="title" :label="title" :value="title" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!canSubmit()" @click="onSubmit"
          >提交</el-button
        >
      </template>
    </el-dialog>

    <!-- 任务卡片列表 -->
    <ErrorState v-if="error" :message="error" @retry="load" />
    <template v-else>
      <div v-loading="loading" class="task-board__body">
        <el-collapse
          v-if="groupedByStatus.length"
          v-model="expandedGroups"
          class="task-status-collapse"
        >
          <el-collapse-item
            v-for="group in groupedByStatus"
            :key="group.key"
            :name="group.key"
            :class="`is-${group.key}`"
          >
            <template #title>
              <div class="task-status-head">
                <span class="task-status-head__label" :class="`is-${group.key}`">{{
                  group.label
                }}</span>
                <span class="task-status-head__count">{{ group.items.length }}</span>
              </div>
            </template>
            <div class="task-card-grid">
              <DoodleNote
                v-for="t in group.items"
                :key="t.id"
                class="task-card"
                variant="sticky"
                :status="stickyStatus(taskStatusTone(t.status))"
                :tilt="taskStatusTone(t.status) === 'failed' ? 1.2 : -1.1"
              >
                <template #header>
                  <h4 class="task-card__title">{{ t.title || "未命名任务" }}</h4>
                </template>
                <ul class="task-card__meta">
                  <li><span class="task-card__meta-k">状态</span>{{ statusLabel(t.status) }}</li>
                  <li>
                    <span class="task-card__meta-k">类型</span
                    >{{ t.task_kind === "case_authoring" ? "用例编写" : "设备执行" }}
                  </li>
                  <li><span class="task-card__meta-k">创建</span>{{ t.created_at || "—" }}</li>
                  <li><span class="task-card__meta-k">设备</span>{{ deviceDisplay(t) }}</li>
                  <li><span class="task-card__meta-k">助手</span>{{ t.assistant_name || "—" }}</li>
                  <li>
                    <span class="task-card__meta-k">费用</span>{{ formatTaskCost(t.deepseek_cost) }}
                  </li>
                  <li>
                    <span class="task-card__meta-k">耗时</span
                    >{{ formatTaskDuration(t.started_at, t.finished_at) }}
                  </li>
                  <li class="task-card__meta-row">
                    <span class="task-card__meta-k">附件</span>
                    <span class="task-card__meta-v">{{ attachmentNames(t) }}</span>
                  </li>
                </ul>
                <template #actions>
                  <DoodleBtn
                    v-if="isRunning(t)"
                    tone="danger"
                    :disabled="cancellingId === t.id"
                    @click="cancel(t)"
                  >
                    {{ cancellingId === t.id ? "关闭中…" : "关闭" }}
                  </DoodleBtn>
                  <DoodleBtn
                    v-if="isFailed(t)"
                    tone="yellow"
                    :disabled="rerunningId === t.id"
                    @click="rerun(t)"
                  >
                    {{ rerunningId === t.id ? "重新执行中…" : "重新执行" }}
                  </DoodleBtn>
                  <DoodleBtn tone="teal" @click="openDetail(t.id)">详情</DoodleBtn>
                </template>
              </DoodleNote>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <EmptyState
        v-if="!filteredItems.length && !loading"
        icon="📋"
        :text="emptyCopy.text"
        :hint="emptyCopy.hint"
      />
    </template>
  </section>
</template>

<style src="./TaskBoard.style.css" scoped></style>
