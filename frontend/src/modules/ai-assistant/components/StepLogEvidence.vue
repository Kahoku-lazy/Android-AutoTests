<template>
  <section class="sle" data-testid="step-log-evidence">
    <header class="sle-head">
      <h5 class="sle-title">设备日志证据</h5>
      <span v-if="hint" class="sle-hint">{{ hint }}</span>
    </header>

    <!-- 无证据（老任务 / 端口未监听 / 已关闭）：如实说明，不留空 -->
    <p v-if="!evidence" class="sle-empty" data-testid="log-evidence-empty">
      {{ NO_EVIDENCE_TEXT }}
    </p>

    <template v-else>
      <!-- 摘要常显：等级 + 条数 + 关键词 + 功能点 -->
      <div v-if="hits.length" class="sle-summary" data-testid="log-evidence-summary">
        <span
          v-for="(hit, index) in hits"
          :key="index"
          class="sle-chip"
          :class="gradeTagClass(hit.grade)"
        >
          <span class="sle-chip__grade">{{ gradeLabel(hit.grade) }}</span>
          <span class="sle-chip__count">{{ hitCount(hit) }} 条</span>
          <span class="sle-chip__keyword">{{ hit.keyword || "—" }}</span>
          <span v-if="hitFeatureText(hit)" class="sle-chip__feature">{{
            hitFeatureText(hit)
          }}</span>
        </span>
      </div>
      <p v-else class="sle-summary-plain" data-testid="log-evidence-conclusion">
        {{ conclusionLine }}
      </p>

      <!-- 详情折叠：命中 / 动作前 / 超窗 / 窗口原始日志 -->
      <el-collapse v-if="hasEvidenceDetail(evidence)" class="sle-detail">
        <el-collapse-item
          v-if="hits.length"
          name="hits"
          :title="`命中详情（${hits.length} 个关键词）`"
        >
          <article v-for="(hit, index) in hits" :key="index" class="sle-hit">
            <p class="sle-hit__head">
              <span class="sle-tag" :class="gradeTagClass(hit.grade)">{{
                gradeLabel(hit.grade)
              }}</span>
              <span class="sle-hit__keyword">{{ hit.keyword || "—" }}</span>
              <span v-if="hitFeatureText(hit)" class="sle-hit__feature">{{
                hitFeatureText(hit)
              }}</span>
            </p>
            <ul class="sle-rows">
              <li v-for="(occ, oi) in hitOccurrences(hit)" :key="oi" class="sle-row">
                <span class="sle-row__time">{{ occ.timestamp }}</span>
                <span v-if="occ.source" class="sle-row__src">{{ occ.source }}</span>
                <span v-if="occ.text" class="sle-row__text">{{ occ.text }}</span>
              </li>
            </ul>
            <p v-if="hit.baseline_occurrences?.length" class="sle-hit__baseline">
              动作前基线里已出现过
              {{ hit.baseline_occurrences.length }} 次（故判为疑似周期，不能单独作为通过依据）
            </p>
          </article>
        </el-collapse-item>

        <el-collapse-item
          v-if="evidence.before_action?.length"
          name="before"
          :title="`动作前日志（${evidence.before_action.length}）`"
        >
          <ul class="sle-rows">
            <li v-for="(row, index) in evidence.before_action" :key="index" class="sle-row">
              <span class="sle-row__time">{{ row.timestamp }}</span>
              <span class="sle-row__text">{{ row.text }}</span>
            </li>
          </ul>
        </el-collapse-item>

        <el-collapse-item
          v-if="evidence.out_of_window?.length"
          name="out"
          :title="`超窗日志（${evidence.out_of_window.length}）`"
        >
          <ul class="sle-rows">
            <li v-for="(row, index) in evidence.out_of_window" :key="index" class="sle-row">
              <span class="sle-row__text">{{ outOfWindowLine(row) }}</span>
            </li>
          </ul>
        </el-collapse-item>

        <el-collapse-item
          v-if="lines.length"
          name="lines"
          :title="`窗口原始日志（${lines.length} 条${mergedCount ? `，含 ${mergedCount} 条同毫秒合并` : ''}）`"
        >
          <ul class="sle-rows">
            <li
              v-for="(line, index) in lines"
              :key="index"
              class="sle-row"
              :class="{ 'is-merged': line.merged }"
            >
              <span class="sle-row__time">{{ line.timestamp }}</span>
              <span class="sle-row__src">{{ line.source }}</span>
              <span class="sle-row__text">{{ line.text }}</span>
            </li>
          </ul>
        </el-collapse-item>
      </el-collapse>
    </template>
  </section>
</template>

<script setup lang="ts">
/** StepLogEvidence — 单步尝试的验收设备日志证据：摘要常显 + 详情折叠（只读，不排序） */
import { computed } from "vue"
import type { TaskLogEvidence, TaskLogEvidenceHit } from "@/shared/types/ai"
import {
  NO_EVIDENCE_TEXT,
  conclusionText,
  evidenceLines,
  gradeLabel,
  gradeTagClass,
  hasEvidenceDetail,
  hitFeatureText,
  hitOccurrences,
  outOfWindowLine,
  windowHint,
} from "../helpers/log-evidence"

const props = defineProps<{ evidence?: TaskLogEvidence }>()

const hits = computed(() => props.evidence?.hits || [])
const lines = computed(() => evidenceLines(props.evidence))
const mergedCount = computed(() => lines.value.filter((line) => line.merged).length)
const hint = computed(() => windowHint(props.evidence))

const conclusionLine = computed(() => {
  const evidence = props.evidence
  if (!evidence) return ""
  const rows = Number(evidence.window_line_count ?? evidence.lines?.length ?? 0) || 0
  return `${conclusionText(evidence.conclusion) || "未命中关键词"}（窗口内 ${rows} 行）`
})

function hitCount(hit: TaskLogEvidenceHit): number {
  return Number(hit.count ?? hit.occurrences?.length ?? 0) || 1
}
</script>

<style src="./StepLogEvidence.style.css" scoped></style>
