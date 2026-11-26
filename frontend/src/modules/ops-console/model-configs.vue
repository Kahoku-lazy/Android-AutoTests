<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import OpsModelIdentityCell from "./components/OpsModelIdentityCell.vue"
import { createModelConfig, deleteModelConfig, listModelConfigs, updateModelConfig } from "./api"
import {
  defaultProviderForKind,
  keyForProvider,
  modelKindClass,
  modelKindLabel,
  normalizeProvider,
  OPS_DEFAULT_MODEL_KIND,
  OPS_MODEL_COLUMNS,
  OPS_MODEL_KIND_OPTIONS,
  OPS_MODEL_PAGE_SIZE,
  OPS_OMNI_VOICES,
  OPS_PAGE_ICON,
  OPS_PAGE_ICON_GRADIENT,
  OPS_PROTOCOL_OPTIONS,
  OPS_TTS_VOICES,
  providersForKind,
} from "./constants"
import type { OpsModelConfig, OpsModelConfigInput } from "./types"
import { useModelNameDraft } from "./composables/useModelNameDraft"

const configs = ref<OpsModelConfig[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")
const saving = ref(false)
const editorOpen = ref(false)
const editingId = ref<number | null>(null)
const keyword = ref("")

const visibleConfigs = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return configs.value
  return configs.value.filter((row) =>
    [
      row.model_name,
      row.provider,
      modelKindLabel(row.model_kind),
      row.api_key_env,
      row.base_url,
    ].some((field) => (field || "").toLowerCase().includes(q)),
  )
})

function onCommand(command: string, row: OpsModelConfig): void {
  if (command === "delete") void remove(row)
}

const page = ref(1)
const totalPages = computed(() =>
  Math.max(1, Math.ceil(visibleConfigs.value.length / OPS_MODEL_PAGE_SIZE)),
)
const pagedConfigs = computed(() =>
  visibleConfigs.value.slice(
    (page.value - 1) * OPS_MODEL_PAGE_SIZE,
    page.value * OPS_MODEL_PAGE_SIZE,
  ),
)

function goPage(next: number): void {
  page.value = Math.max(1, Math.min(next, totalPages.value))
}

watch(keyword, () => {
  page.value = 1
})

function blankForm(): OpsModelConfigInput {
  const provider = defaultProviderForKind(OPS_DEFAULT_MODEL_KIND)
  return {
    provider,
    api_protocol: "deepseek",
    model_kind: OPS_DEFAULT_MODEL_KIND,
    voice: "",
    dimensions: null,
    api_key_env: keyForProvider(provider),
    base_url: "",
    model_name: "",
  }
}

const form = ref<OpsModelConfigInput>(blankForm())
const providerOptions = computed(() => providersForKind(form.value.model_kind))

const {
  rows: nameRows,
  loading: loadingNames,
  hint: discoverHint,
  single: singleModelName,
  reset: resetNameRows,
  add: addNameRow,
  remove: removeNameRow,
  names: namesInForm,
  validUrl: validApiUrl,
  discover: loadNames,
} = useModelNameDraft(form)

watch(
  () => form.value.provider,
  (provider) => {
    const key = keyForProvider(provider)
    if (key) form.value.api_key_env = key
  },
)

watch(
  () => form.value.model_kind,
  (kind) => {
    form.value.provider = normalizeProvider(kind, form.value.provider)
  },
)

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    const { data } = await listModelConfigs()
    if (!data.status || !data.data) throw data
    configs.value = data.data.configs || []

    page.value = Math.min(
      page.value,
      Math.max(1, Math.ceil(configs.value.length / OPS_MODEL_PAGE_SIZE)),
    )
    loaded.value = true
  } catch (e) {
    error.value = formatApiError(e as never, "模型配置加载失败")
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editingId.value = null
  form.value = blankForm()
  resetNameRows([""])
  discoverHint.value = ""
  editorOpen.value = true
}

