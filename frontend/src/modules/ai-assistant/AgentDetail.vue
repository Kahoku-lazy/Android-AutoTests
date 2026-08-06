<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getAgentDetail, detectModels as apiDetectModels, uploadAvatar, saveAgent } from "./api/agents";
import { ElMessage, ElMessageBox } from "element-plus";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import { IconArrowLeft } from "@/shared/icons/index";
import { ROUTE_AI_ASSISTANT } from "./constants";
import { useAgentTools } from "./composables/useAgentTools";
import AgentBasicInfo from "./components/AgentBasicInfo.vue";
import AgentModelConfig from "./components/AgentModelConfig.vue";
import AgentPromptEditor from "./components/AgentPromptEditor.vue";
import AgentToolsPanel from "./components/AgentToolsPanel.vue";
import AgentAdvancedConfig from "./components/AgentAdvancedConfig.vue";
import AgentFormFooter from "./components/AgentFormFooter.vue";
import KnowledgeImportDialog from "./components/KnowledgeImportDialog.vue";

const route = useRoute();
const router = useRouter();
const agentId = computed(() => route.params.agentId);
const isNew = computed(() => agentId.value === "new");
const agent = ref(null);
const loading = ref(false);
const loadError = ref("");
const uploading = ref(false);
const fileInput = ref(null);

const form = ref({
  name: "",
  avatar: "🤖",
  tags: "",
  description: "",
  model_provider: "dashscope",
  model_name: "qwen-max",
  api_key: "",
  base_url: "",
  system_prompt: "",
  temperature: 0.7,
  max_tokens: 4096,
  generate_kwargs: "{}",
  formatter: "dashscope",
  max_iters: 10,
  parallel_tool_calls: true,
  print_hint_msg: false,
  memory_mode: "inmemory",
  long_term_memory_mode: "both",
  enable_meta_tool: false,
  enable_rewrite_query: true,
  enable_knowledge_base: false,
  enable_workspace_tools: false,
  enable_business_tools: false,
  enable_mcp_tools: false,
  enable_skills: false,
  tools: [],
  compression_enabled: false,
  compression_threshold: 10000,
  compression_keep_recent: 3,
  compression_prompt: "",
  compression_template: "",
  tts_enabled: false,
  skills_config: {},
  knowledge_sources: {},
});

async function loadAgentDetail() {
  // All data sources are independent — load them in a single parallel batch.
  // Including getAgentDetail avoids a second sequential network round-trip
  // for edit mode.
  loadError.value = "";
  if (!isNew.value) {
    loading.value = true;
  }
  try {
    await Promise.all([
      loadPlatformTools(),
      loadAvailableSkills(),
      loadKnowledgeDocs(),
      loadAgentTools(),
      isNew.value
        ? Promise.resolve()  // New agents start with empty prompt — no default.
        : getAgentDetail(agentId.value).then((data) => {
            if (data?.status) {
              const allTools = data.agent.tools || [];
              const platformNames = allTools
                .filter((t) => t.tool_type === "platform" && t.enabled)
                .map((t) => t.name);
              selectedPlatformTools.value = new Set(platformNames);
              form.value = { ...form.value, ...data.agent, tools: [] };
              agent.value = data.agent;
            }
          }),
    ]);
  } catch (err) {
    if (!isNew.value) {
      loadError.value = "加载智能体详情失败，请检查网络连接";
      console.error('Failed to load agent detail:', err);
    }
  }
  if (!isNew.value) loading.value = false;
}

onMounted(() => { loadAgentDetail() });

const providers = [
  {
    value: "dashscope",
    label: "阿里百炼 (DashScope)",
    formatter: "dashscope",
    models: ["qwen-max", "qwen-plus", "qwen-turbo", "qwen3-235b"],
  },
  {
    value: "openai",
    label: "OpenAI",
    formatter: "openai",
    models: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o4-mini"],
  },
  {
    value: "anthropic",
    label: "Anthropic (Claude)",
    formatter: "anthropic",
    models: ["claude-fable-5", "claude-opus-4-8", "claude-sonnet-4-6"],
  },
  {
    value: "deepseek",
    label: "DeepSeek",
    formatter: "openai",
    models: [
      "deepseek-v4-flash",
      "deepseek-v4-pro",
      "deepseek-chat",
      "deepseek-reasoner",
    ],
  },
  {
    value: "custom",
    label: "自定义 (OpenAI 兼容)",
    formatter: "openai",
    models: [],
  },
];

