<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import OpsPromptPreview from "./components/OpsPromptPreview.vue"
import OpsAgentKindTags from "./components/OpsAgentKindTags.vue"
import {
  draftFromAgent,
  draftProblem,
  draftToInput,
  emptyDraft,
  type AgentFormDraft,
} from "./helpers/agent-form"
import { formatApiError } from "@/shared/api-client"
import {
  createOpsAgent,
  deleteOpsAgent,
  listModelConfigs,
  listOpsAgents,
  updateOpsAgent,
} from "./api"
import {
  OPS_AGENT_COLUMNS,
  OPS_AGENT_DELETE_HINT,
  OPS_AGENT_EMPTY,
  OPS_AGENT_KIND_OPTIONS,
  OPS_AGENT_PAGE_SIZE,
  OPS_AGENT_PAGE_SUBTITLE,
  OPS_AGENT_PAGE_TITLE,
  OPS_PAGE_ICON,
  OPS_PAGE_ICON_GRADIENT,
} from "./constants"
import type { OpsAgent, OpsModelConfig } from "./types"

const agents = ref<OpsAgent[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")
const saving = ref(false)
const editorOpen = ref(false)
const editingId = ref<string | null>(null)
const configs = ref<OpsModelConfig[]>([])
const form = ref<AgentFormDraft>({ name: "", model_config_id: null, system_prompt: "", kind: "" })
const promptFile = ref<HTMLInputElement>()

const previewOpen = ref(false)
const previewAgent = ref<OpsAgent | null>(null)

function openPreview(agent: OpsAgent): void {
  previewAgent.value = agent
  previewOpen.value = true
}

const modelOptions = computed(() =>
  configs.value.map((item) => ({
    id: item.id,
    label: `${item.api_key_env} / ${item.model_name}`,
  })),
)

const page = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(agents.value.length / OPS_AGENT_PAGE_SIZE)))
const pagedAgents = computed(() =>
  agents.value.slice((page.value - 1) * OPS_AGENT_PAGE_SIZE, page.value * OPS_AGENT_PAGE_SIZE),
)

function goPage(next: number): void {
  page.value = Math.max(1, Math.min(next, totalPages.value))
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    const { data } = await listOpsAgents()
    if (!data.status || !data.data) throw data
    agents.value = data.data || []

    page.value = Math.min(
      page.value,
      Math.max(1, Math.ceil(agents.value.length / OPS_AGENT_PAGE_SIZE)),
    )
    const configRes = await listModelConfigs()
    configs.value = configRes.data.data?.configs || []
    loaded.value = true
  } catch (e) {
    error.value = formatApiError(e as never, "Agent配置加载失败")
  } finally {
    loading.value = false
  }
}

function readPromptFile(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ""
  if (!file) return
  if (!file.name.toLowerCase().endsWith(".md")) {
    ElMessage.warning("请上传 .md 文件")
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form.value.system_prompt = String(reader.result || "")
    ElMessage.success("已读入，可继续修改")
  }
  reader.onerror = () => {
    ElMessage.error("文件读取失败")
  }
  reader.readAsText(file)
}

function openCreate(): void {
  editingId.value = null
  form.value = emptyDraft()
  editorOpen.value = true
}

function openEdit(agent: OpsAgent): void {
  editingId.value = agent.role_id
  form.value = draftFromAgent(agent)
  editorOpen.value = true
}

async function save(): Promise<void> {
  const payload = draftToInput(form.value)
  const problem = draftProblem(payload)
  if (problem) {
    ElMessage.warning(problem)
    return
  }
  saving.value = true
  try {
    const { data } =
      editingId.value == null
        ? await createOpsAgent(payload)
        : await updateOpsAgent(editingId.value, payload)
    if (!data.status) throw data
    editorOpen.value = false
    ElMessage.success(editingId.value == null ? "已创建" : "已保存")
    await load()
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "保存失败"))
  } finally {
    saving.value = false
  }
}

