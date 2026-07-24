<script setup>
defineProps({
  toolCalls: { type: Array, default: () => [] },
});

function toolStateLabel(state) {
  const labels = {
    calling: "调用中...",
    submitted: "参数已提交",
    running: "执行中...",
    success: "执行完成",
    error: "执行出错",
    finished: "已完成",
    denied: "已拒绝",
  };
  return labels[state] || state || "";
}

function toolIcon(state) {
  if (state === "calling") return "⏳";
  if (state === "running") return "🔄";
  if (state === "success") return "✅";
  if (state === "error") return "❌";
  return "🔧";
}

function formatOutput(output) {
  if (typeof output === "string") return output.slice(0, 300);
  return JSON.stringify(output).slice(0, 300);
}
</script>

<template>
  <div v-if="toolCalls.length" class="tool-flow-block">
    <div
      v-for="tc in toolCalls"
      :key="tc.id"
      class="tool-step"
      :class="tc.state"
    >
      <div class="tool-step-header">
        <span class="tool-step-icon">{{ toolIcon(tc.state) }}</span>
        <span class="tool-step-name">{{ tc.name }}</span>
        <span class="tool-step-state">{{ toolStateLabel(tc.state) }}</span>
      </div>
      <div v-if="tc.displayArgs" class="tool-step-args">
        <details>
          <summary>参数</summary>
          <pre>{{ tc.displayArgs }}</pre>
        </details>
      </div>
      <div v-if="tc.partialOutput" class="tool-step-output streaming">
        <span class="tool-streaming-dot" />
        {{ tc.partialOutput.slice(0, 200) }}...
      </div>
      <div v-if="tc.output && !tc.partialOutput" class="tool-step-output">
        {{ formatOutput(tc.output) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-flow-block {
  margin: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tool-step {
  border-radius: 10px;
  border: 1px solid #e8e2d6;
  background: rgba(255, 255, 255, 0.7);
  padding: 8px 12px;
}
.tool-step.calling {
  border-color: #19c8b9;
  background: rgba(230, 249, 246, 0.4);
}
.tool-step.running {
  border-color: #e8a735;
  background: rgba(254, 246, 230, 0.4);
}
.tool-step.success {
  border-color: #a3d977;
  background: rgba(242, 251, 230, 0.4);
}
.tool-step.error {
  border-color: #e85f5f;
  background: rgba(254, 237, 237, 0.4);
}
.tool-step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.tool-step-icon {
  font-size: 14px;
}
.tool-step-name {
  font-weight: 700;
  color: #4a3a28;
}
.tool-step-state {
  font-size: 11px;
  color: #8a7b66;
}
.tool-step-args {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6d5f4b;
}
.tool-step-args details summary {
  cursor: pointer;
  color: #8a7b66;
  font-size: 12px;
}
.tool-step-args pre {
  margin: 4px 0;
  padding: 8px;
  background: var(--ink);
  border-radius: 8px;
  color: #e6db74;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
}
.tool-step-output {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6d5f4b;
  line-height: 1.5;
  white-space: pre-wrap;
}
.tool-step-output.streaming {
  color: #19c8b9;
}
.tool-streaming-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #19c8b9;
  animation: pulse 1s infinite;
  margin-right: 4px;
  vertical-align: middle;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}
</style>
