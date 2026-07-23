<script setup>
import { ref } from "vue";
import { stepSummary, FIELD_LABELS } from "../step-utils.js";

defineProps({
  steps: { type: Array, default: () => [] },
});

const expanded = ref({});

function toggle(idx) {
  expanded.value[idx] = !expanded.value[idx];
}

const DETAIL_FIELDS = [
  "xpath",
  "xpath2",
  "timeout",
  "expected_text",
  "index",
  "direction",
  "distance",
];
</script>

<template>
  <div v-if="steps.length === 0" class="step-viewer-empty">
    <span class="step-viewer-empty__icon">📋</span>
    <p>暂无步骤</p>
  </div>

  <div v-else class="step-viewer">
    <div
      v-for="(step, idx) in steps"
      :key="idx"
      class="step-viewer__item"
      :class="{ 'step-viewer__item--expanded': expanded[idx] }"
    >
      <!-- Collapsed summary bar -->
      <div class="step-viewer__bar" @click="toggle(idx)">
        <span class="step-viewer__idx">{{ idx + 1 }}</span>
        <span class="step-viewer__summary">{{ stepSummary(step) }}</span>
        <span class="step-viewer__toggle">{{ expanded[idx] ? "▾" : "▸" }}</span>
      </div>

      <!-- Expanded detail fields -->
      <div v-if="expanded[idx]" class="step-viewer__detail">
        <div class="step-viewer__detail-grid">
          <div
            v-for="field in DETAIL_FIELDS"
            :key="field"
            class="step-viewer__field"
          >
            <template v-if="step[field] !== undefined && step[field] !== ''">
              <span class="step-viewer__field-label">{{
                FIELD_LABELS[field] || field
              }}</span>
              <span class="step-viewer__field-value">{{ step[field] }}</span>
            </template>
          </div>
          <div
            v-if="step.description"
            class="step-viewer__field step-viewer__field--desc"
          >
            <span class="step-viewer__field-label">{{
              FIELD_LABELS.description
            }}</span>
            <span class="step-viewer__field-value">{{ step.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-viewer {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-viewer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--app-text-secondary);
}

.step-viewer-empty__icon {
  font-size: 36px;
}

.step-viewer-empty p {
  font-size: 14px;
  margin: 0;
}

.step-viewer__item {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--doodle-ink, #2d2d2d);
  background: rgba(255,255,255,0.38);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-viewer__item:hover {
  border-color: rgba(162,210,255,0.58);
  background: rgba(162,210,255,0.12);
}

.step-viewer__bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
}

.step-viewer__idx {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(162,210,255,0.18);
  color: var(--app-green-deep);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-viewer__summary {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}

.step-viewer__toggle {
  font-size: 12px;
  color: var(--app-text-secondary);
  flex-shrink: 0;
}

.step-viewer__detail {
  padding: 4px 16px 16px 56px;
}

.step-viewer__detail-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
}

.step-viewer__field {
  display: flex;
  gap: 6px;
  align-items: baseline;
  font-size: 12px;
}

.step-viewer__field--desc {
  flex-basis: 100%;
}

.step-viewer__field-label {
  color: var(--app-text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.step-viewer__field-label::after {
  content: "：";
}

.step-viewer__field-value {
  color: var(--app-text);
  font-weight: 600;
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  word-break: break-all;
}
</style>
