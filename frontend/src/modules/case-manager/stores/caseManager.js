/**
 * case-manager Pinia store — shared state for three case types with TAB switching.
 */
import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { fetchDirectories } from "../api/directories.js";
import { listDefinitions } from "../api/uiAutomation.js";
import { listStorageDefinitions } from "../api/storage.js";
import { listApiDefinitions } from "../api/apiTesting.js";

const TAB_STORAGE_KEY = "case-manager-active-tab";

export const useCaseManagerStore = defineStore("caseManager", () => {
  // ── TAB state ──
  const activeTab = ref(localStorage.getItem(TAB_STORAGE_KEY) || "ui");

  function setActiveTab(tab) {
    activeTab.value = tab;
    localStorage.setItem(TAB_STORAGE_KEY, tab);
  }

  const caseType = computed(() => {
    const map = { ui: "ui_automation", storage: "storage", api: "api_testing" };
    return map[activeTab.value] || "ui_automation";
  });

  // ── Tree ──
  const treeData = ref([]);

  async function loadTree() {
    try {
      const res = await fetchDirectories(caseType.value);
      treeData.value = res.data.tree || [];
    } catch {
      treeData.value = [];
    }
  }

  // ── Definitions per type ──
  const uiDefinitions = ref([]);
  const storageDefinitions = ref([]);
  const apiDefinitions = ref([]);
  const loading = ref(false);

  const currentDefinitions = computed(() => {
    const map = {
      ui: uiDefinitions,
      storage: storageDefinitions,
      api: apiDefinitions,
    };
    return map[activeTab.value]?.value || [];
  });

  async function loadDefinitions(directoryId = null) {
    loading.value = true;
    try {
      if (activeTab.value === "ui") {
        const res = await listDefinitions(directoryId);
        uiDefinitions.value = res.data.definitions || [];
      } else if (activeTab.value === "storage") {
        const res = await listStorageDefinitions(directoryId);
        storageDefinitions.value = res.data.definitions || [];
      } else if (activeTab.value === "api") {
        const res = await listApiDefinitions(directoryId);
        apiDefinitions.value = res.data.definitions || [];
      }
    } catch {
      // keep existing data on error
    } finally {
      loading.value = false;
    }
  }

  async function loadAll(directoryId = null) {
    await Promise.all([loadTree(), loadDefinitions(directoryId)]);
  }

  return {
    activeTab,
    caseType,
    setActiveTab,
    treeData,
    loadTree,
    uiDefinitions,
    storageDefinitions,
    apiDefinitions,
    currentDefinitions,
    loading,
    loadDefinitions,
    loadAll,
  };
});
