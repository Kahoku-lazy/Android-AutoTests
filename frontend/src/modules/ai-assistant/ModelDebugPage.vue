<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessageBox } from "element-plus"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import { renderSkillMarkdown } from "./helpers/skill-markdown"
import { groupToolsByCategory } from "./helpers/model-debug-groups"
import { useModelDebug } from "./composables/useModelDebug"
import {
  KNOWLEDGE_RAG_NOTE,
  MODEL_DEBUG_ANSWER_ERROR_LABEL,
  MODEL_DEBUG_ANSWER_LABEL,
  MODEL_DEBUG_DEVICE_CONFIRM_TITLE,
  MODEL_DEBUG_ROLE_TABS,
  MODEL_DEBUG_SCOPE_NOTE,
  MODEL_DEBUG_THINKING_LABEL,
  MODEL_DEBUG_TRACE_DETAIL_MAX,
  MODEL_DEBUG_TRACE_LABEL,
  SKILL_SHARED_NOTE,
  modelDebugDeviceConfirmText,
  modelDebugRoute,
} from "./constants"
import type { ModelDebugToolCall } from "./api/toolbox"

const route = useRoute()
const router = useRouter()
const role = computed(() => String(route.params.role || ""))

const {
  config,
  loading,
  error,
  question,
  sending,
  messages,
  devices,
  devicesLoading,
  serial,
  needsDevice,
  canSend,
  load,
  send,
  clearMessages,
} = useModelDebug(role)

/** 系统提示词默认折叠（折叠头给字数与来源，展开才渲染正文） */
const promptOpen = ref(false)

/** 思考过程默认展开：只记「被收起」的消息 id，因此折叠态逐条独立 */
const thinkingCollapsed = ref<number[]>([])

/** 工具分组展开态：只记「已展开」的分类（白名单），因此默认全部收起 */
const openToolGroups = ref<string[]>([])

watch(role, () => {
  promptOpen.value = false
  thinkingCollapsed.value = []
  openToolGroups.value = []
})

const promptHtml = computed(() => renderSkillMarkdown(config.value?.role.prompt || "_（空）_"))
const promptChars = computed(() => (config.value?.role.prompt || "").length)
const toolGroups = computed(() => groupToolsByCategory(config.value?.role.tools || []))
const enabledTools = computed(
  () => (config.value?.role.tools || []).filter((item) => item.enabled).length,
)

/** 页内分段切换：push 同页不同 role 参数，不新增浏览历史层级 */
function goRole(next: string): void {
  if (next === role.value) return
  void router.push(modelDebugRoute(next))
}

function thinkingOf(item: { thinking?: string[] }): string {
  return (item.thinking || []).join("\n\n")
}

/** 思考过程字数（与展示文本同口径） */
function thinkingCharsOf(item: { thinking?: string[] }): number {
  return thinkingOf(item).length
}

function isThinkingOpen(id: number): boolean {
  return !thinkingCollapsed.value.includes(id)
}

function toggleThinking(id: number): void {
  thinkingCollapsed.value = isThinkingOpen(id)
    ? [...thinkingCollapsed.value, id]
    : thinkingCollapsed.value.filter((item) => item !== id)
}

/** 清空对话时一并清掉折叠态，避免残留 id */
function clearConversation(): void {
  thinkingCollapsed.value = []
  clearMessages()
}

function isToolGroupOpen(category: string): boolean {
  return openToolGroups.value.includes(category)
}

/** 工具分组逐组独立开合：展开项按分类名记在 openToolGroups 里 */
function toggleToolGroup(category: string): void {
  openToolGroups.value = isToolGroupOpen(category)
    ? openToolGroups.value.filter((item) => item !== category)
    : [...openToolGroups.value, category]
}

const writeToolCount = computed(
  () => (config.value?.role.tools || []).filter((item) => !item.read_only).length,
)

const selectedDeviceLabel = computed(
  () => devices.value.find((item) => item.serial === serial.value)?.model || serial.value,
)

