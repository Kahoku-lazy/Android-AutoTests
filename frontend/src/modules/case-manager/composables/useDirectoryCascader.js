/**
 * useDirectoryCascader — 目录级联选择器数据
 * Extracted from CaseEditor.vue
 */
import { ref } from "vue";
import { fetchDirectories } from "../api.js";

export function useDirectoryCascader() {
  const dirOptions = ref([]);

  function buildCascaderOptions(tree) {
    return tree.map((node) => ({
      value: node.id,
      label: node.name,
      children: node.children?.length > 0 ? buildCascaderOptions(node.children) : undefined,
    }));
  }

  async function loadDirOptions() {
    try {
      const { data } = await fetchDirectories();
      if (data.ok) dirOptions.value = buildCascaderOptions(data.tree);
    } catch { /* ignore */ }
  }

  return { dirOptions, loadDirOptions };
}
