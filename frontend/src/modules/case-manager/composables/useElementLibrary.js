/**
 * useElementLibrary — 元素库管理（pages、elements、搜索、自动填充）
 * Extracted from StepEditor.vue
 */
import { ref, computed } from "vue";
import { listPages, getPageElements } from "../api/uiAutomation.js";

export function useElementLibrary() {
  const pages = ref([]);
  const allElements = ref([]);
  const elementSearchQuery = ref("");

  const filteredElements = computed(() => {
    if (!elementSearchQuery.value) return allElements.value;
    const q = elementSearchQuery.value.toLowerCase();
    return allElements.value.filter((el) =>
      (el.alias || "").toLowerCase().includes(q) ||
      (el.text_val || "").toLowerCase().includes(q) ||
      (el.resource_id || "").toLowerCase().includes(q) ||
      (el.content_desc || "").toLowerCase().includes(q) ||
      (getXPath(el) || "").toLowerCase().includes(q)
    );
  });

  const filteredPages = computed(() => {
    const pageIds = new Set(filteredElements.value.map((e) => e._pageId));
    return pages.value.filter((p) => pageIds.has(p.id));
  });

  async function loadElementLibrary() {
    try {
      const { data: pageData } = await listPages();
      if (!pageData.ok) return;
      pages.value = pageData.pages || [];
      const results = [];
      for (const p of pages.value) {
        try {
          const { data: elData } = await getPageElements(p.id);
          if (elData.ok) {
            for (const e of elData.elements || []) {
              results.push({ ...e, _pageLabel: p.label || `Page#${p.id}`, _pageId: p.id });
            }
          }
        } catch { /* skip failed page */ }
      }
      allElements.value = results;
    } catch { /* skip failed load */ }
  }

  function getXPath(el) {
    try { return JSON.parse(el.xpath_candidates)[0]?.xpath || ""; }
    catch { return ""; }
  }

  function elementOptionLabel(el) {
    return el.alias || el.text_val || el.resource_id || "未命名";
  }

  function onElementPicked(step, field, elementId) {
    const el = allElements.value.find((e) => e.id === elementId);
    if (!el) return;
    step[field] = getXPath(el);
    if (!step.description) step.description = el.alias || el.text_val || el.resource_id || "";
    step[`_el_${field}`] = el;
    step[`_el_id_${field}`] = el.id;
  }

  function resolveElementName(step, field = "xpath") {
    const id = step[`_el_id_${field}`];
    if (id) {
      const el = allElements.value.find((e) => e.id === id);
      if (el) return el.alias || el.text_val || el.resource_id || "未命名元素";
    }
    const cached = step[`_el_${field}`];
    if (cached) return cached.alias || cached.text_val || cached.resource_id || "未命名元素";
    return step.description || "元素";
  }

  return {
    pages, allElements, elementSearchQuery,
    filteredElements, filteredPages,
    loadElementLibrary, getXPath, elementOptionLabel,
    onElementPicked, resolveElementName,
  };
}
