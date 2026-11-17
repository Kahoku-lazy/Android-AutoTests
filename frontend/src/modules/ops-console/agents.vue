<script setup lang="ts">
/** 运营后台 · Agent配置：名称、一条模型配置、系统提示词。 */
import { computed, onMounted, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
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
  OPS_AGENT_PAGE_SIZE,
  OPS_AGENT_PAGE_SUBTITLE,
  OPS_AGENT_PAGE_TITLE,
  OPS_PAGE_ICON,
  OPS_PAGE_ICON_GRADIENT,
} from "./constants"
import type { OpsAgent, OpsAgentInput, OpsModelConfig } from "./types"

const agents = ref<OpsAgent[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")
const saving = ref(false)
const editorOpen = ref(false)
const editingId = ref<string | null>(null)
const configs = ref<OpsModelConfig[]>([])
const form = ref<OpsAgentInput>({ name: "", model_config_id: null, system_prompt: "" })
const promptFile = ref<HTMLInputElement>()

const modelOptions = computed(() =>
  configs.value.map((item) => ({
    id: item.id,
    label: `${item.api_key_env} / ${item.model_name}`,
  })),
)

// ── 本页分页：Agent 配置接口一次返回全部，前端按每页 10 条切片 ──
const page = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(agents.value.length / OPS_AGENT_PAGE_SIZE)))
const pagedAgents = computed(() =>
  agents.value.slice((page.value - 1) * OPS_AGENT_PAGE_SIZE, page.value * OPS_AGENT_PAGE_SIZE),
)

/** 翻页：越界夹到首 / 末页，判断放在这里，模板只负责禁用态。 */
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
    // 删除后当前页可能已越界：夹回最后一页，避免停在空白页
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
  form.value = { name: "", model_config_id: null, system_prompt: "" }
  editorOpen.value = true
}

function openEdit(agent: OpsAgent): void {
  editingId.value = agent.role_id
  form.value = {
    name: agent.name || "",
    model_config_id: agent.model_config_id,
    system_prompt: agent.system_prompt || "",
  }
  editorOpen.value = true
}

async function save(): Promise<void> {
  const name = form.value.name.trim()
  if (!name) {
    ElMessage.warning("请填写名称")
    return
  }
  if (form.value.model_config_id == null) {
    ElMessage.warning("请选择模型配置")
    return
  }
  saving.value = true
  const payload = { ...form.value, name }
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
        <!-- 行 1：新建配置 -->
        <div class="ops-toolbar">
          <DoodleBtn tone="yellow" @click="openCreate">新建配置</DoodleBtn>
        </div>

        <!-- 行 2：页码文案 + 翻页（常驻，只有一页时两键置灰仍可见） -->
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
          <template #cell-system_prompt="{ record }">{{ record.system_prompt || "—" }}</template>
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
  </div>
</template>

<style src="./index.style.css" scoped></style>
<style scoped>
/* 行间距：新建配置 / 翻页行 / 表格之间取 --app-space-md（16px），
   比共享骨架的 8px 更松，避免按键紧贴表格表头。 */
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
</style>
