import { ref } from "vue";

export function useToolCalls() {
  const toolCalls = ref([]);

  function resetToolCalls() {
    toolCalls.value = [];
  }

  return { toolCalls, resetToolCalls };
}