const detectingModels = ref(false);
const detectedModels = ref([]);


	// ── Tools / Skills / MCP / Knowledge ── composable replaces ~400 lines
	const tools = useAgentTools(form, isNew, agentId)
	const {
	  toolCategories, selectedPlatformTools, loadingPlatformTools,
	  loadPlatformTools, togglePlatformTool, isPlatformToolSelected,
	  toggleCategory, isCategorySelected,
	  availableSkills, enabledSkills, loadingSkills,
	  loadAvailableSkills, isSkillEnabled, toggleSkill,
	  selectAllSkills, deselectAllSkills,
	  knowledgeDocs, loadingDocs, showImportDialog,
	  loadKnowledgeDocs, isDocEnabled, toggleDocEnabled, importDocs, removeDoc,
	  openImportDialog, closeImportDialog, importedDocIds,
	  mcpTools, mcpDialogVisible, mcpDialogMode, mcpForm, mcpJsonError,
	  mcpTestingId, mcpTestResults,
	  loadAgentTools, openMcpDialog, saveMcpTool, testMcp, toggleMcp,
	  removeMcpApi, removeMcpLocal,
	  skills, skillUploading, skillFolderInput, removeSkill, formatSkillSize,
	  platformToolSelectedCount, wsSkillEnabledCount, kbDocSelectedCount,
	  mcpCount, customSkillCount,
	} = tools

	function highlightJson(raw) {
	  if (!raw) return '';
	  try {
	    const obj = JSON.parse(raw);
	    const formatted = JSON.stringify(obj, null, 2);
	    return formatted
	      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
	      .replace(/("(?:[^"\\]|\\.)*")\s*:/g, '<span style="color:#9cdcfe">$1</span>:')
	      .replace(/:\s*("(?:[^"\\]|\\.)*")/g, ': <span style="color:#ce9178">$1</span>')
	      .replace(/:\s*(\d+\.?\d*)/g, ': <span style="color:#b5cea8">$1</span>')
	      .replace(/:\s*(true|false)/g, ': <span style="color:#569cd6">$1</span>')
	      .replace(/:\s*(null)/g, ': <span style="color:#569cd6">$1</span>');
	  } catch { return raw.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
	}

	const configPreviewHtml = computed(() => highlightJson(mcpForm.config_json))

	function triggerSkillUpload() { skillFolderInput.value?.click() }
	async function handleSkillFolderChange(e) {
	  const files = Array.from(e.target.files || [])
	  if (!files.length) return
	  await tools.uploadSkill(files)
	  e.target.value = ''
	}

	// Step 4 collapse panel — default expand memory + platform
	const memoryToolActive = ref(["memory", "platform"])

// 合并内置模型 + API 检测到的模型，去重
const availableModels = computed(() => {
  const builtin =
    providers.find((p) => p.value === form.value.model_provider)?.models || [];
  const all = [...new Set([...builtin, ...detectedModels.value])];
  // 如果当前选择的模型不在列表中，追加
  if (form.value.model_name && !all.includes(form.value.model_name)) {
    all.push(form.value.model_name);
  }
  return all;
});

async function detectModels() {
  if (!form.value.api_key) {
    ElMessage.warning("请先填写 API Key");
    return;
  }
  detectingModels.value = true;
  try {
    const data = await apiDetectModels({
      model_provider: form.value.model_provider,
      api_key: form.value.api_key,
      base_url: form.value.base_url,
    });
    if (data.status) {
      detectedModels.value = data.models || [];
      if (data.models.length) {
        ElMessage.success(`检测到 ${data.models.length} 个可用模型`);
        // 如果当前模型不在列表中，自动选择第一个
        if (
          !data.models.includes(form.value.model_name) &&
          data.models.length
        ) {
          form.value.model_name = data.models[0];
        }
      } else {
        ElMessage.warning("未能检测到可用模型，请检查 API Key 和地址");
      }
    }
  } catch (e) {
    ElMessage.error("模型检测请求失败");
  }
  detectingModels.value = false;
}

function onProviderChange(p) {
  const prov = providers.find((x) => x.value === p);
  if (prov) {
    form.value.formatter = prov.formatter;
    form.value.model_name = prov.models[0] || "";
  }
  detectedModels.value = [];
}

const memoryModes = [
  { value: "inmemory", label: "短期记忆 (InMemory)" },
  { value: "longterm", label: "长期记忆 (LongTerm)" },
];
const ltmModes = [
  { value: "agent_control", label: "智能体控制" },
  { value: "static_control", label: "静态控制" },
  { value: "both", label: "两者结合" },
];

function triggerUpload() {
  fileInput.value?.click();
}
async function handleAvatarUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  uploading.value = true;
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const data = await uploadAvatar( {
        image: reader.result,
      });
      if (data.status) form.value.avatar = data.url;
    } catch (err) { console.error('Failed to upload avatar:', err) }
    uploading.value = false;
  };
  reader.readAsDataURL(file);
}

