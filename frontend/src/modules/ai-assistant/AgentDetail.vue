<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getAgentDetail, detectModels as apiDetectModels, uploadAvatar, saveAgent } from "./api.js";
import { ElMessage, ElMessageBox } from "element-plus";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import { IconArrowLeft, IconSave } from "@/shared/icons/index.js";
import { fetchDefaultPrompt } from "./api.js";
import { useAgentTools } from "./composables/useAgentTools.js";
import AgentBasicInfo from "./components/AgentBasicInfo.vue";
import AgentModelConfig from "./components/AgentModelConfig.vue";
import AgentPromptEditor from "./components/AgentPromptEditor.vue";
import AgentToolsPanel from "./components/AgentToolsPanel.vue";
import AgentAdvancedConfig from "./components/AgentAdvancedConfig.vue";
import AgentFormFooter from "./components/AgentFormFooter.vue";

const route = useRoute();
const router = useRouter();
const agentId = computed(() => route.params.agentId);
const isNew = computed(() => agentId.value === "new");
const agent = ref(null);
const loading = ref(false);
const uploading = ref(false);
const fileInput = ref(null);
const step = ref(1);

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
  enable_knowledge_base: true,
  tools: [],
  compression_enabled: false,
  compression_threshold: 10000,
  compression_keep_recent: 3,
  compression_prompt: "",
  compression_template: "",
  tts_enabled: false,
  skills_config: {},
  phase_tool_config: {},
  knowledge_sources: [],
});

// SOP phase tool config helpers
const sopPhases = [
  { key: "1", label: "阶段 1：需求分析与用例设计", icon: "📋" },
  { key: "2", label: "阶段 2：元素准备", icon: "🔍" },
  { key: "3", label: "阶段 3：用例创建与调试", icon: "✏️" },
  { key: "4", label: "阶段 4：任务执行", icon: "▶️" },
];

function phaseToolEnabled(phase, toolName) {
  const cfg = form.value.phase_tool_config || {};
  const phaseTools = cfg[phase];
  if (!phaseTools || !phaseTools.length) return true; // not configured = all enabled
  return phaseTools.includes(toolName);
}

function togglePhaseTool(phase, toolName) {
  const cfg = { ...(form.value.phase_tool_config || {}) };
  let phaseTools = [...(cfg[phase] || [])];

  // First click on a phase: initialize with all tools minus this one
  if (!phaseTools.length) {
    phaseTools = availablePlatformTools.value.map((t) => t.name);
  }

  if (phaseTools.includes(toolName)) {
    phaseTools = phaseTools.filter((n) => n !== toolName);
  } else {
    phaseTools.push(toolName);
  }

  // Normalize: if all tools are selected, clear to empty (all enabled)
  const allNames = new Set(availablePlatformTools.value.map((t) => t.name));
  const selected = new Set(phaseTools);
  if (
    allNames.size === selected.size &&
    [...allNames].every((n) => selected.has(n))
  ) {
    delete cfg[phase];
  } else {
    cfg[phase] = phaseTools;
  }

  form.value.phase_tool_config = cfg;
}

function selectAllPhaseTools(phase) {
  const cfg = { ...(form.value.phase_tool_config || {}) };
  delete cfg[phase];
  form.value.phase_tool_config = cfg;
}

function deselectAllPhaseTools(phase) {
  const cfg = { ...(form.value.phase_tool_config || {}) };
  cfg[phase] = [];
  form.value.phase_tool_config = cfg;
}

const phaseToolConfigEnabled = ref(false);

function onTogglePhaseTool({ phase, name }) { togglePhaseTool(phase, name) }

const configPreviewHtml = computed(() => highlightJson(mcpForm.config_json))

