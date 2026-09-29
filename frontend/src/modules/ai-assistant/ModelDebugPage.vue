<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessageBox } from "element-plus"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import StepLogCheck from "./components/StepLogCheck.vue"
import StepLogEvidence from "./components/StepLogEvidence.vue"
import { groupToolsByCategory } from "./helpers/model-debug-groups"
import { hasLogCheck } from "./helpers/task-detail"
import { useModelDebug } from "./composables/useModelDebug"
import { useModelDebugFolding } from "./composables/useModelDebugFolding"
import {
  MODEL_DEBUG_ANSWER_ERROR_LABEL,
  MODEL_DEBUG_ANSWER_LABEL,
  MODEL_DEBUG_ASSEMBLY_NOTE,
  MODEL_DEBUG_DEVICE_CONFIRM_TITLE,
  MODEL_DEBUG_DEVICE_EMPTY_NOTE,
  MODEL_DEBUG_DEVICE_LOADING_NOTE,
  MODEL_DEBUG_DEVICE_NEEDED_BADGE,
  MODEL_DEBUG_DEVICE_NOT_NEEDED_BADGE,
  MODEL_DEBUG_DEVICE_NOT_NEEDED_NOTE,
  MODEL_DEBUG_LAYER_TITLES,
  MODEL_DEBUG_LOG_ASSERTION_LABEL,
  MODEL_DEBUG_LOG_BASIS_LABEL,
  MODEL_DEBUG_ROLE_TABS,
  MODEL_DEBUG_SCOPE_NOTE,
  MODEL_DEBUG_SKILL_DIR_EMPTY_NOTE,
  MODEL_DEBUG_SKILL_DIR_TITLE,
  MODEL_DEBUG_SKILL_GATE_OFF_NOTE,
  MODEL_DEBUG_THINKING_LABEL,
  MODEL_DEBUG_TRACE_DETAIL_MAX,
  MODEL_DEBUG_TRACE_LABEL,
  SKILL_SHARED_NOTE,
  modelDebugDeviceConfirmText,
  modelDebugLogBasisText,
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

/** 折叠态（思考过程逐条独立 / 工具分组逐组独立，切角色重置）由 composable 持有 */
const {
  reset: resetFolding,
  thinkingOf,
  thinkingCharsOf,
  isThinkingOpen,
  toggleThinking,
  isToolGroupOpen,
  toggleToolGroup,
} = useModelDebugFolding(role)

const toolGroups = computed(() => groupToolsByCategory(config.value?.role.tools || []))
const enabledTools = computed(
  () => (config.value?.role.tools || []).filter((item) => item.enabled).length,
)

/** 页内分段切换：push 同页不同 role 参数，不新增浏览历史层级 */
function goRole(next: string): void {
  if (next === role.value) return
  void router.push(modelDebugRoute(next))
}

/** 清空对话时一并清掉折叠态，避免残留 id */
function clearConversation(): void {
  resetFolding()
  clearMessages()
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
      subtitle="单模型调试台：模型 / 工具 / Skill + 对话验证"
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
            <section class="md-role" data-testid="model-debug-role-band">
              <h3 class="md-section-title">{{ MODEL_DEBUG_LAYER_TITLES.role }}</h3>

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
              </dl>
            </section>

            <!-- ② 生效装配：能干什么 -->
            <section class="md-section">
              <h3 class="md-section-title">{{ MODEL_DEBUG_LAYER_TITLES.assembly }}</h3>

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

                <p class="md-note">{{ MODEL_DEBUG_ASSEMBLY_NOTE }}</p>
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
                      ? MODEL_DEBUG_SKILL_DIR_EMPTY_NOTE
                      : MODEL_DEBUG_SKILL_GATE_OFF_NOTE
                  }}
                </p>
              </div>
            </section>

            <!-- ③ 参考数据：有哪些资产（只读；设备与 Skill 目录） -->
            <section class="md-section" data-testid="model-debug-reference">
              <h3 class="md-section-title">{{ MODEL_DEBUG_LAYER_TITLES.reference }}</h3>

              <div class="md-panel">
                <div class="md-group-head">
                  <span class="md-group-title">设备</span>
                  <span class="md-badge">
                    {{
                      needsDevice
                        ? MODEL_DEBUG_DEVICE_NEEDED_BADGE
                        : MODEL_DEBUG_DEVICE_NOT_NEEDED_BADGE
                    }}
                  </span>
                </div>
                <ul
                  v-if="needsDevice && devices.length"
                  class="md-list"
                  data-testid="model-debug-ref-devices"
                >
                  <li v-for="item in devices" :key="item.serial">
                    {{ item.model || item.serial }}（{{ item.serial }}）
                  </li>
                </ul>
                <p v-else class="md-note" data-testid="model-debug-ref-device-note">
                  {{
                    !needsDevice
                      ? MODEL_DEBUG_DEVICE_NOT_NEEDED_NOTE
                      : devicesLoading
                        ? MODEL_DEBUG_DEVICE_LOADING_NOTE
                        : MODEL_DEBUG_DEVICE_EMPTY_NOTE
                  }}
                </p>
              </div>

              <div class="md-panel">
                <div class="md-group-head">
                  <span class="md-group-title">{{ MODEL_DEBUG_SKILL_DIR_TITLE }}</span>
                  <span class="md-badge">{{ config.skills.items.length }} 个</span>
                </div>
                <ul
                  v-if="config.skills.items.length"
                  class="md-list"
                  data-testid="model-debug-ref-skills"
                >
                  <li v-for="item in config.skills.items" :key="item.path">
                    {{ item.name }} — {{ item.path }}
                  </li>
                </ul>
                <p v-else class="md-empty">
                  {{
                    config.skills.gate_on
                      ? MODEL_DEBUG_SKILL_DIR_EMPTY_NOTE
                      : MODEL_DEBUG_SKILL_GATE_OFF_NOTE
                  }}
                </p>
              </div>
            </section>
          </div>

          <!-- ④ 调试对话：常驻右栏 -->
          <aside class="md-panel md-chat">
            <h3 class="md-section-title">{{ MODEL_DEBUG_LAYER_TITLES.chat }}</h3>
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

                <!-- 设备点击证据：点击前时间点 + 点击后截图路径（+ 该时间点后 5 秒日志） -->
                <StepLogCheck v-if="hasLogCheck(item.log_check)" :check="item.log_check" />

                <!-- 验收角色的日志证据（调试回溯）：基准说明 + 与任务详情同一份证据组件 -->
                <section
                  v-if="item.log_basis"
                  class="md-log-basis"
                  data-testid="model-debug-log-basis"
                >
                  <p class="md-log-basis__head">{{ MODEL_DEBUG_LOG_BASIS_LABEL }}</p>
                  <p class="md-log-basis__text">{{ modelDebugLogBasisText(item.log_basis) }}</p>
                  <p v-if="item.log_assertion_info" class="md-log-basis__text">
                    <span data-testid="model-debug-log-assertion-info">
                      {{ MODEL_DEBUG_LOG_ASSERTION_LABEL }}：{{ item.log_assertion_info }}
                    </span>
                  </p>
                </section>
                <StepLogEvidence v-if="item.log_evidence" :evidence="item.log_evidence" />

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
                  {{ MODEL_DEBUG_DEVICE_EMPTY_NOTE }}
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
