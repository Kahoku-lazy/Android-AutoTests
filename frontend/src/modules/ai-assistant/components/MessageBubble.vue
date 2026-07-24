<script setup>
import ThinkingBlock from "./ThinkingBlock.vue";
import ToolCallAppCard from "./ToolCallCard.vue";
import HintAppCard from "./HintCard.vue";
import { renderMarkdown } from "../composables/useMarkdown.js";

const props = defineProps({
  message: { type: Object, required: true },
  agentName: { type: String, default: "AI" },
  agentAvatar: { type: String, default: "" },
  avatarStyleFn: { type: Function, default: () => ({}) },
  avatarTextFn: { type: Function, default: () => "" },
  importingPrd: { type: Boolean, default: false },
  /** 流式等待中：在气泡内显示打字点，避免外层再叠一层 typing-row */
  typing: { type: Boolean, default: false },
});

const emit = defineEmits(["toggle-thinking", "import-prd"]);

function toggleThinking() {
  emit("toggle-thinking", props.message);
}

function reasonLabel(reason) {
  if (reason === "exceed_max_iters") return "⚠️ 达到最大迭代次数";
  if (reason === "stopped") return "⏹ 用户主动停止";
  if (reason === "error") return "❌ 异常终止";
  return reason;
}
</script>

<template>
  <div :class="['msg', message.role]">
    <div
      class="msg-avatar"
      :style="avatarStyleFn(message.role === 'assistant' ? agentAvatar : '')"
    >
      <span v-if="message.role === 'user'">👤</span>
      <template v-else>
        <span v-if="avatarTextFn(agentAvatar)">{{ avatarTextFn(agentAvatar) }}</span>
      </template>
    </div>
    <div class="msg-content">
      <div class="msg-author">
        {{ message.role === "user" ? "我" : agentName }}
        <span
          v-if="message.role === 'assistant' && message.flow"
          class="msg-flow-tag"
          :class="message.flow"
        >
          {{ message.flow === "sse" ? "⚡ SSE" : "⏳ Django" }}
        </span>
      </div>

      <ThinkingBlock
        v-if="message.role === 'assistant' && message.thinking"
        :thinking="message.thinking"
        :thinking-done="message.thinkingDone"
        :expanded="message.thinkingExpanded"
        @toggle="toggleThinking"
      />

      <ToolCallAppCard
        v-if="message.role === 'assistant' && message.toolFlow?.length"
        :tool-calls="message.toolFlow"
      />

      <HintAppCard
        v-if="message.role === 'assistant' && message.hint"
        :hint="message.hint"
        :importing="importingPrd"
        @import-prd="emit('import-prd', $event)"
      />

      <div
        v-if="typing && message.role === 'assistant' && !message.content"
        class="msg-text typing"
      >
        <span class="typing-label">AI正在思考中</span>
        <span class="typing-dots" aria-hidden="true">
          <i></i><i></i><i></i>
        </span>
      </div>
      <div
        v-else-if="message.role === 'user' || message.content"
        class="msg-text"
        v-html="
          message.role === 'user'
            ? message.content
            : renderMarkdown(message.content)
        "
      />

      <div v-if="message.tokens" class="msg-tokens">
        <span v-if="message.model_name" class="model-name-tag">{{
          message.model_name
        }}</span>
        {{ message.tokens }} tokens
        <span
          v-if="message.inputTokens"
          style="color: #8a7b66; font-size: 11px"
        >
          (输入 {{ message.inputTokens }} / 输出
          {{ message.tokens - message.inputTokens || message.tokens }})
        </span>
      </div>

      <div
        v-if="
          message.role === 'assistant' &&
          message.reason &&
          message.reason !== 'normal'
        "
        class="reason-badge"
        :class="message.reason"
      >
        {{ reasonLabel(message.reason) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.msg {
  display: flex;
  gap: 14px;
  max-width: 80%;
}
.msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.msg.assistant {
  align-self: flex-start;
}
.msg-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--doodle-bg, #faf5ee);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(61, 52, 40, 0.08);
}
.msg-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}
.msg-author {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-ink-muted, #999);
  padding: 0 6px;
}
.msg.user .msg-author {
  text-align: right;
}
.msg-flow-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 6px;
  font-weight: 700;
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
}
.msg-flow-tag.sse {
  background: #e6f9f6;
  color: #158a80;
  border: 1px solid rgba(25, 200, 185, 0.4);
}
.msg-flow-tag.fallback {
  background: #fef6e6;
  color: #8a6d14;
  border: 1px solid rgba(232, 167, 53, 0.4);
}
.msg-text {
  padding: 16px 20px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 2px 10px rgba(61, 52, 40, 0.08);
}
.msg.user .msg-text {
  background: linear-gradient(135deg, var(--app-accent-purple, #b39ef3) 0%, #15a89c 100%);
  color: #fff;
  border-bottom-right-radius: 6px;
}
.msg.assistant .msg-text {
  background: #fff;
  color: var(--doodle-ink, #2d2d2d);
  border: 1px solid var(--doodle-bg, #faf5ee);
  border-bottom-left-radius: 6px;
}
.msg-tokens {
  font-size: 11px;
  color: var(--app-ink-muted, #999);
  padding: 0 6px;
}
.model-name-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(25, 200, 185, 0.1);
  color: var(--app-accent-purple, #b39ef3);
  border: 1px solid rgba(25, 200, 185, 0.3);
  margin-right: 6px;
}
.reason-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  margin-top: 4px;
  font-weight: 600;
}
.reason-badge.exceed_max_iters {
  background: #fff3e0;
  color: #bf360c;
  border: 1px solid #ff8a65;
}
.reason-badge.stopped {
  background: #f5f5f5;
  color: #616161;
  border: 1px solid #bdbdbd;
}
.reason-badge.error {
  background: #ffebee;
  color: #b71c1c;
  border: 1px solid #ef5350;
}
.msg-text :deep(p) {
  margin: 0 0 8px;
}
.msg-text :deep(p:last-child) {
  margin-bottom: 0;
}
.msg-text :deep(code) {
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.06);
}
.msg.user .msg-text :deep(code) {
  background: #fff;
}
.msg-text :deep(pre) {
  margin: 8px 0;
  padding: 12px 16px;
  border-radius: 10px;
  background: #2d2d2d;
  overflow-x: auto;
}
.msg-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #f8f8f2;
  font-size: 13px;
}
.msg-text :deep(ul),
.msg-text :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}
.msg-text :deep(li) {
  margin: 4px 0;
}
.msg-text :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}
.msg-text :deep(th) {
  background: #f5f3ed;
  padding: 8px 12px;
  border: 1px solid var(--doodle-bg, #faf5ee);
  font-weight: 700;
}
.msg-text :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--doodle-bg, #faf5ee);
}
.msg-text :deep(blockquote) {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 4px solid var(--app-accent-purple, #b39ef3);
  background: rgba(25, 200, 185, 0.06);
  color: #6d5f4b;
}
.msg-text :deep(h1),
.msg-text :deep(h2) {
  margin: 12px 0 8px;
  font-size: 1.1em;
}
.msg-text :deep(a) {
  color: var(--app-accent-purple, #b39ef3);
  text-decoration: underline;
}
.msg-text :deep(.mermaid-placeholder) {
  opacity: 0.6;
  transition: opacity 0.2s;
}
.msg-text :deep(.mermaid-diagram) {
  margin: 10px 0;
  padding: 14px;
  background: #fff;
  border-radius: 12px;
  border: 2px solid var(--app-accent-purple, #b39ef3);
  overflow-x: auto;
  display: flex;
  justify-content: center;
}
.msg-text :deep(.mermaid-diagram svg) {
  max-width: 100%;
  height: auto;
}

.typing {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 22px;
}
.typing-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-secondary, #9a8c98);
  background: linear-gradient(
    90deg,
    var(--app-text-secondary, #9a8c98) 0%,
    var(--el-color-primary, #7ab88d) 40%,
    var(--app-text-secondary, #9a8c98) 80%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: typing-shimmer 1.8s ease-in-out infinite;
}
.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.typing-dots i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-primary, #7ab88d);
  animation: msg-bounce 1.4s ease-in-out infinite;
}
.typing-dots i:nth-child(1) {
  animation-delay: 0s;
}
.typing-dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes typing-shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}
@keyframes msg-bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-6px);
  }
}
</style>
