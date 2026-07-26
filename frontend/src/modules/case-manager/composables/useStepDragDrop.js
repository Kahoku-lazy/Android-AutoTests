/**
 * useStepDragDrop — 步骤拖拽排序
 * Extracted from StepEditor.vue
 */
import { ref } from 'vue';

export function useStepDragDrop(steps, expanded) {
  const dragIndex = ref(null);
  const dropTargetIdx = ref(null);

  function onDragStart(idx, e) {
    dragIndex.value = idx;
    dropTargetIdx.value = null;
    e.dataTransfer.effectAllowed = 'move';
  }

  function onDragOver(idx, e) {
    e.preventDefault();
    if (idx !== dragIndex.value) dropTargetIdx.value = idx;
  }

  function onDragLeave() {
    dropTargetIdx.value = null;
  }

  function onDragEnd() {
    dragIndex.value = null;
    dropTargetIdx.value = null;
  }

  function onDrop(e, idx) {
    e.preventDefault();
    e.stopPropagation();
    if (dragIndex.value === null || dragIndex.value === idx) {
      dragIndex.value = null;
      dropTargetIdx.value = null;
      return;
    }
    const arr = [...steps.value];
    const [moved] = arr.splice(dragIndex.value, 1);
    arr.splice(idx, 0, moved);
    steps.value = arr;
    expanded.value = {};
    dragIndex.value = null;
    dropTargetIdx.value = null;
  }

  return { dragIndex, dropTargetIdx, onDragStart, onDragOver, onDragLeave, onDragEnd, onDrop };
}