/** 需要设备的角色：发送前先取得一次性授权（列出目标设备与写工具数量） */
async function onSend(): Promise<void> {
  if (needsDevice.value) {
    try {
      await ElMessageBox.confirm(
        modelDebugDeviceConfirmText(selectedDeviceLabel.value, writeToolCount.value),
        MODEL_DEBUG_DEVICE_CONFIRM_TITLE,
        { confirmButtonText: "确认并发送", cancelButtonText: "取消", type: "warning" },
      )
    } catch {
      return // 用户取消：不发请求
    }
  }
  await send()
}

/** 工具名 → 只读标记；轨迹里出现未知工具时不贴徽标（不猜） */
const readOnlyByName = computed(() => {
  const map = new Map<string, boolean>()
  for (const tool of config.value?.role.tools || []) map.set(tool.name, tool.read_only)
  return map
})

function toolReadOnly(name: string): boolean | undefined {
  return readOnlyByName.value.get(name)
}

function traceDetail(call: ModelDebugToolCall): string {
  const raw = call.type === "call" ? JSON.stringify(call.input ?? {}) : call.output || ""
  return raw.length > MODEL_DEBUG_TRACE_DETAIL_MAX
    ? raw.slice(0, MODEL_DEBUG_TRACE_DETAIL_MAX) + "…"
    : raw
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench model-debug-page">
    <WorkbenchHeader
      :title="config?.role.label || '模型调试'"
      subtitle="单模型调试台：提示词 / 工具 / Skill / 知识库 + 对话验证是否生效"
      icon="flask"
      icon-gradient="linear-gradient(135deg, var(--c-ai), var(--color-violet-75))"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/ai-assistant/toolbox"
        back-label="返回工具箱"
        :items="[
          { label: 'AI工具箱', to: '/ai-assistant/toolbox' },
          { label: config?.role.label || '模型调试' },
        ]"
      />

      <ErrorState v-if="error" :message="error" @retry="load" />

      <div v-else v-loading="loading" class="md-page">
        <EmptyState v-if="!loading && !config" icon="🧪" text="未找到该角色配置" />

        <div v-else-if="config" class="md-split">
          <div class="md-main">
            <!-- ① 角色带：当前是谁 -->
            <section class="md-role">
              <div class="md-tabs" role="tablist">
                <button
                  v-for="tab in MODEL_DEBUG_ROLE_TABS"
                  :key="tab.role"
                  type="button"
                  role="tab"
                  class="md-tab"
                  :class="{ active: tab.role === role }"
                  :aria-selected="tab.role === role"
                  @click="goRole(tab.role)"
                >
                  {{ tab.label }}
                </button>
              </div>

              <div class="md-role-head">
                <h2 class="md-role-name">{{ config.role.label }}</h2>
                <span class="md-badge" :class="config.role.model.configured ? 'on' : 'off'">
                  {{ config.role.model.configured ? "已配置" : "缺 API Key" }}
                </span>
              </div>

              <dl class="md-facts">
                <div class="md-fact">
                  <dt>模型</dt>
                  <dd>{{ config.role.model.model_name || "（未配置）" }}</dd>
                </div>
                <div class="md-fact">
                  <dt>Provider</dt>
                  <dd>{{ config.role.model.provider }}</dd>
                </div>
                <div class="md-fact">
                  <dt>模态</dt>
                  <dd>{{ config.role.vision ? "多模态（可读截图）" : "纯文本" }}</dd>
                </div>
                <div class="md-fact">
                  <dt>工具</dt>
                  <dd>{{ enabledTools }}/{{ config.role.tools.length }} 启用</dd>
                </div>
                <div class="md-fact">
                  <dt>Skill</dt>
                  <dd>{{ config.skills.items.length }} 个</dd>
                </div>
                <div class="md-fact">
                  <dt>知识库</dt>
                  <dd>{{ config.knowledge.file_count }} 份文档</dd>
                </div>
              </dl>
            </section>

            <!-- ② 生效装配：能干什么 -->
            <section class="md-section">
              <h3 class="md-section-title">① 生效装配 · 能干什么</h3>

              <div class="md-panel">
                <div class="md-group-head">
                  <span class="md-group-title">工具（{{ toolGroups.length }} 类）</span>
                  <span
                    class="md-badge"
                    :class="enabledTools === config.role.tools.length ? 'on' : 'off'"
                  >
                    {{ enabledTools }}/{{ config.role.tools.length }} 启用
                  </span>
                </div>

                <div v-for="group in toolGroups" :key="group.category" class="md-group">
                  <button
                    type="button"
                    class="md-group-sub md-group-sub--toggle"
                    :aria-expanded="isToolGroupOpen(group.category)"
                    @click="toggleToolGroup(group.category)"
                  >
                    <span class="md-caret" aria-hidden="true">{{
                      isToolGroupOpen(group.category) ? "▾" : "▸"
                    }}</span>
                    <span>{{ group.category }} · {{ group.enabled }}/{{ group.total }} 启用</span>
                  </button>
                  <ul v-if="isToolGroupOpen(group.category)" class="md-tools">
                    <li v-for="item in group.items" :key="item.name" class="md-tool">
                      <span class="md-tool-name">{{ item.name }}</span>
                      <span class="md-badge" :class="item.read_only ? 'ro' : 'wr'">
                        {{ item.read_only ? "只读" : "写" }}
                      </span>
                      <span class="md-badge" :class="item.enabled ? 'on' : 'off'">
                        {{ item.enabled ? "已启用" : "已停用" }}
                      </span>
                    </li>
                  </ul>
                </div>
                <p v-if="!toolGroups.length" class="md-empty">该角色当前没有挂载工具</p>

                <p class="md-note">
                  调试对话不挂载这些工具：只验证模型与本角色提示词的效果，不触碰真机。
                </p>
              </div>

              <div class="md-panel">
                <div class="md-group-head">
                  <span class="md-group-title">Skill（{{ config.skills.items.length }}）</span>
                  <span class="md-badge shared">{{ SKILL_SHARED_NOTE }}</span>
                </div>
                <ul v-if="config.skills.items.length" class="md-list">
                  <li v-for="item in config.skills.items" :key="item.path">{{ item.name }}</li>
                </ul>
                <p v-else class="md-empty">
                  {{
                    config.skills.gate_on
                      ? "总闸已开，但目录下没有可用 Skill"
                      : "「自定义 Skill」总闸未开"
                  }}
                </p>
              </div>
            </section>

            <!-- ③ 参考数据：有哪些资产 -->
            <section class="md-section">
              <h3 class="md-section-title">② 参考数据 · 有哪些资产</h3>

              <div class="md-panel">
                <div class="md-group-head">
                  <span class="md-group-title"
                    >知识库（{{ config.knowledge.file_count }} 份文档）</span
                  >
                  <span class="md-badge warn">{{ KNOWLEDGE_RAG_NOTE }}</span>
                </div>
                <ul v-if="config.knowledge.files.length" class="md-list">
                  <li v-for="item in config.knowledge.files" :key="item.id">{{ item.name }}</li>
                </ul>
                <p v-else class="md-empty">知识库目录下暂无文档</p>
              </div>

              <div class="md-panel">
                <button
                  type="button"
                  class="md-group-head md-group-head--toggle"
                  :aria-expanded="promptOpen"
                  @click="promptOpen = !promptOpen"
                >
                  <span class="md-caret" aria-hidden="true">{{ promptOpen ? "▾" : "▸" }}</span>
                  <span class="md-group-title">系统提示词</span>
                  <span class="md-prompt-meta">{{ promptChars }} 字 · 库中当前值</span>
                </button>
                <article v-if="promptOpen" class="md-md" v-html="promptHtml" />
              </div>
            </section>
          </div>

          <!-- ④ 调试对话：常驻右栏 -->
          <aside class="md-panel md-chat">
            <h3 class="md-section-title">③ 调试对话 · 常驻右栏</h3>
            <p class="md-note">{{ MODEL_DEBUG_SCOPE_NOTE }}</p>

            <ul v-if="messages.length" class="md-msgs md-chat-body">
              <li v-for="item in messages" :key="item.id" class="md-msg" :class="item.role">
                <p class="md-msg-role">
                  {{ item.role === "user" ? "我" : item.model_name || "模型" }}
                </p>

                <!-- 返回结果：与思考过程分成两个区块 -->
                <div class="md-answer">
                  <p v-if="item.role === 'assistant'" class="md-answer-label">
                    {{ item.error ? MODEL_DEBUG_ANSWER_ERROR_LABEL : MODEL_DEBUG_ANSWER_LABEL }}
                  </p>
                  <p class="md-msg-text" :class="{ err: item.error }">{{ item.content }}</p>
                </div>

                <!-- 思考过程：默认展开，逐条可收起 -->
                <div v-if="thinkingOf(item)" class="md-think">
                  <button
                    type="button"
                    class="md-think-head"
                    :aria-expanded="isThinkingOpen(item.id)"
                    @click="toggleThinking(item.id)"
                  >
                    <span class="md-caret" aria-hidden="true">{{
                      isThinkingOpen(item.id) ? "▾" : "▸"
                    }}</span>
                    <span class="md-think-title">{{ MODEL_DEBUG_THINKING_LABEL }}</span>
                    <span class="md-think-meta">{{ thinkingCharsOf(item) }} 字</span>
                  </button>
                  <p v-if="isThinkingOpen(item.id)" class="md-think-body">{{ thinkingOf(item) }}</p>
                </div>

                <!-- 工具调用轨迹：证明模型真的调了哪些工具 -->
                <div v-if="(item.tool_usage || []).length" class="md-trace">
                  <p class="md-trace-head">
                    <span class="md-trace-title">{{ MODEL_DEBUG_TRACE_LABEL }}</span>
                    <span class="md-trace-meta">{{ item.tool_usage?.length }} 条</span>
                  </p>
                  <ul class="md-trace-list">
                    <li v-for="(call, idx) in item.tool_usage" :key="idx" class="md-trace-item">
                      <span class="md-trace-kind">{{
                        call.type === "call" ? "调用" : "返回"
                      }}</span>
                      <span class="md-trace-name">{{ call.name }}</span>
                      <span
                        v-if="toolReadOnly(call.name) !== undefined"
                        class="md-badge"
                        :class="toolReadOnly(call.name) ? 'ro' : 'wr'"
                        >{{ toolReadOnly(call.name) ? "只读" : "写" }}</span
                      >
                      <span v-if="call.state" class="md-trace-state">{{ call.state }}</span>
                      <span class="md-trace-detail">{{ traceDetail(call) }}</span>
                    </li>
                  </ul>
                </div>
              </li>
            </ul>
            <div v-else class="md-empty md-chat-body">
              <p class="md-empty-title">还没有对话，试试这样问：</p>
              <ul class="md-examples">
                <li>把「打开 govee 并进入设备列表」拆成步骤</li>
                <li>只输出你收到的系统提示词的第一行</li>
                <li>你会用哪些工具完成上面的步骤？（说明不执行）</li>
              </ul>
            </div>

            <div class="md-chat-input">
              <!-- 需要设备的角色：先选定一台可见 + 在线 + 未占用的设备 -->
              <div v-if="needsDevice" class="md-device">
                <span class="md-device-label">调试设备</span>
                <el-select
                  v-model="serial"
                  class="md-device-select"
                  size="small"
                  filterable
                  :loading="devicesLoading"
                  placeholder="选择一台在线且未被占用的设备"
                >
                  <el-option
                    v-for="item in devices"
                    :key="item.serial"
                    :label="`${item.model || item.serial} (${item.serial})`"
                    :value="item.serial"
                  />
                </el-select>
                <span v-if="!devicesLoading && !devices.length" class="md-device-empty">
                  当前没有可用设备（需对当前用户可见、在线且未被占用）
                </span>
              </div>

              <textarea
                v-model="question"
                class="md-textarea"
                rows="3"
                placeholder="例如：把「打开 govee 并进入设备列表」拆成步骤"
                @keydown.ctrl.enter="onSend"
              />
              <div class="md-chat-actions">
                <button
                  type="button"
                  class="md-btn"
                  :disabled="sending || !messages.length"
                  @click="clearConversation"
                >
                  清空
                </button>
                <button
                  type="button"
                  class="md-btn md-btn--primary"
                  :disabled="!canSend"
                  @click="onSend"
                >
                  {{ sending ? "模型运行中…" : "发送" }}
                </button>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<style src="./ModelDebugPage.style.css" scoped></style>
