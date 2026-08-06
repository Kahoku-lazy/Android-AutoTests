<script setup>
import CaseList from "../CaseList.vue";
import { listApiDefinitions, deleteApiDefinition, getApiDefinition } from "../../api/apiTesting";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
defineEmits(["refresh-tree"]);

const api = { listDefs: listApiDefinitions, deleteDef: deleteApiDefinition, getDef: getApiDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "方法", dataIndex: "method", minWidth: 86, align: "center" },
  { title: "URL", dataIndex: "url", minWidth: 220 },
  { title: "状态码", dataIndex: "expected_status", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

const METHOD_COLORS = { GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#a78bfa' }

function editPath(id) { return `/cases/api/${id}/edit`; }
</script>

<template>
  <CaseList case-type="api" :list-api="api" :columns="columns" create-path="/cases/api/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    :active-case-id="activeCaseId"
    @refresh-tree="$emit('refresh-tree')">
    <template #cell-method="{ value }">
      <span :style="{ color: METHOD_COLORS[value] || 'inherit', fontWeight: 700 }">{{ value }}</span>
    </template>
    <template #detail="{ case: c }">
      <div class="api-detail">
        <div class="api-detail__row" v-if="c.url">
          <span class="api-detail__badge" :style="{ background: METHOD_COLORS[c.method] || '#999' }">{{ c.method }}</span>
          <code class="api-detail__url">{{ c.url }}</code>
        </div>
        <div class="api-detail__row" v-if="c.expected_status">
          <span class="api-detail__label">状态码</span>
          <span class="api-detail__val">{{ c.expected_status }}</span>
        </div>
        <div class="api-detail__row" v-if="c.headers">
          <span class="api-detail__label">Headers</span>
          <pre class="api-detail__code">{{ c.headers }}</pre>
        </div>
        <div class="api-detail__row" v-if="c.body">
          <span class="api-detail__label">请求体</span>
          <pre class="api-detail__code">{{ c.body }}</pre>
        </div>
        <div class="api-detail__row" v-if="c.expected_response">
          <span class="api-detail__label">预期响应</span>
          <pre class="api-detail__code">{{ c.expected_response }}</pre>
        </div>
        <div class="api-detail__row" v-if="c.precondition">
          <span class="api-detail__label">前置条件</span>
          <p class="api-detail__text">{{ c.precondition }}</p>
        </div>
      </div>
    </template>
  </CaseList>
</template>

<style scoped>
.api-detail { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.api-detail__row { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }
.api-detail__badge {
  display: inline-block; padding: 2px 10px; border-radius: 8px;
  font-size: 11px; font-weight: 800; color: #fff; flex-shrink: 0;
}
.api-detail__url {
  font-family: var(--app-font-mono); font-size: 13px; color: #8275c2;
  word-break: break-all;
}
.api-detail__label {
  font-size: 11px; font-weight: 700; color: var(--app-ink-muted);
  text-transform: uppercase; letter-spacing: 0.03em; min-width: 60px; flex-shrink: 0;
}
.api-detail__val { font-size: 14px; font-weight: 700; color: var(--ink); }
.api-detail__code {
  font-family: var(--app-font-mono); font-size: 12px; background: rgba(30,30,40,0.05);
  padding: 8px 10px; border-radius: 6px; margin: 0; white-space: pre-wrap; word-break: break-all;
  flex: 1; min-width: 200px; max-height: 160px; overflow-y: auto;
}
.api-detail__text { font-size: 13px; color: var(--ink); margin: 0; line-height: 1.5; }
</style>
