<script setup>
import { ref, computed } from "vue";
import client from "@/shared/api-client.js";
import { IconPlus, IconTrash } from "@/shared/icons/index.js";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:modelValue"]);

const watchers = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const expanded = ref(false);

// Element picker
const pages = ref([]);
const allElements = ref([]);
const elementSearchQuery = ref("");

const filteredElements = computed(() => {
  if (!elementSearchQuery.value) return allElements.value;
  const q = elementSearchQuery.value.toLowerCase();
  return allElements.value.filter(
    (el) =>
      (el.alias || "").toLowerCase().includes(q) ||
      (el.resource_id || "").toLowerCase().includes(q) ||
      (el.text_val || "").toLowerCase().includes(q),
  );
});

async function loadElements() {
  try {
    const { data: pageData } = await client.get("/elements/pages");
    if (!pageData.ok) return;
    pages.value = pageData.pages || [];
    const results = [];
    for (const p of pages.value) {
      try {
        const { data: elData } = await client.get(`/elements/pages/${p.id}/items`);
        if (elData.ok) {
          for (const e of elData.elements || []) {
            results.push({ ...e, _pageLabel: p.label || `Page#${p.id}`, _pageId: p.id });
          }
        }
      } catch (_) {}
    }
    allElements.value = results;
  } catch (_) {}
}

function getXPath(el) {
  try { return JSON.parse(el.xpath_candidates)[0]?.xpath || ""; } catch { return ""; }
}

function onElementPicked(watcher, elementId) {
  const el = allElements.value.find((e) => e.id === elementId);
  if (!el) return;
  watcher.xpath = getXPath(el);
  watcher._label = el.alias || el.text_val || el.resource_id || "";
}

function addWatcher() {
  watchers.value = [...watchers.value, { xpath: "", action: "click", _label: "" }];
  if (!allElements.value.length) loadElements();
}

function removeWatcher(idx) {
  watchers.value = watchers.value.filter((_, i) => i !== idx);
}
</script>

<template>
  <div class="watcher-panel">
    <div class="watcher-header" @click="expanded = !expanded; if (!allElements.length) loadElements()">
      <span class="watcher-toggle">{{ expanded ? '▾' : '▸' }}</span>
      <span class="watcher-title">🛡️ 前置条件 — 全局弹窗监视器</span>
      <span class="watcher-count">{{ watchers.length }}</span>
      <span class="watcher-hint">检测步骤执行中意外弹出的弹窗并自动关闭</span>
    </div>

    <div v-show="expanded" class="watcher-body">
      <div v-if="!watchers.length" class="watcher-empty">
        暂未配置弹窗监视器。点击下方按钮添加。
      </div>

      <div v-for="(w, idx) in watchers" :key="idx" class="watcher-item">
        <span class="watcher-idx">{{ idx + 1 }}</span>
        <el-select
          :model-value="w._label || ''"
          placeholder="搜索弹窗元素..."
          filterable
          :filter-method="(q) => (elementSearchQuery = q)"
          clearable
          style="flex: 1"
          @change="(val) => onElementPicked(w, val)"
        >
          <el-option-group
            v-for="pg in pages" :key="pg.id"
            :label="(pg.label || 'Page#' + pg.id) + ' (' + filteredElements.filter(e => e._pageId === pg.id).length + ')'"
          >
            <el-option
              v-for="el in filteredElements.filter(e => e._pageId === pg.id)"
              :key="el.id"
              :label="el.alias || el.text_val || el.resource_id || '未命名'"
              :value="el.id"
            />
          </el-option-group>
        </el-select>
        <code class="watcher-xpath" v-if="w.xpath">{{ w.xpath.slice(0, 50) }}{{ w.xpath.length > 50 ? '…' : '' }}</code>
        <el-button size="small" @click="removeWatcher(idx)" type="danger" plain>
          <IconTrash :size="14" />
        </el-button>
      </div>

      <el-button size="small" type="primary" plain @click="addWatcher" style="margin-top: 8px">
        <IconPlus :size="14" style="margin-right: 4px" />添加监视器
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.watcher-panel {
  border: 1px dashed rgba(247, 205, 103, 0.45);
  border-radius: 12px;
  background: rgba(247, 205, 103, 0.06);
  margin-bottom: 12px;
  overflow: hidden;
}
.watcher-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}
.watcher-toggle { font-size: 12px; color: var(--app-text-secondary); width: 16px; }
.watcher-title { font-size: 13px; font-weight: 700; color: #b8860b; }
.watcher-count {
  font-size: 11px; font-weight: 700; color: #fff;
  background: #f7cd67; padding: 1px 8px; border-radius: 10px;
}
.watcher-hint { font-size: 11px; color: var(--app-text-secondary); margin-left: auto; }
.watcher-body { padding: 0 14px 14px; }
.watcher-empty {
  text-align: center; color: var(--app-text-secondary); font-size: 13px;
  padding: 16px; border: 1px dashed rgba(162,210,255,0.3); border-radius: 8px;
}
.watcher-item {
  display: flex; align-items: center; gap: 8px; margin-top: 8px;
  padding: 6px 10px; background: #fff; border-radius: 8px;
}
.watcher-idx {
  width: 22px; height: 22px; border-radius: 50%;
  background: #f7cd67; color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.watcher-xpath {
  font-size: 10px; color: var(--app-text-muted); background: rgba(162,210,255,0.1);
  padding: 2px 6px; border-radius: 4px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; max-width: 160px;
}
</style>