onMounted(async () => {
  // Always load available platform tools list, skills, and knowledge docs
  await loadPlatformTools();
  await loadAvailableSkills();
  await loadKnowledgeDocs();
  await loadAgentTools();

  if (!isNew.value) {
    loading.value = true;
    try {
      const { data } = await getAgentDetail(agentId.value);
      if (data.ok) {
        // Restore selected platform tools from agent detail
        const allTools = data.agent.tools || [];
        const platformNames = allTools
          .filter((t) => t.tool_type === "platform" && t.enabled)
          .map((t) => t.name);
        selectedPlatformTools.value = new Set(platformNames);
        // Don't populate form.tools from API — MCP tools loaded via loadAgentTools()
        form.value = { ...form.value, ...data.agent, tools: [] };
        agent.value = data.agent;
        // Show phase config panel if agent already has phase_tool_config set
        const ptc = data.agent.phase_tool_config || {};
        if (Object.keys(ptc).length > 0) phaseToolConfigEnabled.value = true;
      }
    } catch (err) { console.error('Failed to load agent detail:', err) }
    loading.value = false;
  } else {
    // New agent: pre-fill default system prompt template
    await loadDefaultPrompt();
  }
});

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
	  availablePlatformTools, selectedPlatformTools, loadingPlatformTools,
	  loadPlatformTools, togglePlatformTool, isPlatformToolSelected,
	  availableSkills, loadingSkills,
	  loadAvailableSkills, isSkillEnabled, toggleSkill,
	  selectAllSkills, deselectAllSkills,
	  knowledgeDocs, loadingDocs,
	  loadKnowledgeDocs, isDocEnabled, toggleDoc, selectAllDocs, deselectAllDocs,
	  mcpTools, mcpDialogVisible, mcpDialogMode, mcpForm, mcpJsonError,
	  mcpTestingId, mcpTestResults,
	  loadAgentTools, openMcpDialog, saveMcpTool, testMcp, toggleMcp,
	  removeMcpApi, removeMcpLocal,
	  skills, skillUploading, skillFolderInput, removeSkill, formatSkillSize,
	  platformToolSelectedCount, wsSkillEnabledCount, kbDocSelectedCount,
	  mcpCount, customSkillCount,
	} = tools

	function highlightJson(raw) {
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

	function triggerSkillUpload() { skillFolderInput.value?.click() }
	async function handleSkillFolderChange(e) {
	  const files = Array.from(e.target.files || [])
	  if (!files.length) return
	  await tools.uploadSkill(files)
	  e.target.value = ''
	}

	// Step 4 collapse panel — default expand memory + platform
	const memoryToolActive = ref(["memory", "platform"])

// Load default system prompt template
const loadingDefaultPrompt = ref(false);
async function loadDefaultPrompt() {
  loadingDefaultPrompt.value = true;
  try {
    const data = await fetchDefaultPrompt();
    if (data.ok && data.template) form.value.system_prompt = data.template;
  } catch (err) { console.error('Failed to load default prompt:', err) }
  loadingDefaultPrompt.value = false;
}

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
    const { data } = await apiDetectModels({
      model_provider: form.value.model_provider,
      api_key: form.value.api_key,
      base_url: form.value.base_url,
    });
    if (data.ok) {
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

const stepLabels = ["基本信息", "模型配置", "提示词", "记忆工具", "高级"];

function goToStep(n) {
  if (n >= 1 && n <= stepLabels.length) step.value = n;
}

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
      const { data } = await uploadAvatar( {
        image: reader.result,
      });
      if (data.ok) form.value.avatar = data.url;
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
  // If phase tool config switch is off, clear the config so backend
  // doesn't apply phase filtering (backward compatible: all tools injected).
  if (!phaseToolConfigEnabled.value) {
    payload.phase_tool_config = {};
  }
  const url = isNew.value
    ? "/ai/agents/create"
    : `/ai/agents/${agentId.value}/update`;
  try {
    const { data } = await saveAgent(url, payload);
    if (data.ok) {
      ElMessage.success("保存成功");
      router.push("/ai-assistant");
    } else {
      ElMessage.error(data.error || "保存失败");
    }
  } catch (err) {
    const errors = err.response?.data?.errors;
    const msg =
      err.response?.data?.error ||
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
          ? '配置一个全新的 AI 智能体，分 5 步完成设置'
          : agent?.name
            ? `编辑「${agent.name}」— 所有配置项已展开，修改后直接保存`
            : '所有配置项已展开，修改后直接保存'
      "
      icon="settings"
      icon-gradient="linear-gradient(135deg,#5EEAD4,#14b8a6)"
    />

    <div class="doc-body agent-body">
      <!-- Back button -->
      <button class="back-btn" @click="router.push('/ai-assistant')">
        <IconArrowLeft :size="18" />
        <span>返回智能体列表</span>
      </button>

      <!-- Steps bar -->
      <div v-if="isNew" class="doc-section steps-section">
        <el-steps :active="step - 1" finish-status="success" align-center>
          <el-step v-for="(label, i) in stepLabels" :key="i" :title="label"
            class="clickable-step" @click="goToStep(i + 1)" />
        </el-steps>
      </div>

      <AgentBasicInfo :form="form" :is-new="isNew" :uploading="uploading" :step="step"
        @trigger-upload="triggerUpload" @avatar-upload="handleAvatarUpload" />

      <AgentModelConfig :form="form" :is-new="isNew" :step="step"
        :providers="providers" :available-models="availableModels"
        :detected-models="detectedModels" :detecting-models="detectingModels"
        @provider-change="onProviderChange" @detect-models="detectModels" />

      <AgentPromptEditor :form="form" :is-new="isNew" :step="step"
        @load-default-prompt="loadDefaultPrompt" />

      <AgentToolsPanel :form="form" :is-new="isNew" :step="step"
        :memory-modes="memoryModes" :ltm-modes="ltmModes"
        :available-platform-tools="availablePlatformTools" :loading-platform-tools="loadingPlatformTools"
        :selected-platform-tools="selectedPlatformTools" :platform-tool-selected-count="platformToolSelectedCount"
        :available-skills="availableSkills" :loading-skills="loadingSkills"
        :enabled-skills="enabledSkills" :ws-skill-enabled-count="wsSkillEnabledCount"
        :knowledge-docs="knowledgeDocs" :loading-docs="loadingDocs"
        :enabled-doc-ids="enabledDocIds" :kb-doc-selected-count="kbDocSelectedCount"
        :sop-phases="sopPhases" :phase-tool-config-enabled="phaseToolConfigEnabled"
        :mcp-tools="mcpTools" :skills="skills" :mcp-test-results="mcpTestResults"
        :mcp-testing-id="mcpTestingId" :mcp-count="mcpCount" :custom-skill-count="customSkillCount"
        :skill-uploading="skillUploading"
        :mcp-dialog-visible="mcpDialogVisible" :mcp-dialog-mode="mcpDialogMode"
        :mcp-form="mcpForm" :mcp-json-error="mcpJsonError" :config-preview="configPreviewHtml"
        @toggle-platform-tool="togglePlatformTool" @toggle-skill="toggleSkill"
        @toggle-doc="toggleDoc" @toggle-phase-tool="onTogglePhaseTool"
        @select-all-skills="selectAllSkills" @deselect-all-skills="deselectAllSkills"
        @select-all-docs="selectAllDocs" @deselect-all-docs="deselectAllDocs"
        @select-all-phase="selectAllPhaseTools" @deselect-all-phase="deselectAllPhaseTools"
        @open-mcp-dialog="openMcpDialog" @save-mcp-tool="saveMcpTool" @close-mcp-dialog="mcpDialogVisible=false"
        @test-mcp="testMcp" @toggle-mcp="toggleMcp"
        @remove-mcp-api="removeMcpApi" @remove-mcp-local="removeMcpLocal"
        @trigger-skill-upload="triggerSkillUpload" @remove-skill="removeSkill"
        @update:phase-tool-config-enabled="phaseToolConfigEnabled=$event"
        @update:mcp-dialog-visible="mcpDialogVisible=$event" />

      <AgentAdvancedConfig :form="form" :is-new="isNew" :step="step" />

      <AgentFormFooter :is-new="isNew" :step="step"
        @save="save" @prev-step="step--" @next-step="step++" />
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

/* ── Steps bar ── */
.steps-section { padding: 24px 32px; flex-shrink: 0; }
.steps-section :deep(.clickable-step) { cursor: pointer; }
.steps-section :deep(.clickable-step .el-step__title),
.steps-section :deep(.clickable-step .el-step__icon) { cursor: pointer; }
.steps-section :deep(.clickable-step:hover .el-step__title) { color: var(--ai-teal); }

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

