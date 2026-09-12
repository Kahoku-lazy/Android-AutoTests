<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getAgentDetail, uploadAvatar, saveAgent, testAgent } from "./api/agents";
import { formatApiError } from "@/shared/api-client";
import { ElMessage, ElMessageBox } from "element-plus";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import { IconArrowLeft } from "@/shared/icons/index";
import { ROUTE_AI_ASSISTANT } from "./constants";
import AgentBasicInfo from "./components/AgentBasicInfo.vue";
import AgentRouteConfig from "./components/AgentRouteConfig.vue";
import AgentFormFooter from "./components/AgentFormFooter.vue";

const route = useRoute();
const router = useRouter();
const agentId = computed(() => route.params.agentId);
const isNew = computed(() => agentId.value === "new");
const activeRoute = computed(() => {
  const r = route.query.route;
  return r === "device_control" ? r : null;
});
const agent = ref(null);
const loading = ref(false);
const loadError = ref("");
const uploading = ref(false);
const fileInput = ref(null);
const uploadTargetRoute = ref(null);
const testing = ref(false);
const testResults = ref(null);
const ROLE_LABELS = { planner: "规划模型", executor: "执行模型", verifier: "校验模型" };

const form = ref({
  name: "",
  avatar: "🤖",
  tags: "",
  description: "",
  model_provider: "dashscope",
  model_name: "qwen-max",
  vision_model_name: "",
  strong_model_name: "",
  strong_enabled: false,
  api_key: "",
  base_url: "",
  enable_knowledge_base: false,
  enable_workspace_tools: false,
  enable_business_tools: false,
  enable_mcp_tools: false,
  enable_skills: false,
  tools: [],
  skills_config: {},
  knowledge_sources: {},
  max_loops: 3,
  route_configs: {
    device_control: { name: "", avatar: "📱", planner: {}, executor: {}, verifier: {} },
  },
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
    if (!isNew.value) {
      const data = await getAgentDetail(agentId.value)
      if (data?.status && data.data?.agent) {
        const agentPayload = data.data.agent;
        form.value = { ...form.value, ...agentPayload, tools: [] };
        form.value.route_configs = {
          device_control: { name: "", avatar: "📱", planner: {}, executor: {}, verifier: {}, ...(agentPayload.route_configs?.device_control || {}) },
        };
        form.value.max_loops = agentPayload.max_loops ?? 3;
        agent.value = agentPayload;
      }
    }
  } catch (err) {
    if (!isNew.value) {
      loadError.value = "加载智能体详情失败，请检查网络连接";
      console.error('Failed to load agent detail:', err);
    }
  }
  if (!isNew.value) loading.value = false;
}

onMounted(() => { loadAgentDetail() });

function triggerUpload(routeKey) {
  uploadTargetRoute.value = routeKey;
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
      if (data.status) {
        const url = data.data?.url || '';
        const routeKey = uploadTargetRoute.value || activeRoute.value;
        if (routeKey && form.value.route_configs[routeKey]) {
          form.value.route_configs[routeKey].avatar = url;
        } else {
          form.value.avatar = url;
        }
      }
    } catch (err) { console.error('Failed to upload avatar:', err); ElMessage.error('头像上传失败，请稍后重试') }
    uploading.value = false;
    uploadTargetRoute.value = null;
  };
  reader.readAsDataURL(file);
}

async function save() {
  const payload = { ...form.value };
  if (!payload.name?.trim()) {
    const routeKey = activeRoute.value;
    const routeName = routeKey
      ? payload.route_configs?.[routeKey]?.name
      : payload.route_configs?.device_control?.name;
    payload.name = (routeName || '').trim() || '平台小助手';
  }
  // 工具/知识库配置已移到 AI 工具箱 / 知识库页（platform-config），此处不随智能体提交
  for (const k of [
    'tools', 'enable_workspace_tools', 'enable_business_tools',
    'enable_mcp_tools', 'enable_skills', 'enable_knowledge_base',
    'skills_config', 'knowledge_sources',
  ]) {
    delete payload[k];
  }
  try {
    const data = await saveAgent(isNew.value, agentId.value, payload);
    if (data.status) {
      ElMessage.success("保存成功");
      router.push(ROUTE_AI_ASSISTANT);
    } else {
      ElMessage.error(data.message || "保存失败");
    }
  } catch (err) {
    ElMessage.error("保存失败: " + formatApiError(err));
  }
}

