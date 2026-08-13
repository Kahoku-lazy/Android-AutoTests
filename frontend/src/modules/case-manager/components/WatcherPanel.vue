<script setup>
import { ref, computed } from "vue";
import { listPages, getPageElements } from "../api/uiAutomation";
import { IconPlus, IconTrash } from "@/shared/icons/index";

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
    const { data: pageData } = await listPages();
    if (!pageData.status) return;
    pages.value = pageData.pages || [];
    const results = [];
    for (const p of pages.value) {
      try {
        const { data: elData } = await getPageElements(p.id);
        if (elData.status) {
          for (const e of elData.elements || []) {
            results.push({ ...e, _pageLabel: p.label || `Page#${p.id}`, _pageId: p.id });
          }
        }
      } catch (e) { console.error(e); }
    }
    allElements.value = results;
  } catch (e) { console.error(e); }
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
    <div class="watcher-header" role="button" tabindex="0" @click="expanded = !expanded; if (!allElements.length) loadElements()" @keydown.enter.prevent="expanded = !expanded; if (!allElements.length) loadElements()" @keydown.space.prevent="expanded = !expanded; if (!allElements.length) loadElements()">
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
  border: 1px dashed var(--case-warn-border-dashed);
  border-radius: var(--app-radius-md);
  background: var(--case-warn-bg);
  margin-bottom: 12px;
  overflow: hidden;
}
.watcher-header {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}
.watcher-toggle { font-size: var(--app-size-sm); color: var(--app-text-secondary); width: 16px; }
.watcher-title { font-size: var(--app-size-sm); font-weight: 700; color: var(--case-warn-accent-text); }
.watcher-count {
  font-size: var(--app-size-xs); font-weight: 700; color: var(--case-watcher-badge-text);
  background: var(--case-watcher-badge-bg); padding: 1px 8px; border-radius: 10px;
}
.watcher-hint { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-left: auto; }
.watcher-body { padding: 0 14px 14px; }
.watcher-empty {
  text-align: center; color: var(--app-text-secondary); font-size: var(--app-size-sm);
  padding: var(--app-space-md); border: 1px dashed var(--case-border-dashed); border-radius: var(--app-radius-md);
}
.watcher-item {
  display: flex; align-items: center; gap: var(--app-space-sm); margin-top: var(--app-space-sm);
  padding: 6px 10px; background: var(--app-bg-card); border-radius: var(--app-radius-md);
}
.watcher-idx {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--case-watcher-badge-bg); color: var(--case-watcher-badge-text); font-size: var(--app-size-xs); font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.watcher-xpath {
  font-size: var(--app-size-xs); color: var(--app-text-secondary); background: var(--case-bg-dragover);
  padding: 2px 6px; border-radius: var(--app-radius-sm); overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; max-width: 160px;
}
</style>
