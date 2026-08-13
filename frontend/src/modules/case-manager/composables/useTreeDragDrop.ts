/**
 * useTreeDragDrop — 目录树长按拖拽 + el-tree drop 处理器
 * Extracted from DirectoryTree.vue
 */
import { ref, onUnmounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatApiError } from "@/shared/api-client";
import { batchMoveItems } from "../api";

export function useTreeDragDrop(emit) {
  const dragEnabled = ref(false);
  const longPressTimer = ref(null);
  const dragSourceNode = ref(null);

  function clearLongPress() {
    if (longPressTimer.value) {
      clearTimeout(longPressTimer.value);
      longPressTimer.value = null;
    }
  }

  function onNodeMouseDown(e) {
    if (e.button !== 0) return;
    clearLongPress();
    longPressTimer.value = setTimeout(() => {
      dragEnabled.value = true;
    }, 500);
  }

  function onNodeMouseUp() {
    clearLongPress();
  }

  function onNodeMouseLeave() {
    clearLongPress();
  }

  onUnmounted(() => {
    clearLongPress();
  });

  function allowDrag() {
    return dragEnabled.value;
  }

  function allowDrop(_draggingNode, dropNode, type) {
    const target = dropNode.data;
    if (type === "inner" && target.node_type !== "directory") return false;
    return true;
  }

  async function handleNodeDrop(draggingNode, dropNode, dropType) {
    const source = draggingNode.data;
    const target = dropNode.data;

    // Reset drag state
    dragEnabled.value = false;
    dragSourceNode.value = null;

    let targetDirId;
    if (dropType === "inner") {
      targetDirId = target.id;
    } else {
      targetDirId = target.parent_id;
    }

    if (targetDirId === undefined || targetDirId === null) {
      ElMessage.warning("不能移动到根级，请选择一个目录");
      return;
    }

    const sourceName = source.name || source.case_id || source.id;
    const sourceType = source.node_type === "case" ? "用例" : "目录";

    try {
      await ElMessageBox.confirm(
        `将${sourceType}「${sourceName}」移动到目标位置？`,
        "确认移动",
        { confirmButtonText: "确认移动", cancelButtonText: "取消", type: "warning" },
      );
    } catch {
      return; // user cancelled
    }

    const items = [{
      type: source.node_type === "case" ? "case" : "directory",
      id: source.node_type === "case" ? source.case_id : source.id,
    }];

    try {
      const { data } = await batchMoveItems(items, targetDirId);
      if (data.status) {
        if (data.errors?.length) data.errors.forEach((e) => ElMessage.error(`${e.id}: ${e.reason}`));
        if (data.moved > 0) {
          ElMessage.success(`已移动 ${data.moved} 项`);
          emit("refresh");
        }
      } else {
        ElMessage.error(data.message || "移动失败");
      }
    } catch (e) {
      ElMessage.error(formatApiError(e, "移动失败"));
    }
  }

  return {
    dragEnabled,
    dragSourceNode,
    onNodeMouseDown, onNodeMouseUp, onNodeMouseLeave,
    allowDrag, allowDrop, handleNodeDrop,
  };
}