async function remove(agent: OpsAgent): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `删除 Agent 配置「${agent.name}」？\n${OPS_AGENT_DELETE_HINT}`,
      "请确认",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    )
  } catch {
    return
  }
  try {
    const { data } = await deleteOpsAgent(agent.role_id)
    if (!data.status) throw data
    ElMessage.success("已删除")
    await load()
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "删除失败"))
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ops-workbench">
    <WorkbenchHeader
      :title="OPS_AGENT_PAGE_TITLE"
      :subtitle="OPS_AGENT_PAGE_SUBTITLE"
      :icon="OPS_PAGE_ICON"
      :icon-gradient="OPS_PAGE_ICON_GRADIENT"
    />

    <div class="doc-body">
      <section class="doc-section ops-section" data-testid="ops-agents-page">
        <div class="ops-toolbar">
          <DoodleBtn tone="yellow" @click="openCreate">新建配置</DoodleBtn>
        </div>

        <div class="ops-controls">
          <span class="ops-page-info">
            第 {{ page }} / {{ totalPages }} 页 · 共 {{ agents.length }} 条
          </span>
          <div class="ops-page-nav">
            <DoodleBtn tone="paper" :disabled="page <= 1" @click="goPage(page - 1)">
              上一页
            </DoodleBtn>
            <DoodleBtn tone="paper" :disabled="page >= totalPages" @click="goPage(page + 1)">
              下一页
            </DoodleBtn>
          </div>
        </div>

        <ErrorState v-if="error && !loaded" :message="error" @retry="load" />
        <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="6" />
        <AppTable
          v-else
          :columns="OPS_AGENT_COLUMNS"
          :data-source="pagedAgents"
          row-key="role_id"
          :border="true"
          :loading="loading"
          :empty-text="OPS_AGENT_EMPTY"
          accent="var(--c-ops)"
        >
          <template #cell-model_name="{ record }">
            {{ record.api_key_env }} / {{ record.model_name }}
          </template>
          <template #cell-kinds="{ record }">
            <OpsAgentKindTags :kinds="record.kinds" />
          </template>
          <template #cell-system_prompt="{ record }">
            <button
              v-if="record.system_prompt"
              class="ops-prompt"
              type="button"
              :aria-label="`查看「${record.name}」的系统提示词全文`"
              @click.stop="openPreview(record)"
            >
              <span class="ops-prompt__text">{{ record.system_prompt }}</span>
              <span class="ops-prompt__more">查看</span>
            </button>
            <span v-else class="ops-prompt__none">—</span>
          </template>
          <template #cell-actions="{ record }">
            <DoodleBtn tone="paper" @click.stop="openEdit(record)">编辑</DoodleBtn>
            <DoodleBtn tone="danger" @click.stop="remove(record)">删除</DoodleBtn>
          </template>
          <template #empty>
            <EmptyState icon="🤖" :text="OPS_AGENT_EMPTY" hint="点右上角新建一条" />
          </template>
        </AppTable>
      </section>
    </div>

    <el-drawer
      v-model="editorOpen"
      :title="editingId == null ? '新建配置' : '编辑配置'"
      size="min(460px, 92vw)"
    >
      <div class="ops-form">
        <label class="ops-field">
          名称
          <el-input v-model="form.name" maxlength="200" placeholder="给智能体起个名字" />
        </label>
        <label class="ops-field">
          类型
          <el-radio-group v-model="form.kind" class="ops-kind-picker">
            <el-radio-button
              v-for="item in OPS_AGENT_KIND_OPTIONS"
              :key="item.value"
              :value="item.value"
            >
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
        </label>
        <label class="ops-field">
          模型配置
          <el-select v-model="form.model_config_id" placeholder="先在模型配置里新增">
            <el-option
              v-for="item in modelOptions"
              :key="item.id"
              :label="item.label"
              :value="item.id"
            />
          </el-select>
        </label>
        <label class="ops-field">
          系统提示词
          <span class="ops-prompt__tools">
            <DoodleBtn tone="paper" @click="promptFile?.click()">上传 Markdown</DoodleBtn>
            <input
              ref="promptFile"
              class="ops-prompt__file"
              type="file"
              accept=".md,text/markdown"
              @change="readPromptFile"
            />
          </span>
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="8"
            placeholder="可留空，或上传 .md 后继续修改"
          />
        </label>
        <div class="ops-form__actions">
          <DoodleBtn tone="paper" @click="editorOpen = false">取消</DoodleBtn>
          <DoodleBtn tone="yellow" :disabled="saving" @click="save">
            {{ saving ? "保存中" : "保存" }}
          </DoodleBtn>
        </div>
      </div>
    </el-drawer>

    <OpsPromptPreview
      v-model="previewOpen"
      :name="previewAgent?.name || ''"
      :prompt="previewAgent?.system_prompt || ''"
    />
  </div>
</template>

<style src="./index.style.css" scoped></style>
<style scoped>
.ops-section {
  gap: var(--app-space-md);
}

.ops-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ops-prompt__tools {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.ops-prompt__file {
  display: none;
}

.ops-field {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ops-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--app-space-sm);
}

.ops-prompt {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.ops-prompt__text {
  flex: 1 1 0;
  width: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--app-text-primary);
}

.ops-prompt__more {
  flex: 0 0 auto;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.ops-prompt:hover .ops-prompt__more {
  color: var(--app-text-primary);
}

.ops-prompt:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

.ops-prompt__none {
  color: var(--app-text-secondary);
}
</style>