async function testConnection() {
  if (testing.value) return;
  testing.value = true;
  testResults.value = null;
  try {
    const data = await testAgent(agentId.value, { route: activeRoute.value });
    if (data.status && data.data) {
      if (data.data.results) testResults.value = data.data.results;
      const connected = data.data.connected;
      if (connected) ElMessage.success("连接成功");
      else ElMessage.warning("存在未连通的模型");
    } else {
      ElMessage.error(data.message || "校验失败");
    }
  } catch (err) {
    ElMessage.error("校验请求失败，请检查网络连接");
  }
  testing.value = false;
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench" v-loading="loading">
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
      icon-gradient="linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover))"
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
      <AgentBasicInfo
        v-if="activeRoute"
        :form="form.route_configs[activeRoute]"
        :uploading="uploading && uploadTargetRoute === activeRoute"
        route-mode
        @trigger-upload="triggerUpload(activeRoute)"
      />
      <AgentBasicInfo v-if="!activeRoute" :form="form" :is-new="isNew" />

      <section class="doc-section step-panel">
        <div class="section-title"><span class="section-num">🔄</span>循环次数</div>
        <el-form label-width="110px" class="agent-form">
          <el-form-item label="max_loops">
            <el-input-number v-model="form.max_loops" :min="1" :max="10" />
          </el-form-item>
        </el-form>
      </section>

      <template v-if="!activeRoute || activeRoute === 'device_control'">
        <AgentBasicInfo
          v-if="!activeRoute"
          :form="form.route_configs.device_control"
          :uploading="uploading && uploadTargetRoute === 'device_control'"
          route-mode
          @trigger-upload="triggerUpload('device_control')"
        />
        <AgentRouteConfig label="控制设备 Device Control" v-model="form.route_configs.device_control" />
      </template>


      <section class="doc-section step-panel">
        <div class="section-title"><span class="section-num">✅</span>模型校验</div>
        <el-button :loading="testing" :disabled="isNew" @click="testConnection">校验模型连接</el-button>
        <div v-if="testResults" class="test-results">
          <div v-for="(r, role) in testResults" :key="role" class="test-row">
            <span class="test-role">{{ ROLE_LABELS[role] || role }}</span>
            <span class="test-state" :class="r.connected ? 'ok' : 'fail'">
              {{ r.connected ? '✓ 已连通' : '✗ ' + (r.message || '未连通') }}
            </span>
          </div>
        </div>
      </section>

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
  display: inline-flex; align-items: center; gap: var(--app-space-sm); padding: 10px 20px;
  border: 2px solid var(--ai-teal); border-radius: 12px; background: var(--ai-teal-bg);
  color: var(--ai-teal-text); font-size: var(--app-size-md); font-weight: 700; font-family: inherit;
  cursor: pointer; transition: all 0.2s ease; align-self: flex-start;
}
.back-btn:hover { background: var(--ai-teal); color: var(--app-bg-card); box-shadow: var(--app-shadow-md); transform: translateY(-1px); }

/* ── Shared step panel（:deep 才能作用到子组件标题） ── */
:deep(.step-panel) { padding: 28px var(--app-space-xl); }
:deep(.section-title) {
  display: flex; align-items: center; gap: 12px; font-size: var(--app-size-lg); font-weight: 700;
  color: var(--ai-ink-soft); margin-bottom: var(--app-space-lg); padding-bottom: 14px; border-bottom: 2px solid var(--ai-bg-subtle);
}
:deep(.section-num) {
  display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;
  border-radius: 10px; background: linear-gradient(135deg,var(--ai-teal),var(--ai-teal-hover));
  color: var(--app-bg-card); font-size: var(--app-size-md); font-weight: 700; box-shadow: var(--app-shadow-sm);
}
.agent-form :deep(.el-form-item__label) { font-size: var(--app-size-md); font-weight: 600; color: var(--ai-ink-subtle); }
.agent-form :deep(.el-input__wrapper),
.agent-form :deep(.el-textarea__inner) { border-radius: 10px; font-size: var(--app-size-md); }
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
.test-results { display: flex; flex-direction: column; gap: var(--app-space-sm); margin-top: var(--app-space-md); }
.test-row { display: flex; align-items: center; gap: 12px; font-size: var(--app-size-sm); }
.test-role { font-weight: 700; color: var(--ai-ink-muted); min-width: 72px; }
.test-state.ok { color: var(--ai-teal-text); font-weight: 700; }
.test-state.fail { color: var(--el-color-danger); font-weight: 700; }
</style>

