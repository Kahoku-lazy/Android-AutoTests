<script setup lang="ts">
import CaseList from "../CaseList.vue";
import { listApiDefinitions, deleteApiDefinition, getApiDefinition } from "../../api/apiTesting";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
defineEmits(["refresh-tree", "clear-case", "select-case", "go-all"]);

const api = { listDefs: listApiDefinitions, deleteDef: deleteApiDefinition, getDef: getApiDefinition };

// Derive flat display fields from config_json for list columns
function firstStepMethod(row: Record<string, any>) {
  const cfg = row.config_json
  if (!cfg) return ''
  // Single format
  if (cfg.meta && cfg.request) return cfg.request.method || ''
  // Multi format
  if (cfg.steps && cfg.steps.length) return cfg.steps[0].method || ''
  return ''
}
function firstStepUrl(row: Record<string, any>) {
  const cfg = row.config_json
  if (!cfg) return ''
  // Single format
  if (cfg.meta && cfg.request) return (cfg.meta.base_url || '') + (cfg.request.path || '')
  // Multi format
  if (cfg.steps && cfg.steps.length) return (cfg.steps[0].domain || '') + (cfg.steps[0].url || '')
  return ''
}
function stepCount(row: Record<string, any>) {
  const cfg = row.config_json
  if (!cfg) return 0
  // Single format: count cases
  if (cfg.meta && cfg.cases) return cfg.cases.length
  // Multi format: count steps
  if (cfg.steps) return cfg.steps.length
  return 0
}

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 180 },
  { title: "方法", dataIndex: "_method", minWidth: 76, align: "center" },
  { title: "URL", dataIndex: "_url", minWidth: 200 },
  { title: "步骤", dataIndex: "_stepCount", minWidth: 60, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 70, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 160, align: "center" },
];

const METHOD_COLORS: Record<string, string> = {
  GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#a78bfa',
}

function editPath(id: string) { return `/cases/api/${id}/edit`; }
function jsonPreview(obj: any) {
  if (!obj || !Object.keys(obj).length) return ''
  try { return JSON.stringify(obj, null, 2) } catch { return '' }
}
</script>

