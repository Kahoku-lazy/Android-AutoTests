<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
})

const previewVisible = ref(false)
const previewSrc = ref('')
const previewTitle = ref('')
const expandedCases = ref(new Set())

// ── Group steps by case ──
const caseGroups = computed(() => {
  const map = new Map()
  for (const s of props.steps) {
    const cid = s.caseId || '_default'
    if (!map.has(cid)) {
      map.set(cid, {
        caseId: cid,
        caseTitle: s.caseTitle || cid,
        total: 0, pass: 0, fail: 0,
        steps: [],
        date: s._date || '',
      })
    }
    const g = map.get(cid)
    g.steps.push(s)
    g.total++
    if (s.result === 'pass') g.pass++
    else if (s.result === 'fail') g.fail++
  }
  return Array.from(map.values())
})

function toggleCase(cid) {
  if (expandedCases.value.has(cid)) expandedCases.value.delete(cid)
  else expandedCases.value.add(cid)
  expandedCases.value = new Set(expandedCases.value)
}

function screenshotUrl(relPath) {
  if (!relPath) return ''
  return `/api/runner/step-screenshots/${relPath}`
}

function openPreview(step) {
  previewSrc.value = screenshotUrl(step.screenshot)
  previewTitle.value = `步骤 ${step.index + 1} · ${step.type} · ${step.result}`
  previewVisible.value = true
}

function stepTypeColor(type) {
  if (/click|long_click/.test(type)) return '#e85f5f'
  if (/fill|type/.test(type)) return '#5fa8e8'
  if (/assert/.test(type)) return '#6fba2c'
  if (/navigate/.test(type)) return '#9e9e9e'
  if (/wait|sleep/.test(type)) return '#f0a050'
  return '#8e8e8e'
}
</script>