function openEdit(row: OpsModelConfig): void {
  editingId.value = row.id
  const kind = row.model_kind || OPS_DEFAULT_MODEL_KIND
  const provider = normalizeProvider(kind, row.provider)
  form.value = {
    provider,
    api_protocol: row.api_protocol || "openai",
    model_kind: kind,
    voice: row.voice || "",
    dimensions: row.dimensions ?? null,
    api_key_env: keyForProvider(provider),
    base_url: row.base_url || "",
    model_name: row.model_name,
  }
  resetNameRows([row.model_name])
  discoverHint.value = ""
  editorOpen.value = true
}

async function save(): Promise<void> {
  if (
    form.value.model_kind !== "tts" &&
    form.value.model_kind !== "embedding" &&
    !validApiUrl(form.value.base_url)
  ) {
    ElMessage.error(
      form.value.base_url.trim() ? "API 地址必须是 http 或 https 链接" : "API 地址不能为空",
    )
    return
  }
  if (form.value.model_kind === "embedding" && !(Number(form.value.dimensions) > 0)) {
    ElMessage.error("向量维度必须是正整数")
    return
  }
  const names = namesInForm()
  if (!names.length) {
    ElMessage.warning("请填写至少一个模型名称")
    return
  }
  saving.value = true
  try {
    if (editingId.value != null) {
      const { data } = await updateModelConfig(editingId.value, {
        ...form.value,
        model_name: names[0],
      })
      if (!data.status) throw data
      for (const name of names.slice(1)) {
        const created = await createModelConfig({ ...form.value, model_name: name })
        if (!created.data.status) throw created.data
      }
    } else {
      for (const name of names) {
        const { data } = await createModelConfig({ ...form.value, model_name: name })
        if (!data.status) throw data
      }
    }
    editorOpen.value = false
    ElMessage.success(names.length > 1 ? `已保存 ${names.length} 个模型` : "已保存")
    await load()
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "保存失败"))
  } finally {
    saving.value = false
  }
}