<template>
  <CaseList case-type="api" :list-api="api" :columns="columns" create-path="/cases/api/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    :active-case-id="activeCaseId"
    @refresh-tree="$emit('refresh-tree')"
    @clear-case="$emit('clear-case')"
    @select-case="$emit('select-case', $event)"
    @go-all="$emit('go-all')">
    <template #cell-_method="{ record }">
      <span v-if="firstStepMethod(record)" :style="{ color: METHOD_COLORS[firstStepMethod(record)] || 'inherit', fontWeight: 700 }">{{ firstStepMethod(record) }}</span>
      <span v-else style="color:var(--app-ink-muted)">—</span>
    </template>
    <template #cell-_url="{ record }">
      <code v-if="firstStepUrl(record)" class="api-list__url-code" :title="firstStepUrl(record)">{{ firstStepUrl(record) }}</code>
      <span v-else style="color:var(--app-ink-muted)">—</span>
    </template>
    <template #cell-_stepCount="{ record }">
      <span style="font-weight:600">{{ stepCount(record) || 0 }}</span>
    </template>
    <template #detail="{ case: c }">
      <div class="api-detail">
        <!-- ── Single format ── -->
        <template v-if="c.config_json && c.config_json.meta && c.config_json.cases">
          <div class="api-detail__row">
            <span class="api-detail__label">格式</span>
            <span class="api-detail__val">单接口 · 数据驱动</span>
          </div>
          <div class="api-detail__row">
            <span class="api-detail__label">BASE</span>
            <code class="api-detail__url">{{ c.config_json.meta.base_url || '—' }}</code>
          </div>
          <div class="api-detail__row">
            <span class="api-detail__label">请求</span>
            <span class="api-detail__badge" :style="{ background: METHOD_COLORS[c.config_json.request.method] || '#999' }">{{ c.config_json.request.method }}</span>
            <code class="api-detail__url">{{ (c.config_json.meta.base_url || '') + (c.config_json.request.path || '') }}</code>
          </div>
          <div class="api-detail__row">
            <span class="api-detail__label">用例</span>
            <span class="api-detail__val">{{ c.config_json.cases.length }} 条</span>
          </div>
          <div class="api-detail__row" v-for="cat in [...new Set(c.config_json.cases.map((x: any) => String(x.category)).filter(Boolean) as string[])]" :key="cat">
            <span class="api-detail__label api-detail__cat-tag">{{ cat }}</span>
            <span class="api-detail__val">{{ c.config_json.cases.filter((x: any) => x.category === cat).length }} 条</span>
          </div>
        </template>
        <!-- ── Multi format ── -->
        <template v-else>
        <div v-if="c.config_json && c.config_json.steps && c.config_json.steps.length">
          <div class="api-detail__row" v-for="(s, si) in c.config_json.steps" :key="si">
            <span class="api-detail__step-idx">步骤{{ si + 1 }}</span>
            <span class="api-detail__badge" :style="{ background: METHOD_COLORS[s.method] || '#999' }">{{ s.method }}</span>
            <code class="api-detail__url">{{ (s.domain || '') + (s.url || '') }}</code>
          </div>
        </div>
        <div v-else class="api-detail__row">
          <span class="api-detail__label">步骤</span>
          <span class="api-detail__empty">无步骤数据</span>
        </div>
        <div class="api-detail__row" v-if="(c.config_json && c.config_json.test_data || []).length">
          <span class="api-detail__label">测试数据</span>
          <span class="api-detail__val">{{ c.config_json.test_data.length }} 行</span>
        </div>
        <div class="api-detail__row" v-if="(c.config_json && c.config_json.validation || []).length">
          <span class="api-detail__label">校验规则</span>
          <span class="api-detail__val">{{ c.config_json.validation.filter(v=>v.enabled).length }}/{{ c.config_json.validation.length }} 启用</span>
        </div>
        <div class="api-detail__row" v-if="c.precondition">
          <span class="api-detail__label">前置条件</span>
          <p class="api-detail__text">{{ c.precondition }}</p>
        </div>
        </template>
      </div>
    </template>
  </CaseList>
</template>

<style scoped>
.api-detail { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.api-detail__row { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }
.api-detail__badge {
  display: inline-block; padding: 2px 10px; border-radius: 8px;
  font-size: var(--app-size-xs); font-weight: 800; color: var(--app-text-inverse); flex-shrink: 0;
}
.api-detail__url {
  font-family: var(--app-font-mono); font-size: var(--app-size-sm); color: var(--app-accent-purple-dark);
  word-break: break-all;
}
.api-detail__label {
  font-size: var(--app-size-xs); font-weight: 700; color: var(--app-ink-muted);
  text-transform: uppercase; letter-spacing: 0.03em; min-width: 60px; flex-shrink: 0;
}
.api-detail__val { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); }
.api-detail__empty { color: var(--app-ink-muted); font-size: var(--app-size-sm); }
.api-detail__code {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); background: rgba(30,30,40,0.05);
  padding: 8px 10px; border-radius: 6px; margin: 0; white-space: pre-wrap; word-break: break-all;
  flex: 1; min-width: 200px; max-height: 160px; overflow-y: auto;
}
.api-detail__step-idx {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--ink); color: var(--app-text-inverse);
  font-size: var(--app-size-xs); font-weight: 800; flex-shrink: 0;
}
.api-detail__text { font-size: var(--app-size-sm); color: var(--ink); margin: 0; line-height: 1.5; }
.api-detail__cat-tag {
  display: inline-flex; align-items: center; background: var(--app-accent-purple-light, #ede9fe);
  color: var(--app-accent-purple-dark, #6d28d9); padding: 2px 8px; border-radius: 4px;
  font-size: var(--app-size-xs); font-weight: 600; min-width: auto;
}

/* ── List column styles ── */
.api-list__url-code {
  font-size: var(--app-size-xs);
  font-family: var(--app-font-mono);
  color: var(--app-accent-purple-dark);
}
</style>
