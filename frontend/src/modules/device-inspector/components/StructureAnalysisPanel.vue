<script setup>
/** 结构分析面板 — 纯规则分区结果展示（6 层分区树 + 元素档案表）。展示组件，不碰 HTTP。 */
import { ref, computed } from 'vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  elements: { type: Array, default: () => [] },
  isWebview: { type: Boolean, default: false },
})

const activeRole = ref(null)

const activeElements = computed(() =>
  activeRole.value
    ? props.elements.filter(e => e.role === activeRole.value)
    : props.elements
)

function selectSection(section) {
  activeRole.value = activeRole.value === section.role ? null : section.role
}

function shortClass(name) {
  return (name || '').split('.').pop()
}

/** 元素标识：text > content_desc > resource_id > class 短名 */
function elLabel(e) {
  return e.text || e.content_desc || e.resource_id || shortClass(e.class_name) || '—'
}

// 唯一定位候选优先级（与 PageElementsPanel 口径一致）
const XPATH_PRIORITY = ['resource-id', 'text', 'content-desc', 'class', 'combined']

function bestXPath(e) {
  const xpaths = e.xpaths || []
  const unique = xpaths.filter(x => x.count === 1 && x.xpath)
  const pool = unique.length ? unique : xpaths
  if (!pool.length) return ''
  const prio = t => { const i = XPATH_PRIORITY.indexOf(t); return i === -1 ? 999 : i }
  return [...pool].sort((a, b) => prio(a.type) - prio(b.type))[0].xpath
}

const METRIC_TAG = { 可点击: 'success', 可滚动: 'info', 可勾选: 'warning' }
</script>

<template>
  <div class="sap">
    <div v-if="isWebview" class="sap-webview-hint">
      纯 WebView 页面 — 原生层级无业务元素，页面内容需切 Web context 获取
    </div>

    <div v-if="sections.length" class="sap-body">
      <!-- 左：分区树 -->
      <aside class="sap-sections">
        <div class="sap-sections-title">页面分区</div>
        <div
          v-for="s in sections"
          :key="s.role"
          class="sap-section"
          :class="{ 'sap-section--active': s.role === activeRole }"
          role="button"
          tabindex="0"
          @click="selectSection(s)"
          @keydown.enter.prevent="selectSection(s)"
          @keydown.space.prevent="selectSection(s)"
        >
          <span class="sap-section-name">{{ s.name }}</span>
          <span class="sap-section-count">{{ s.element_count }}</span>
        </div>
      </aside>

      <!-- 右：元素档案表 -->
      <section class="sap-table">
        <el-table :data="activeElements" size="small" height="100%">
          <el-table-column label="标识" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ elLabel(row) }}</template>
          </el-table-column>
          <el-table-column label="元素" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.resource_id || '—' }}</template>
          </el-table-column>
          <el-table-column label="指标" width="150">
            <template #default="{ row }">
              <template v-if="(row.metrics || []).length">
                <el-tag
                  v-for="m in row.metrics"
                  :key="m"
                  size="small"
                  :type="METRIC_TAG[m] || 'info'"
                  class="sap-tag"
                >{{ m }}</el-tag>
              </template>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column label="XPath" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ bestXPath(row) || '—' }}</template>
          </el-table-column>
          <el-table-column label="bounds" width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.bounds || '—' }}</template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <EmptyState v-else text="暂无结构数据" hint="点击工具栏「结构分析」生成页面分区" />
  </div>
</template>

<style scoped>
.sap { height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.sap-webview-hint {
  flex-shrink: 0;
  margin-bottom: 10px;
  padding: 8px 12px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-footer-yellow-text);
  background: var(--app-highlight, #FFE066);
  border: 2px solid var(--app-ink, #2d2d2d);
  border-radius: 4px 8px 4px 8px;
}

.sap-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 2fr);
  gap: 12px;
  overflow: hidden;
}

.sap-sections {
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
  background: var(--app-bg-card);
  border: 2px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
}

.sap-sections-title {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-text-secondary);
  margin-bottom: 6px;
}

.sap-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  font-size: var(--app-size-xs);
  border-radius: 4px;
  cursor: pointer;
}

.sap-section:hover { background: var(--app-highlight, #FFE066); }
.sap-section--active {
  background: var(--app-highlight, #FFE066);
  font-weight: 700;
}

.sap-section-count {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 700;
}

.sap-table { min-height: 0; min-width: 0; overflow: hidden; }

.sap-tag { margin-right: 4px; }
</style>
