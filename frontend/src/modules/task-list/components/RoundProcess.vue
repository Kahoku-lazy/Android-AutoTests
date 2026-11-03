<script setup>
/**
 * 任务详情：一轮模型过程（执行或验收）。
 *
 * 只负责渲染已经分好组的轮次：交付 / 结论 / 阶段时间线 / 截图。
 * 过程块默认收起，收起时头部保留角色、判决与结论摘要；步骤行与尝试分块由 CaseStepList 提供。
 */
import { computed, ref } from "vue"
import { formatClock } from "../helpers/report-steps"
import TaskMediaThumb from "./TaskMediaThumb.vue"

const props = defineProps({
  round: { type: Object, required: true },
  /** executor / verifier：决定左边色与标题文案 */
  kind: { type: String, default: "executor" },
  taskId: { type: Number, required: true },
})

/** 阶段 → 配色类；后端只给这四个阶段名 */
const PHASE_CLASS = {
  开始: "is-start",
  推理阶段: "is-reason",
  执行阶段: "is-execute",
  结束: "is-end",
}

/** 过程块默认收起：展开才渲染时间线、截图与明细 */
const open = ref(false)

const isVerifier = computed(() => props.kind === "verifier")

/** 验收判决标记：只在有判决时出现，无判决不给 */
const verdictMark = computed(() => {
  if (!isVerifier.value) return ""
  const passed = props.round?.verdict?.passed
  if (passed === true) return "✅"
  if (passed === false) return "❌"
  return ""
})

/** 收起时的结论摘要：只取判决说明，正文仍在展开体里 */
const summary = computed(() => String(props.round?.verdict?.message || "").trim())

const procTitle = computed(() => (isVerifier.value ? "验收过程" : "执行过程"))

const bodyId = computed(() => `flow-proc-${props.round?.round_id}`)

function phaseClass(phase) {
  return PHASE_CLASS[phase] || "is-other"
}
</script>

<template>
  <section class="flow-proc" :class="isVerifier ? 'is-verifier' : 'is-executor'">
    <button
      type="button"
      class="flow-proc__head"
      :aria-expanded="open"
      :aria-controls="bodyId"
      @click="open = !open"
    >
      <span class="flow-proc__mark" aria-hidden="true">{{ open ? "▾" : "▸" }}</span>
      <span
        v-if="round.role"
        class="flow-proc__role"
        :class="isVerifier ? 'is-verifier' : 'is-executor'"
        >{{ round.role }}</span
      >
      <span class="flow-proc__title">{{ procTitle }}</span>
      <span v-if="round.model" class="flow-proc__meta">{{ round.model }}</span>
      <span v-if="verdictMark" class="flow-proc__verdict">{{ verdictMark }}</span>
      <span v-if="!open && summary" class="flow-proc__summary">{{ summary }}</span>
    </button>

    <div v-if="open" :id="bodyId" class="flow-proc__body">
      <section v-if="round.handover" class="flow-proc__note is-handover">
        <h4 class="flow-proc__note-title">交付</h4>
        <p class="flow-note">{{ round.handover }}</p>
      </section>

      <section v-if="round.verdict && round.verdict.message" class="flow-proc__note is-verdict">
        <h4 class="flow-proc__note-title">结论</h4>
        <p class="flow-note">{{ round.verdict.message }}</p>
      </section>

      <ol v-if="round.blocks && round.blocks.length" class="flow-timeline">
        <li
          v-for="(block, blockIndex) in round.blocks"
          :key="blockIndex"
          class="flow-phase"
          :class="phaseClass(block.phase)"
        >
          <h4 class="flow-phase__title">{{ block.title || block.phase }}</h4>
          <div v-for="item in block.items || []" :key="item.seq" class="flow-item">
            <div class="flow-item__head">
              <time>{{ formatClock(item.time) }}</time>
              <strong>{{ item.label }}</strong>
              <span v-if="item.count > 1" class="flow-item__count">×{{ item.count }}</span>
            </div>
            <p v-if="item.detail" class="flow-item__detail">{{ item.detail }}</p>
            <TaskMediaThumb v-if="item.media_id" :task-id="taskId" :media-id="item.media_id" />
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>

<style src="./RoundProcess.style.css" scoped></style>
