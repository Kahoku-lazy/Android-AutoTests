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
.section-block { margin-top: var(--app-space-lg); }
.sec-title { font-size: var(--app-size-md); font-weight: 700; margin: 0 0 var(--app-space-xs); display: flex; align-items: center; gap: var(--app-space-sm); }
.sec-badge { font-size: var(--app-size-xs); background: var(--app-pending); padding: 2px 10px; border-radius: var(--app-radius-sm); font-weight: 600; color: var(--app-pending-text); }
.sec-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin: 0 0 var(--app-space-md); }

/* ── Case group ── */
.case-group { border: 1.5px solid var(--app-border-light, #e0e0e0); border-radius: var(--app-radius-md); margin-bottom: var(--app-space-sm); overflow: hidden; }
.case-group--expanded { border-color: var(--app-accent-blue, #5fa8e8); }
.case-group__header {
  display: flex; align-items: center; gap: var(--app-space-sm); padding: 10px 14px;
  background: var(--app-bg-subtle, #f8f8f8); cursor: pointer;
  user-select: none; transition: background var(--app-duration-fast) var(--app-ease);
}
.case-group__header:hover { background: var(--app-page-active-bg, #eef4fb); }
.case-group__arrow { font-size: var(--app-size-xs); color: var(--app-text-secondary); width: 14px; flex-shrink: 0; }
.case-group__id { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); background: var(--app-bg-subtle); padding: 2px 6px; border-radius: var(--app-radius-sm); }
.case-group__title { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); flex: 1; }
.case-group__stats { display: flex; gap: var(--app-space-sm); }
.cg-stat { font-size: var(--app-size-xs); padding: 2px var(--app-space-sm); border-radius: var(--app-radius-sm); font-weight: 600; }
.cg-stat--total { background: var(--app-bg-subtle); color: var(--app-text-secondary); }
.cg-stat--pass { background: var(--app-pass); color: var(--app-pass-text); }
.cg-stat--fail { background: var(--app-fail); color: var(--app-fail-text); }
.case-group__date { font-size: var(--app-size-xs); color: var(--app-text-muted); margin-left: auto; }

.case-group__body { padding: var(--app-space-md); background: var(--app-bg-subtle); }

/* ── Screenshot grid ── */
.ss-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--app-space-md);
}
.ss-card {
  border: 1.5px solid var(--app-border-light, #e0e0e0); border-radius: var(--app-radius-md); overflow: hidden;
  background: var(--app-bg-card); transition: box-shadow var(--app-duration-fast) var(--app-ease);
}
.ss-card:hover { box-shadow: var(--app-shadow-sm); }
.ss-card--fail { border-color: var(--app-status-danger); }

.ss-card__header {
  display: flex; align-items: center; gap: var(--app-space-sm);
  padding: 7px 10px; background: var(--app-bg-subtle); border-bottom: 1px solid var(--app-border-lighter);
}
.ss-step-num { font-weight: 700; font-size: var(--app-size-xs); color: var(--ink); }
.ss-type-badge { font-size: var(--app-size-xs); color: var(--app-text-inverse); padding: 2px 7px; border-radius: var(--app-radius-sm); font-family: var(--app-font-mono); }
.ss-result { font-size: var(--app-size-xs); padding: 1px 7px; border-radius: var(--app-radius-sm); font-weight: 600; }
.ss-result--pass { background: var(--app-pass); color: var(--app-pass-text); }
.ss-result--fail { background: var(--app-fail); color: var(--app-fail-text); }

.ss-img-wrap {
  position: relative; cursor: pointer; background: var(--app-bg-subtle);
  min-height: 160px; display: flex; align-items: center; justify-content: center;
  overflow: hidden; max-height: 240px;
}
.ss-img { width: 100%; object-fit: contain; max-height: 240px; display: block; }
.ss-no-img { color: var(--app-text-muted); font-size: var(--app-size-xs); padding: var(--app-space-xl); }
.ss-img-overlay {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: var(--app-overlay, rgba(0,0,0,0.35)); opacity: 0; transition: opacity var(--app-duration-fast) var(--app-ease);
  color: var(--app-text-inverse); font-size: var(--app-size-sm); font-weight: 600;
}
.ss-img-wrap:hover .ss-img-overlay { opacity: 1; }

.ss-card__body { padding: var(--app-space-sm); }
.ss-desc { font-size: var(--app-size-xs); color: var(--ink); line-height: 1.4; margin-bottom: 3px; }
.ss-selector { font-size: var(--app-size-xs); color: var(--app-text-secondary); font-family: var(--app-font-mono); word-break: break-all; }
.ss-error {
  margin-top: 5px; padding: 5px var(--app-space-sm); background: var(--app-fail);
  border-radius: 5px; color: var(--app-fail-text); font-size: var(--app-size-xs); line-height: 1.4;
}
</style>
