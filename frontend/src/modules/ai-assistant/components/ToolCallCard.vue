<script setup lang="ts">
import type { ToolCall } from '@/shared/types/ai'

defineProps<{
  toolCalls?: ToolCall[]
}>()

function toolStateLabel(state: string): string {
  const labels: Record<string, string> = {
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

function toolIcon(state: string): string {
  if (state === "calling") return "⏳";
  if (state === "running") return "🔄";
  if (state === "success") return "✅";
  if (state === "error") return "❌";
  return "🔧";
}

// ── Tool source detection ──
const WORKSPACE_NAMES = ["Bash", "Edit", "Glob", "Grep", "Read", "Write"]

function detectSource(tool: ToolCall): { label: string; cls: string } {
  if (tool.source) {
    const map: Record<string, { label: string; cls: string }> = {
      builtin:  { label: "内置", cls: "src-builtin" },
      platform: { label: "平台", cls: "src-platform" },
      mcp:      { label: "MCP",  cls: "src-mcp" },
      skill:    { label: "Skill", cls: "src-skill" },
    }
    return map[tool.source] || { label: tool.source, cls: "" }
  }
  // Fallback: detect from tool name
  if (WORKSPACE_NAMES.includes(tool.name)) return { label: "内置", cls: "src-builtin" }
  if (tool.name.startsWith("mcp__")) return { label: "MCP", cls: "src-mcp" }
  return { label: "平台", cls: "src-platform" }
}

function elapsedMs(tool: ToolCall): string {
  if (!tool.startedAt) return ""
  const ms = Date.now() - tool.startedAt
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatOutput(output: unknown): string {
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
        <span class="tool-source-tag" :class="detectSource(tc).cls">{{ detectSource(tc).label }}</span>
        <span class="tool-step-state">{{ toolStateLabel(tc.state) }}</span>
        <span v-if="tc.startedAt && tc.state !== 'calling'" class="tool-elapsed">{{ elapsedMs(tc) }}</span>
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
  border: 1px solid var(--doodle-bg, #faf5ee);
  background: #fff;
  padding: 8px 12px;
}
.tool-step.calling {
  border-color: var(--app-accent-purple, #b39ef3);
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
.tool-step.message {
  border-color: #e85f5f;
  background: rgba(254, 237, 237, 0.4);
}
.tool-step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--app-size-sm);
}
.tool-step-icon {
  font-size: var(--app-size-sm);
}
.tool-step-name {
  font-weight: 700;
  color: var(--doodle-ink, #2d2d2d);
}
.tool-step-state {
  font-size: var(--app-size-xs);
  color: #8a7b66;
}
.tool-source-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  line-height: 1.4;
}
.src-builtin  { background: rgba(179,158,243,0.15); color: #7c6ff7; }
.src-platform { background: rgba(25,200,185,0.12); color: #0fa89b; }
.src-mcp      { background: rgba(232,167,53,0.12); color: #c7851a; }
.src-skill    { background: rgba(77,182,172,0.12); color: #2d8a82; }
.tool-elapsed {
  font-size: 10px;
  color: #b5a68e;
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}
.tool-step-args {
  margin: 6px 0 0;
  font-size: var(--app-size-sm);
  color: #6d5f4b;
}
.tool-step-args details summary {
  cursor: pointer;
  color: #8a7b66;
  font-size: var(--app-size-sm);
}
.tool-step-args pre {
  margin: 4px 0;
  padding: 8px;
  background: var(--ink);
  border-radius: 8px;
  color: #e6db74;
  font-size: var(--app-size-sm);
  overflow-x: auto;
  white-space: pre-wrap;
}
.tool-step-output {
  margin: 6px 0 0;
  font-size: var(--app-size-sm);
  color: #6d5f4b;
  line-height: 1.5;
  white-space: pre-wrap;
}
.tool-step-output.streaming {
  color: var(--app-accent-purple, #b39ef3);
}
.tool-streaming-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--app-accent-purple, #b39ef3);
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