async function save() {
  // In create mode, include MCP tools in payload. In edit mode, tools are managed via API.
  let allTools = [];
  if (isNew.value) {
    const platformToolRecords = [...selectedPlatformTools.value].map(
      (name) => ({
        name,
        tool_type: "platform",
        enabled: true,
        config_json: "{}",
      }),
    );
    allTools = [
      ...form.value.tools.map((t) => ({
        name: t.name || "",
        tool_type: t.tool_type || "mcp",
        enabled: t.enabled !== false,
        config_json:
          typeof t.config_json === "string"
            ? t.config_json
            : JSON.stringify(t.config_json || {}),
      })),
      ...platformToolRecords,
    ];
  }
  const payload = { ...form.value, tools: allTools };
  try {
    const data = await saveAgent(isNew.value, agentId.value, payload);
    if (data.status) {
      ElMessage.success("保存成功");
      router.push(ROUTE_AI_ASSISTANT);
    } else {
      ElMessage.error(data.message || "保存失败");
    }
  } catch (err) {
    const errors = err.response?.data?.errors;
    const msg =
      err.response?.data?.message ||
      (errors
        ? Object.entries(errors)
            .map(([k, v]) => `${k}: ${v}`)
            .join("; ")
        : null) ||
      err.message;
    ElMessage.error("保存失败: " + msg);
  }
}
</script>