async function remove(row: OpsModelConfig): Promise<void> {
  try {
    await ElMessageBox.confirm(`删除模型「${row.model_name}」？`, "请确认", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })
  } catch {
    return
  }
  try {
    const { data } = await deleteModelConfig(row.id)
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
      title="模型配置"
      subtitle="一个密钥可以配置多个模型。这里只保存环境变量名，不保存密钥明文。"
      :icon="OPS_PAGE_ICON"
      :icon-gradient="OPS_PAGE_ICON_GRADIENT"
    />
    <div class="doc-body">
      <section class="ops-section">
        <!-- 行 1：搜索 + 新建（计数下沉到第二行的页码文案，避免同一个数字写两遍） -->
        <div class="ops-controls">
          <el-input
            v-model="keyword"
            placeholder="搜索厂商 / 模型名"
            clearable
            class="ops-search"
            size="small"
          />
          <DoodleBtn tone="yellow" class="ops-controls__push" @click="openCreate">
            新建模型
          </DoodleBtn>
        </div>

        <div class="ops-controls">
          <span class="ops-page-info">
            第 {{ page }} / {{ totalPages }} 页 · 共 {{ visibleConfigs.length }} 条
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
        <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="5" />
        <AppTable
          v-else
          :columns="OPS_MODEL_COLUMNS"
          :data-source="pagedConfigs"
          row-key="id"
          :loading="loading"
          empty-text="还没有模型配置"
          table-layout="fixed"
          accent="var(--c-ops)"
        >
          <template
            v-for="col in OPS_MODEL_COLUMNS"
            :key="`head-${col.prop}`"
            v-slot:[`header-${col.prop}`]
          >
            <span class="th-ico" aria-hidden="true">{{ col.icon }}</span>{{ col.label }}
          </template>

          <template #cell-model="{ record }">
            <OpsModelIdentityCell :config="record" />
          </template>

          <template #cell-model_kind="{ record }">
            <span :class="modelKindClass(record.model_kind)">{{
              modelKindLabel(record.model_kind)
            }}</span>
          </template>

          <template #cell-base_url="{ record }">{{ record.base_url || "厂商默认" }}</template>

          <template #cell-actions="{ record }">
            <div class="ops-row-actions">
              <button type="button" class="ops-action-pill" @click.stop="openEdit(record)">
                编辑
              </button>
              <el-dropdown trigger="click" @command="onCommand($event, record)">
                <button type="button" class="ops-more" @click.stop>⋯</button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="delete">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <template #empty>
            <EmptyState icon="◇" text="还没有模型配置" hint="先建一条，智能体页才能选择" />
          </template>
        </AppTable>
      </section>
    </div>

    <el-drawer
      v-model="editorOpen"
      :title="editingId == null ? '新建模型' : '编辑模型'"
      size="min(460px, 92vw)"
    >
      <div class="sketch-kit">
        <div class="sketch-form">
          <label class="sketch-field">
            <span class="sketch-field__label">模型类型</span>
            <el-select v-model="form.model_kind">
              <el-option
                v-for="item in OPS_MODEL_KIND_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </label>
          <label class="sketch-field">
            <span class="sketch-field__label">厂商</span>
            <el-select v-model="form.provider">
              <el-option
                v-for="item in providerOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </label>
          <label class="sketch-field">
            <span class="sketch-field__label">密钥环境变量</span>
            <el-input :model-value="form.api_key_env" disabled />
          </label>
          <label class="sketch-field">
            <span class="sketch-field__label">API 协议</span>
            <el-select v-model="form.api_protocol">
              <el-option
                v-for="item in OPS_PROTOCOL_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </label>
          <label v-if="form.model_kind === 'embedding'" class="sketch-field">
            <span class="sketch-field__label">向量维度</span>
            <el-input v-model.number="form.dimensions" placeholder="例如 1024" />
          </label>
          <label
            v-if="form.model_kind !== 'tts' && form.model_kind !== 'embedding'"
            class="sketch-field"
          >
            <span class="sketch-field__label">API 地址</span>
            <el-input
              v-model="form.base_url"
              :placeholder="
                form.model_kind === 'realtime'
                  ? '必填，例如 wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
                  : '必填，例如 https://api.deepseek.com'
              "
            />
          </label>
          <div class="sketch-field">
            <span class="sketch-field__label">
              模型名称
              <DoodleBtn
                v-if="form.model_kind === 'chat'"
                tone="paper"
                :disabled="loadingNames"
                @click="loadNames"
              >
                {{ loadingNames ? "加载中" : "加载模型" }}
              </DoodleBtn>
            </span>
            <div class="sketch-names">
              <template v-if="form.model_kind === 'chat'">
                <div v-for="(row, index) in nameRows" :key="row.key" class="sketch-names__row">
                  <el-input v-model="row.value" />
                  <DoodleBtn tone="danger" @click="removeNameRow(index)">删除</DoodleBtn>
                </div>
                <p v-if="!nameRows.length" class="sketch-names__hint">
                  还没有模型名称，点「+ 添加一行」开始。
                </p>
                <div class="sketch-names__foot">
                  <DoodleBtn tone="paper" @click="addNameRow">+ 添加一行</DoodleBtn>
                  <span v-if="discoverHint" class="sketch-names__hint">{{ discoverHint }}</span>
                </div>
              </template>
              <el-input v-else v-model="singleModelName" />
            </div>
          </div>
          <label
            v-if="form.model_kind !== 'chat' && form.model_kind !== 'embedding'"
            class="sketch-field"
          >
            <span class="sketch-field__label">音色</span>
            <el-select v-model="form.voice" filterable allow-create placeholder="选择或手填音色">
              <el-option
                v-for="voice in form.model_kind === 'realtime' ? OPS_OMNI_VOICES : OPS_TTS_VOICES"
                :key="voice"
                :label="voice"
                :value="voice"
              />
            </el-select>
          </label>
          <div class="sketch-form__actions">
            <DoodleBtn tone="paper" @click="editorOpen = false">取消</DoodleBtn>
            <DoodleBtn tone="yellow" class="doodle-btn--save" :disabled="saving" @click="save"
              >保存</DoodleBtn
            >
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style src="./table.style.css" scoped></style>
<style src="./index.style.css" scoped></style>
<style src="./model-configs.style.css" scoped></style>