<template>
  <section v-if="steps.length" class="section-block">
    <h3 class="sec-title">
      📸 自动化执行步骤详情
      <span class="sec-badge">{{ steps.length }} 步</span>
    </h3>
    <p class="sec-sub">每步自动截图 + 红框标注 AI 操作位置。按用例分组，点击展开查看。</p>

    <!-- 用例分组 -->
    <div v-for="group in caseGroups" :key="group.caseId" class="case-group"
         :class="{ 'case-group--expanded': expandedCases.has(group.caseId) }">
      <!-- 用例头部 -->
      <div class="case-group__header" @click="toggleCase(group.caseId)">
        <span class="case-group__arrow">{{ expandedCases.has(group.caseId) ? '▼' : '▶' }}</span>
        <span class="case-group__id">{{ group.caseId }}</span>
        <span class="case-group__title">{{ group.caseTitle }}</span>
        <div class="case-group__stats">
          <span class="cg-stat cg-stat--total">{{ group.total }} 步</span>
          <span class="cg-stat cg-stat--pass">✅ {{ group.pass }}</span>
          <span class="cg-stat cg-stat--fail" v-if="group.fail > 0">❌ {{ group.fail }}</span>
        </div>
        <span v-if="group.date" class="case-group__date">{{ group.date }}</span>
      </div>

      <!-- 步骤截图网格 -->
      <div v-if="expandedCases.has(group.caseId)" class="case-group__body">
        <div class="ss-grid">
          <div v-for="(step, si) in group.steps" :key="si" class="ss-card"
               :class="{ 'ss-card--fail': step.result === 'fail' }">
            <div class="ss-card__header">
              <span class="ss-step-num">步骤 {{ step.index + 1 }}</span>
              <span class="ss-type-badge" :style="{ background: stepTypeColor(step.type) }">{{ step.type }}</span>
              <span class="ss-result" :class="step.result === 'pass' ? 'ss-result--pass' : 'ss-result--fail'">
                {{ step.result === 'pass' ? '✅ PASS' : '❌ FAIL' }}
              </span>
            </div>

            <div class="ss-img-wrap" @click="openPreview(step)">
              <img v-if="step.screenshot" :src="screenshotUrl(step.screenshot)"
                   :alt="step.description" class="ss-img" loading="lazy" />
              <div v-else class="ss-no-img">无截图</div>
              <div class="ss-img-overlay">🔍 点击放大</div>
            </div>

            <div class="ss-card__body">
              <div class="ss-desc">{{ step.description }}</div>
              <div v-if="step.selector" class="ss-selector">📍 {{ step.selector }}</div>
              <div v-if="step.result === 'fail' && step.error" class="ss-error">
                ❌ {{ step.error }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 大图预览 -->
    <el-dialog v-model="previewVisible" :title="previewTitle" width="90%" top="2vh">
      <img :src="previewSrc" style="width:100%;border-radius:8px;" />
    </el-dialog>
  </section>
</template>

<style scoped>
/* ── Section ── */
.section-block { margin-top: 24px; }
.sec-title { font-size: 18px; font-weight: 700; margin: 0 0 4px; display: flex; align-items: center; gap: 8px; }
.sec-badge { font-size: 12px; background: var(--app-blue-light, #dff5ff); padding: 2px 10px; border-radius: 20px; font-weight: 600; color: var(--ink); }
.sec-sub { font-size: 13px; color: #999; margin: 0 0 12px; }

/* ── Case group ── */
.case-group { border: 1.5px solid var(--app-border, #e0e0e0); border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
.case-group--expanded { border-color: var(--app-blue, #5fa8e8); }
.case-group__header {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  background: var(--app-bg-soft, #f8f8f8); cursor: pointer;
  user-select: none; transition: background 0.15s;
}
.case-group__header:hover { background: #eef4fb; }
.case-group__arrow { font-size: 11px; color: #888; width: 14px; flex-shrink: 0; }
.case-group__id { font-family: monospace; font-size: 12px; color: #888; background: #e8e8e8; padding: 2px 6px; border-radius: 4px; }
.case-group__title { font-weight: 600; font-size: 14px; color: var(--ink); flex: 1; }
.case-group__stats { display: flex; gap: 8px; }
.cg-stat { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.cg-stat--total { background: #e8e8e8; color: #666; }
.cg-stat--pass { background: rgba(111,186,44,0.12); color: #6fba2c; }
.cg-stat--fail { background: rgba(232,95,95,0.12); color: #e85f5f; }
.case-group__date { font-size: 11px; color: #aaa; margin-left: auto; }

.case-group__body { padding: 12px; background: #fafafa; }

/* ── Screenshot grid ── */
.ss-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}
.ss-card {
  border: 1.5px solid #e0e0e0; border-radius: 10px; overflow: hidden;
  background: #fff; transition: box-shadow 0.15s;
}
.ss-card:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.06); }
.ss-card--fail { border-color: #e85f5f; }

.ss-card__header {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; background: #f5f5f5; border-bottom: 1px solid #eee;
}
.ss-step-num { font-weight: 700; font-size: 12px; color: var(--ink); }
.ss-type-badge { font-size: 10px; color: #fff; padding: 2px 7px; border-radius: 3px; font-family: monospace; }
.ss-result { font-size: 11px; padding: 1px 7px; border-radius: 3px; font-weight: 600; }
.ss-result--pass { background: rgba(111,186,44,0.12); color: #6fba2c; }
.ss-result--fail { background: rgba(232,95,95,0.12); color: #e85f5f; }

.ss-img-wrap {
  position: relative; cursor: pointer; background: #f0f0f0;
  min-height: 160px; display: flex; align-items: center; justify-content: center;
  overflow: hidden; max-height: 240px;
}
.ss-img { width: 100%; object-fit: contain; max-height: 240px; display: block; }
.ss-no-img { color: #bbb; font-size: 13px; padding: 30px; }
.ss-img-overlay {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.35); opacity: 0; transition: opacity 0.15s;
  color: #fff; font-size: 14px; font-weight: 600;
}
.ss-img-wrap:hover .ss-img-overlay { opacity: 1; }

.ss-card__body { padding: 8px 10px; }
.ss-desc { font-size: 12px; color: var(--ink); line-height: 1.4; margin-bottom: 3px; }
.ss-selector { font-size: 10px; color: #888; font-family: monospace; word-break: break-all; }
.ss-error {
  margin-top: 5px; padding: 5px 8px; background: rgba(232,95,95,0.06);
  border-radius: 5px; color: #c0392b; font-size: 11px; line-height: 1.4;
}
</style>