<template>
  <div class="doc-page wb-shell ai-workbench" v-loading="loading">
    <WorkbenchHeader
      :title="isNew ? '新建智能体' : '编辑智能体'"
      :subtitle="
        isNew
          ? '配置一个全新的 AI 智能体'
          : agent?.name
            ? `编辑「${agent.name}」`
            : '编辑智能体'
      "
      icon="settings"
      icon-gradient="linear-gradient(135deg,#5EEAD4,#14b8a6)"
    />

    <ErrorState v-if="loadError" :message="loadError" @retry="loadAgentDetail" />

    <div class="doc-body agent-body">
      <!-- Back button -->
      <button class="back-btn" @click="router.push(ROUTE_AI_ASSISTANT)">
        <IconArrowLeft :size="18" />
        <span>返回智能体列表</span>
      </button>

      <input
        type="file"
        ref="fileInput"
        accept="image/*"
        style="display:none"
        @change="handleAvatarUpload"
      />
      <AgentBasicInfo :form="form" :is-new="isNew" :uploading="uploading"
        @trigger-upload="triggerUpload" @avatar-upload="handleAvatarUpload" />

      <AgentModelConfig :form="form" :is-new="isNew"
        :providers="providers" :available-models="availableModels"
        :detected-models="detectedModels" :detecting-models="detectingModels"
        @provider-change="onProviderChange" @detect-models="detectModels" />

      <AgentPromptEditor :form="form" :is-new="isNew" />

      <AgentToolsPanel :form="form" :is-new="isNew"
        :memory-modes="memoryModes" :ltm-modes="ltmModes"
        :tool-categories="toolCategories" :loading-platform-tools="loadingPlatformTools"
        :selected-platform-tools="selectedPlatformTools" :platform-tool-selected-count="platformToolSelectedCount"
        :is-category-selected="isCategorySelected"
        :available-skills="availableSkills" :loading-skills="loadingSkills"
        :enabled-skills="enabledSkills" :ws-skill-enabled-count="wsSkillEnabledCount"
        :knowledge-docs="knowledgeDocs" :loading-docs="loadingDocs"
        :show-import-dialog="showImportDialog" :imported-doc-ids="importedDocIds" :kb-doc-selected-count="kbDocSelectedCount"
        :mcp-tools="mcpTools" :skills="skills" :mcp-test-results="mcpTestResults"
        :mcp-testing-id="mcpTestingId" :mcp-count="mcpCount" :custom-skill-count="customSkillCount"
        :skill-uploading="skillUploading"
        :mcp-dialog-visible="mcpDialogVisible" :mcp-dialog-mode="mcpDialogMode"
        :mcp-form="mcpForm" :mcp-json-error="mcpJsonError" :config-preview="configPreviewHtml"
        @toggle-platform-tool="togglePlatformTool" @toggle-category="toggleCategory"
        @toggle-skill="toggleSkill"
        @toggle-doc-enabled="toggleDocEnabled"
        @select-all-skills="selectAllSkills" @deselect-all-skills="deselectAllSkills"
        @open-import-dialog="openImportDialog" @remove-doc="removeDoc"
        @open-mcp-dialog="openMcpDialog" @save-mcp-tool="saveMcpTool" @close-mcp-dialog="mcpDialogVisible=false"
        @test-mcp="testMcp" @toggle-mcp="toggleMcp"
        @remove-mcp-api="removeMcpApi" @remove-mcp-local="removeMcpLocal"
        @trigger-skill-upload="triggerSkillUpload" @remove-skill="removeSkill"
        @update:mcp-dialog-visible="mcpDialogVisible=$event" />

      <KnowledgeImportDialog
        :visible="showImportDialog"
        :all-docs="knowledgeDocs"
        :imported-doc-ids="importedDocIds"
        @import="importDocs" @close="closeImportDialog" />

      <AgentAdvancedConfig :form="form" :is-new="isNew" />

      <AgentFormFooter :is-new="isNew" @save="save" />
    </div>
  </div>
</template>

<style scoped>
/* ── Page layout ── */
.agent-body {
  flex: 1; min-height: 0; display: flex; flex-direction: column;
  gap: 18px; padding-bottom: 40px; overflow-x: hidden; overflow-y: auto;
}

/* ── Back button ── */
.back-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px;
  border: 2px solid var(--ai-teal); border-radius: 12px; background: var(--ai-teal-bg);
  color: var(--ai-teal-text); font-size: var(--app-size-md); font-weight: 700; font-family: inherit;
  cursor: pointer; transition: all 0.2s ease; align-self: flex-start;
}
.back-btn:hover { background: var(--ai-teal); color: #fff; box-shadow: 0 4px 14px rgba(25,200,185,0.35); transform: translateY(-1px); }

/* ── Shared step panel (used by all 5 sub-components) ── */
.step-panel { padding: 28px 32px; }
.section-title {
  display: flex; align-items: center; gap: 12px; font-size: var(--app-size-lg); font-weight: 700;
  color: var(--ai-ink-soft); margin-bottom: 24px; padding-bottom: 14px; border-bottom: 2px solid var(--ai-bg-subtle);
}
.section-num {
  display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;
  border-radius: 10px; background: linear-gradient(135deg,var(--ai-teal),var(--ai-teal-hover));
  color: #fff; font-size: var(--app-size-md); font-weight: 700; box-shadow: 0 3px 8px rgba(25,200,185,0.3);
}
.agent-form :deep(.el-form-item__label) { font-size: var(--app-size-md); font-weight: 600; color: var(--ai-ink-subtle); }
.agent-form :deep(.el-input__wrapper),
.agent-form :deep(.el-textarea__inner) { border-radius: 10px; font-size: var(--app-size-md); }
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
</style>

