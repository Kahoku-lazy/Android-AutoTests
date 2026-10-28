<script setup>
import { ref, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getAgentDetail, saveAgent } from "./api/agents"
import { formatApiError } from "@/shared/api-client"
import { ElMessage } from "element-plus"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import { ROUTE_AI_ASSISTANT } from "./constants"
import AgentBasicInfo from "./components/AgentBasicInfo.vue"
import AgentFormFooter from "./components/AgentFormFooter.vue"

const route = useRoute()
const router = useRouter()
const agentId = computed(() => route.params.agentId)
const isNew = computed(() => agentId.value === "new")
const agent = ref(null)
const loading = ref(false)
const loadError = ref("")

// 配置页只维护基本信息；模型/线路由后台维护，执行链仍读 route_configs。
// 头像固定为内置图标，不参与表单与保存。
const form = ref({
  name: "",
  tags: "",
  description: "",
})

async function loadAgentDetail() {
  loadError.value = ""
  if (isNew.value) return
  loading.value = true
  try {
    const data = await getAgentDetail(agentId.value)
    if (data?.status && data.data?.agent) {
      const payload = data.data.agent
      const routeConfig =
        payload.route_configs?.device_control || payload.route_configs?.case_authoring || {}
      form.value = {
        name: routeConfig.name || payload.name || "",
        tags: payload.tags || "",
        description: payload.description || "",
      }
      agent.value = payload
    }
  } catch (err) {
    loadError.value = "加载智能体详情失败，请检查网络连接"
    console.error("Failed to load agent detail:", err)
  }
  loading.value = false
}

onMounted(() => {
  loadAgentDetail()
})

async function save() {
  const payload = {
    name: (form.value.name || "").trim() || (isNew.value ? "新智能体" : "平台小助手"),
    tags: form.value.tags || "",
    description: form.value.description || "",
  }
  try {
    const data = await saveAgent(isNew.value, agentId.value, payload)
    if (data.status) {
      ElMessage.success("保存成功")
      router.push(ROUTE_AI_ASSISTANT)
    } else {
      ElMessage.error(data.message || "保存失败")
    }
  } catch (err) {
    ElMessage.error("保存失败: " + formatApiError(err))
  }
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench" v-loading="loading">
    <WorkbenchHeader
      :title="isNew ? '新建智能体' : '编辑智能体'"
      :subtitle="
        isNew ? '配置一个全新的 AI 智能体' : agent?.name ? `编辑「${agent.name}」` : '编辑智能体'
      "
      icon="settings"
      icon-gradient="linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover))"
    />

    <div class="doc-body agent-body">
      <WorkbenchCrumbs
        back-to="/ai-assistant/agents"
        back-label="返回智能体列表"
        :items="[
          { label: '平台小助手', to: '/ai-assistant/agents' },
          { label: isNew ? '新建智能体' : agent?.name || '编辑智能体' },
        ]"
      />
      <ErrorState v-if="loadError" :message="loadError" @retry="loadAgentDetail" />
      <template v-else>
        <AgentBasicInfo :form="form" :task-kind="agent?.task_kind" />
        <AgentFormFooter :is-new="isNew" @save="save" />
      </template>
    </div>
  </div>
</template>

<style scoped>
/* ── Page layout ── */
.agent-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 40px;
  overflow-x: hidden;
  overflow-y: auto;
}

/* ── Section badge ── */
:deep(.section-num) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--app-radius-md);
  background: linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover));
  color: var(--app-bg-card);
  font-size: var(--app-size-md);
  font-weight: 700;
  box-shadow: var(--app-shadow-sm);
}
</style>
